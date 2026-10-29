"""Share explicitly selected wishes; reservation state stays on the original item."""
import json
import secrets
from sqlite3 import IntegrityError
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, ValidationError

from app.database import get_connection
from app.models.identifiers import DatabaseId
from app.models.reservation import GuestReservationCancelRequest, GuestReservationCreateRequest
from app.models.user import User
from app.repositories.gift_repository import GiftRepository
from app.repositories.event_repository import EventRepository
from app.repositories.reservation_repository import ReservationRepository
from app.services.reservation_service import ReservationService
from app.utils.jwt import get_current_user, get_optional_user
from app.utils.security import hash_password, verify_password

router = APIRouter(prefix="/wish-shares", tags=["Wish sharing"])
reservations = ReservationRepository()
reservation_service = ReservationService(reservations, GiftRepository())


class ShareItem(BaseModel):
    kind: Literal["wish", "gift"]
    id: DatabaseId


class ShareRequest(BaseModel):
    items: list[ShareItem] = Field(min_length=1, max_length=50)


def get_reference(token: str, position: int):
    with get_connection() as conn:
        return conn.execute("""
            SELECT wish_shares.owner_id, wish_share_items.kind, wish_share_items.item_id
            FROM wish_share_items JOIN wish_shares ON wish_shares.token = wish_share_items.share_token
            WHERE wish_share_items.share_token = ? AND wish_share_items.position = ?
        """, (token, position)).fetchone()


def rate_limit(request: Request, item_id: int | None = None):
    address = request.client.host if request.client else "unknown"
    retry = reservations.check_guest_rate_limit(address, item_id, namespace="wish-share")
    if retry is not None:
        raise HTTPException(status_code=429, detail="Too many reservation attempts", headers={"Retry-After": str(retry)})
    return address


@router.post("/", status_code=201)
def create_share(data: ShareRequest, user: User = Depends(get_current_user)):
    items, references, seen = [], [], set()
    with get_connection() as conn:
        for item in data.items:
            key = (item.kind, item.id)
            if key in seen:
                continue
            seen.add(key)
            if item.kind == "wish":
                row = conn.execute("""
                    SELECT title,price,description,marketplace_url,picture_url,image_id
                    FROM personal_wishes WHERE id=? AND owner_id=? AND received=0
                """, (item.id, user.id)).fetchone()
            else:
                row = conn.execute("""
                    SELECT gifts.title,gifts.price,gifts.description,gifts.marketplace_url,gifts.picture_url,gifts.image_id
                    FROM gifts JOIN events ON events.id=gifts.event_id
                    WHERE gifts.id=? AND events.owner_id=? AND gifts.received=0
                """, (item.id, user.id)).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Wish not found")
            items.append(dict(row))
            references.append(key)
        token = secrets.token_urlsafe(32)
        conn.execute("INSERT INTO wish_shares (token,owner_id,items_json) VALUES (?,?,?)", (token, user.id, json.dumps(items, ensure_ascii=False)))
        conn.executemany("INSERT INTO wish_share_items (share_token,position,kind,item_id) VALUES (?,?,?,?)",
                         [(token, position, kind, item_id) for position, (kind, item_id) in enumerate(references)])
    return {"token": token}


@router.get("/{token}")
def get_shared_wishes(token: str, user: User | None = Depends(get_optional_user)):
    EventRepository().archive_expired()
    with get_connection() as conn:
        share = conn.execute("SELECT owner_id, items_json FROM wish_shares WHERE token=?", (token,)).fetchone()
        if share is None:
            raise HTTPException(status_code=404, detail="Link not found")
        refs = {row["position"]: row for row in conn.execute("SELECT * FROM wish_share_items WHERE share_token=?", (token,)).fetchall()}
        is_owner = bool(user and user.id == share["owner_id"])
        items = []
        for position, snapshot in enumerate(json.loads(share["items_json"])):
            ref = refs.get(position)
            if ref is None:
                continue
            if ref["kind"] == "wish":
                row = conn.execute("""
                    SELECT personal_wishes.title, personal_wishes.price, personal_wishes.description,
                           personal_wishes.marketplace_url, personal_wishes.picture_url, personal_wishes.image_id,
                           personal_wishes.received, personal_wish_reservations.reserver_id,
                           personal_wish_reservations.wish_id AS reservation_id
                    FROM personal_wishes LEFT JOIN personal_wish_reservations ON personal_wish_reservations.wish_id=personal_wishes.id
                    WHERE personal_wishes.id=? AND personal_wishes.owner_id=?
                """, (ref["item_id"], share["owner_id"])).fetchone()
                available = row is not None and not row["received"]
                reserved = available and row["reservation_id"] is not None
            else:
                row = conn.execute("""
                    SELECT gifts.title, gifts.price, gifts.description, gifts.marketplace_url, gifts.picture_url, gifts.image_id,
                           gifts.received, gifts.status, gifts.contribution_goal, events.status AS event_status,
                           reservations.id AS reservation_id, reservations.reserver_id
                    FROM gifts JOIN events ON events.id=gifts.event_id
                    LEFT JOIN reservations ON reservations.gift_id=gifts.id
                    WHERE gifts.id=? AND events.owner_id=?
                """, (ref["item_id"], share["owner_id"])).fetchone()
                available = row is not None and not row["received"] and row["event_status"] == "active" and row["contribution_goal"] is None and row["status"] != "bought"
                reserved = available and row["status"] == "reserved"
            status = "unavailable" if not available else "hidden" if is_owner else "reserved" if reserved else "available"
            fields = ("title", "price", "description", "marketplace_url", "picture_url", "image_id")
            display = {field: row[field] for field in fields} if row is not None else dict.fromkeys(fields)
            if row is None:
                display["title"] = "Подарок удалён"
            items.append({**display, "position": position, "status": status,
                          "is_mine": bool(reserved and user and row["reserver_id"] == user.id)})
        return {"items": items, "is_owner": is_owner, "legacy": not bool(refs)}


def checked_reference(token: str, position: int, user: User | None):
    ref = get_reference(token, position)
    if ref is None:
        raise HTTPException(status_code=404, detail="Gift not found")
    if user and user.id == ref["owner_id"]:
        raise HTTPException(status_code=403, detail="Cannot reserve your own gift")
    return ref


def event_public_token(gift_id: int, owner_id: int):
    with get_connection() as conn:
        row = conn.execute("""
            SELECT events.public_token FROM gifts JOIN events ON events.id=gifts.event_id
            WHERE gifts.id=? AND events.owner_id=? AND gifts.received=0
        """, (gift_id, owner_id)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Gift not found")
    return row["public_token"]


@router.post("/{token}/items/{position}/reservation")
def reserve_shared_item(token: str, position: int, request: Request, data: dict,
                        user: User | None = Depends(get_optional_user)):
    ref = checked_reference(token, position, user)
    address = rate_limit(request) if user is None else ""
    try:
        guest = GuestReservationCreateRequest.model_validate(data) if user is None else None
    except ValidationError:
        raise HTTPException(status_code=422, detail="Name and secret word are required") from None
    if ref["kind"] == "gift":
        public_token = event_public_token(ref["item_id"], ref["owner_id"])
        if user:
            reservation_service.reserve_gift(ref["item_id"], user.name, False, user.id, public_token)
        else:
            reservation_service.reserve_guest_gift(public_token, ref["item_id"], guest.name, guest.secret_word.get_secret_value(), address)
    else:
        secret_hash = hash_password(guest.secret_word.get_secret_value()) if guest else None
        try:
            with get_connection() as conn:
                conn.execute("BEGIN IMMEDIATE")
                row = conn.execute("SELECT id FROM personal_wishes WHERE id=? AND owner_id=? AND received=0", (ref["item_id"], ref["owner_id"])).fetchone()
                if row is None:
                    raise HTTPException(status_code=404, detail="Gift not found")
                conn.execute("INSERT INTO personal_wish_reservations (wish_id,reserver_id,guest_name,secret_word_hash) VALUES (?,?,?,?)",
                             (ref["item_id"], user.id if user else None, guest.name if guest else None, secret_hash))
        except IntegrityError:
            raise HTTPException(status_code=409, detail="Gift is already reserved") from None
    return {"status": "reserved"}


@router.delete("/{token}/items/{position}/reservation")
def cancel_shared_reservation(token: str, position: int, request: Request, data: dict,
                              user: User | None = Depends(get_optional_user)):
    ref = checked_reference(token, position, user)
    address = rate_limit(request, ref["item_id"]) if user is None else ""
    try:
        guest = GuestReservationCancelRequest.model_validate(data) if user is None else None
    except ValidationError:
        raise HTTPException(status_code=422, detail="Secret word is required") from None
    if ref["kind"] == "gift":
        public_token = event_public_token(ref["item_id"], ref["owner_id"])
        if user:
            reservation_service.unreserve_gift_by_user(ref["item_id"], user.id)
        else:
            reservation_service.unreserve_guest_gift(public_token, ref["item_id"], guest.secret_word.get_secret_value(), address)
    else:
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM personal_wish_reservations WHERE wish_id=?", (ref["item_id"],)).fetchone()
            if row is None:
                raise HTTPException(status_code=404, detail="Reservation not found")
            allowed = row["reserver_id"] == user.id if user else row["reserver_id"] is None and row["secret_word_hash"] and verify_password(guest.secret_word.get_secret_value(), row["secret_word_hash"])
            if not allowed:
                raise HTTPException(status_code=403, detail="Invalid reservation credentials")
            conn.execute("DELETE FROM personal_wish_reservations WHERE wish_id=?", (ref["item_id"],))
    return {"status": "available"}


@router.delete("/{token}")
def revoke_share(token: str, user: User = Depends(get_current_user)):
    with get_connection() as conn:
        deleted = conn.execute("DELETE FROM wish_shares WHERE token=? AND owner_id=?", (token, user.id)).rowcount
    if not deleted:
        raise HTTPException(status_code=404, detail="Link not found")
    return {"revoked": True}
