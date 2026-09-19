from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional

from pydantic import BaseModel
from app.models.gift import Gift
from app.repositories.contribution_repository import ContributionRepository
from app.repositories.gift_repository import GiftRepository
from app.repositories.image_repository import ImageRepository
from app.repositories.marketplace_links_repository import MarketplacesLinksRepository
from app.repositories.event_repository import EventRepository
from app.repositories.reservation_repository import ReservationRepository
from app.services.gift_service import GiftService
from app.services.reservation_service import ReservationService
from app.models.user import User
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
reservation_service = ReservationService(reservation_repo, gift_repo)
gift_service = GiftService(
    gift_repo,
    image_repo,
    marketplace_links_repo,
    contribution_repo,
    event_repo,
    reservation_service,
)


@router.post("/gifts/", response_model=Gift)
def create_gift(gift: Gift, current_user: User = Depends(get_current_user)):
    event = event_repo.get_event_by_id(gift.event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can create gifts")
    return gift_service.create_gift(gift)


@router.get("/gifts/{gift_id}", response_model=Gift)
def get_gift(gift_id: int):
    return gift_service.get_gift_by_id(gift_id)


@router.get("/events/{event_id}/gifts", response_model=List[Gift])
def get_gifts_by_event(event_id: int):
    return gift_service.get_gifts_by_event(event_id)


class GiftUpdateRequest(BaseModel):
    title: Optional[str] = None
    price: Optional[int] = None
    description: Optional[str] = None
    picture_url: Optional[str] = None
    marketplace_url: Optional[str] = None
    category_id: Optional[int] = None
    image_id: Optional[int] = None
    status: Optional[str] = None
    is_reserved: Optional[bool] = None


@router.patch("/gifts/{gift_id}/status", response_model=Gift)
def update_gift_status(gift_id: int, status: str, current_user: User = Depends(get_current_user)):
    gift = gift_service.get_gift_by_id(gift_id)
    event = event_repo.get_event_by_id(gift.event_id)
    if event is None or event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can change gift status")
    return gift_service.update_gift_status(gift_id, status)


@router.patch("/gifts/{gift_id}", response_model=Gift)
def update_gift(
    gift_id: int,
    data: GiftUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    return gift_service.update_gift(gift_id, data.model_dump(exclude_unset=True), current_user)


@router.delete("/gifts/{gift_id}")
def delete_gift(gift_id: int, current_user: User = Depends(get_current_user)):
    gift = gift_service.get_gift_by_id(gift_id)
    event = event_repo.get_event_by_id(gift.event_id)
    if event is None or event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can delete gifts")
    gift_service.delete_gift(gift_id)
    return {"message": "Gift deleted"}
