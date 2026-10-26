from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, StringConstraints, field_validator
from typing import Annotated, List, Optional, Literal

from app.models.gift import Gift, GiftCreateRequest, GiftFilters
from app.models.reservation import PublicGiftReservationRequest
from app.models.user import User
from app.repositories.contribution_repository import ContributionRepository
from app.repositories.gift_repository import GiftRepository
from app.repositories.event_repository import EventRepository
from app.repositories.image_repository import ImageRepository
from app.repositories.marketplace_links_repository import MarketplacesLinksRepository
from app.repositories.reservation_repository import ReservationRepository
from app.services.gift_service import GiftService
from app.services.reservation_service import ReservationService
from app.services.recommendation_service import RecommendationService
from app.services.gift_privacy import owner_gift_response, owner_gift_filters
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
def create_gift(gift: GiftCreateRequest, current_user: User = Depends(get_current_user)):
    event = event_repo.get_event_by_id(gift.event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can create gifts")
    return gift_service.create_gift(gift, gift.tag_ids)


@router.get("/events/{event_id}/recommendations")
def get_recommendations(
    event_id: int,
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=6, ge=1, le=20),
):
    event = event_repo.get_event_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can view recommendations")
    return RecommendationService().get_recommendations(event, limit)


@router.get("/gifts/{gift_id}", response_model=Gift)
def get_gift(gift_id: int, current_user: User = Depends(get_current_user), show_reservations: bool = False):
    gift = gift_service.get_gift_by_id(gift_id)
    event = event_repo.get_event_by_id(gift.event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can view a gift")
    return owner_gift_response(gift, show_reservations)


@router.get("/events/{event_id}/gifts", response_model=List[Gift])
def get_gifts_by_event(
    event_id: int,
    filters: Annotated[GiftFilters, Query()],
    current_user: User = Depends(get_current_user),
):
    event = event_repo.get_event_by_id(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can view gifts")
    gifts = gift_service.get_gifts_by_event(event_id, owner_gift_filters(filters))
    return [owner_gift_response(gift, filters.show_reservations) for gift in gifts]


class GiftUpdateRequest(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None = None
    price: Optional[int] = Field(default=None, gt=0, le=9223372036854775807)
    description: Optional[str] = None
    picture_url: Optional[str] = None
    marketplace_url: Optional[str] = None
    category_id: Optional[int] = None
    image_id: Optional[int] = None
    status: Optional[Literal["available", "bought"]] = None
    is_reserved: Optional[bool] = None
    tag_ids: list[int] = Field(default_factory=list)
    contribution_goal: int | None = Field(default=None, gt=0, le=9223372036854775807)

    @field_validator("title", "price", "status")
    @classmethod
    def validate_required_fields(cls, value):
        if value is None:
            raise ValueError("Title, price and status cannot be null")
        return value


@router.patch("/gifts/{gift_id}/status", response_model=Gift)
def update_gift_status(gift_id: int, status: str, current_user: User = Depends(get_current_user)):
    gift = gift_service.get_gift_by_id(gift_id)
    event = event_repo.get_event_by_id(gift.event_id)
    if event is None or event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can change gift status")
    return owner_gift_response(gift_service.update_gift_status(gift_id, status))


@router.patch("/gifts/{gift_id}", response_model=Gift)
def update_gift(
    gift_id: int,
    data: GiftUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    return owner_gift_response(gift_service.update_gift(gift_id, data.model_dump(exclude_unset=True), current_user))


@router.patch("/events/public/{public_token}/gifts/{gift_id}/reservation", response_model=Gift)
def update_public_gift_reservation(
    public_token: str,
    gift_id: int,
    data: PublicGiftReservationRequest,
    current_user: User = Depends(get_current_user),
):
    return gift_service.update_public_gift_reservation(public_token, gift_id, data.is_reserved, current_user)


@router.delete("/gifts/{gift_id}")
def delete_gift(gift_id: int, current_user: User = Depends(get_current_user)):
    gift = gift_service.get_gift_by_id(gift_id)
    event = event_repo.get_event_by_id(gift.event_id)
    if event is None or event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can delete gifts")
    gift_service.delete_gift(gift_id)
    return {"message": "Gift deleted"}
