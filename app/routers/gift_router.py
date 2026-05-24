from fastapi import APIRouter
from typing import List
from app.models.gift import Gift
from app.repositories.gift_repository import GiftRepository
from app.services.gift_service import GiftService

router = APIRouter(
    tags=["Gifts"]
)

gift_repo = GiftRepository()
gift_service = GiftService(gift_repo)

@router.post("/gifts/", response_model=Gift)
def create_gift(gift: Gift):
    return gift_service.create_gift(gift)

@router.get("/gifts/{gift_id}", response_model=Gift)
def get_gift(gift_id: int):
    return gift_service.get_gift_by_id(gift_id)

@router.get("/events/{event_id}/gifts", response_model=List[Gift])
def get_gifts_by_event(event_id: int):
    return gift_service.get_gifts_by_event(event_id)

@router.patch("/gifts/{gift_id}/status")
def update_gift_status(gift_id: int, status: str):
    return gift_service.update_gift_status(gift_id, status)

@router.delete("/gifts/{gift_id}")
def delete_gift(gift_id: int):
    gift_service.delete_gift(gift_id)
    return {"message": "Gift deleted"}
