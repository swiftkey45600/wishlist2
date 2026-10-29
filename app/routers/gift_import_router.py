from fastapi import APIRouter, Depends
from app.models.gift import Gift
from app.models.gift_import import GiftImportRequest
from app.models.identifiers import DatabaseId
from app.models.user import User
from app.services.gift_import_service import GiftImportService
from app.services.gift_privacy import owner_gift_response
from app.utils.jwt import get_current_user

router = APIRouter(prefix="/events", tags=["Gift imports"])
service = GiftImportService()


@router.get("/{event_id}/gift-options")
def get_gift_options(event_id: DatabaseId, user: User = Depends(get_current_user)):
    return service.get_options(event_id, user.id)


@router.post("/{event_id}/gifts/import", response_model=list[Gift])
def add_existing_gifts(event_id: DatabaseId, data: GiftImportRequest, user: User = Depends(get_current_user)):
    return [owner_gift_response(gift) for gift in service.add(event_id, user.id, data.items)]
