"""Personal wishes can exist independently of an event."""
import json
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, StringConstraints

from app.database import get_connection
from app.models.identifiers import DatabaseId
from app.models.user import User
from app.utils.jwt import get_current_user
from app.utils.image_access import signed_image_url, can_use_image

router = APIRouter(prefix="/wishes", tags=["Wishes"])


class WishCreate(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
    price: int | None = Field(default=None, gt=0, le=9223372036854775807)
    description: str | None = None
    marketplace_url: str | None = None
    picture_url: str | None = None
    image_id: DatabaseId | None = None
    priority: Literal["low", "normal", "high"] = "normal"
    tags: list[Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]] = Field(default_factory=list, max_length=30)


class WishReceived(BaseModel):
    received: bool


class AddToEvent(BaseModel):
    event_id: DatabaseId


def as_wish(row):
    result = dict(row)
    result["image_url"] = signed_image_url(result["image_id"])
    result["tags"] = json.loads(result.pop("tags_json"))
    result["received"] = bool(result["received"])
    return result


def validate_image(connection, image_id, user_id):
    if image_id is not None and not can_use_image(connection, image_id, user_id):
        raise HTTPException(status_code=404, detail="Image not found")


def wish_values(data: WishCreate):
    tags = list(dict.fromkeys(tag.strip() for tag in data.tags))
    return (data.title, data.price, data.description, data.marketplace_url, data.picture_url,
            data.image_id, json.dumps(tags, ensure_ascii=False), data.priority)


@router.get("/")
def get_wishes(user: User = Depends(get_current_user)):
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM personal_wishes WHERE owner_id = ? ORDER BY id DESC", (user.id,)).fetchall()
    return [as_wish(row) for row in rows]


@router.post("/", status_code=201)
def create_wish(data: WishCreate, user: User = Depends(get_current_user)):
    with get_connection() as connection:
        validate_image(connection, data.image_id, user.id)
        row = connection.execute("""
            INSERT INTO personal_wishes (owner_id, title, price, description, marketplace_url,
                                         picture_url, image_id, tags_json, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING *
        """, (user.id, *wish_values(data))).fetchone()
    return as_wish(row)


@router.put("/{wish_id}")
def update_wish(wish_id: DatabaseId, data: WishCreate, user: User = Depends(get_current_user)):
    with get_connection() as connection:
        validate_image(connection, data.image_id, user.id)
        row = connection.execute("""
            UPDATE personal_wishes SET title=?, price=?, description=?, marketplace_url=?,
                                       picture_url=?, image_id=?, tags_json=?, priority=?
            WHERE id=? AND owner_id=? RETURNING *
        """, (*wish_values(data), wish_id, user.id)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Wish not found")
    return as_wish(row)


@router.patch("/{wish_id}/received")
def set_received(wish_id: DatabaseId, data: WishReceived, user: User = Depends(get_current_user)):
    with get_connection() as connection:
        row = connection.execute(
            "UPDATE personal_wishes SET received = ? WHERE id = ? AND owner_id = ? RETURNING *",
            (int(data.received), wish_id, user.id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Wish not found")
    return as_wish(row)


@router.delete("/{wish_id}")
def delete_wish(wish_id: DatabaseId, user: User = Depends(get_current_user)):
    with get_connection() as connection:
        count = connection.execute("DELETE FROM personal_wishes WHERE id = ? AND owner_id = ?", (wish_id, user.id)).rowcount
    if not count:
        raise HTTPException(status_code=404, detail="Wish not found")
    return {"deleted": True}


@router.post("/{wish_id}/events", status_code=201)
def add_to_event(wish_id: DatabaseId, data: AddToEvent, user: User = Depends(get_current_user)):
    from app.services.gift_import_service import GiftImportService
    from app.models.gift_import import GiftImportItem
    gift = GiftImportService().add(data.event_id, user.id, [GiftImportItem(kind="wish", id=wish_id)])[0]
    return {"gift_id": gift.id}
