from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel

from app.models.gift import Gift
from app.models.reservation import Reservation
from app.models.user import User
from app.repositories.contribution_repository import ContributionRepository
from app.repositories.gift_repository import GiftRepository
from app.repositories.event_repository import EventRepository
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.image_repository import ImageRepository
from app.repositories.marketplace_links_repository import MarketplacesLinksRepository
from app.services.gift_service import GiftService
from app.utils.jwt import get_current_user

router = APIRouter(
    tags=["Gifts"]
)

gift_repo = GiftRepository()
image_repo = ImageRepository()
marketplace_links_repo = MarketplacesLinksRepository()
contribution_repo = ContributionRepository()
event_repo = EventRepository()
reservation_repo = ReservationRepository()
gift_service = GiftService(
    gift_repo,
    image_repo,
    marketplace_links_repo,
    contribution_repo,
)


@router.post("/gifts/", response_model=Gift)
def create_gift(gift: Gift):
    return gift_service.create_gift(gift)


@router.get("/gifts/{gift_id}", response_model=Gift)
def get_gift(gift_id: int):
    return gift_service.get_gift_by_id(gift_id)


@router.get("/events/{event_id}/gifts", response_model=List[Gift])
def get_gifts_by_event(event_id: int):
    return gift_service.get_gifts_by_event(event_id)


class GiftUpdateRequest(BaseModel):
    title: str | None = None
    price: int | None = None
    description: str | None = None
    picture_url: str | None = None
    marketplace_url: str | None = None
    reserved: bool | None = None


@router.patch("/gifts/{gift_id}", response_model=Gift)
def update_gift(
    gift_id: int,
    data: GiftUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    gift = gift_repo.get_gift_by_id(gift_id)
    if gift is None:
        raise HTTPException(status_code=404, detail="Gift not found")

    event = event_repo.get_event_by_id(gift.event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    fields = data.model_dump(exclude_unset=True)
    reserved = fields.pop("reserved", None)

    if event.owner_id == current_user.id:
        if reserved is not None:
            raise HTTPException(status_code=403, detail="Event owner cannot reserve own gift")
        return gift_service.update_gift(gift_id, fields)

    if fields:
        raise HTTPException(status_code=403, detail="Only event owner can edit gift fields")

    if reserved is None:
        raise HTTPException(status_code=400, detail="reserved is required")

    existing = reservation_repo.get_reservation_by_gift(gift_id)

    if reserved:
        if existing is not None:
            raise HTTPException(status_code=409, detail="Gift is already reserved")

        reservation_repo.reserve_gift(
            Reservation(
                gift_id=gift_id,
                is_anonymous=False,
                reserver_name=current_user.name,
                user_id=current_user.id,
            )
        )
        gift_repo.update_gift_status(gift_id, "reserved")
    else:
        if existing is None:
            raise HTTPException(status_code=404, detail="Reservation not found")
        if existing.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="You can only cancel your own reservation")

        reservation_repo.unreserve_gift(gift_id)
        gift_repo.update_gift_status(gift_id, "available")

    return gift_service.get_gift_by_id(gift_id)


@router.patch("/gifts/{gift_id}/status", response_model=Gift)
def update_gift_status(gift_id: int, status: str):
    return gift_service.update_gift_status(gift_id, status)


@router.delete("/gifts/{gift_id}")
def delete_gift(gift_id: int):
    gift_service.delete_gift(gift_id)
    return {"message": "Gift deleted"}