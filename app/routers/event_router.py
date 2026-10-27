from typing import Annotated

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from app.models.event import EventCopyRequest, EventCreateRequest, EventStatus, EventUpdateRequest
from app.models.gift import GiftFilters
from app.models.user import User
from app.services.event_service import EventService
from app.repositories.event_repository import EventRepository
from app.repositories.gift_repository import GiftRepository
from app.utils.jwt import get_current_user, get_optional_user
from app.services.gift_privacy import owner_gift_response, owner_gift_filters

router = APIRouter(
    prefix="/events",
    tags=["events"]
)

event_repository = EventRepository()
gift_repository = GiftRepository()
event_service = EventService(event_repository, gift_repository)

@router.get("/")
async def get_events(current_user: User = Depends(get_current_user), status: EventStatus | None = None):
    return {"events": event_service.get_user_events(current_user.id, status)}



@router.get("/user/{owner_id}")
async def get_user_events(owner_id: int, current_user: User = Depends(get_current_user), status: EventStatus | None = None):
    if owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own events")
    events = event_service.get_user_events(owner_id, status)
    if not events and status is None:
        raise HTTPException(status_code=404, detail="Owner has no events")
    return {"events": events}


@router.get("/public/{public_token}")
async def get_public_event(
    public_token: str, filters: Annotated[GiftFilters, Query()],
    current_user: User | None = Depends(get_optional_user),
):
    event = event_service.get_event_by_token(public_token)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    is_owner = current_user is not None and current_user.id == event.owner_id
    gifts = gift_repository.get_gifts_by_event(event.id, owner_gift_filters(filters) if is_owner else filters)
    if is_owner:
        gifts = [owner_gift_response(gift, filters.show_reservations) for gift in gifts]
    return {"event": event, "gifts": gifts}


@router.get("/{event_id}")
async def get_event(event_id: int, current_user: User = Depends(get_current_user)):
    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can view an event")
    return {"event": event}


@router.get("/{event_id}/statistics")
async def get_event_statistics(
    event_id: int,
    current_user: User = Depends(get_current_user),
):
    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the event owner can view statistics")
    return event_service.get_price_statistics(event_id)


@router.post("/")
async def create_event(event_request: EventCreateRequest, current_user: User = Depends(get_current_user)):
    if current_user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    event = event_service.create_event(
        owner_id=current_user.id,
        title=event_request.title,
        description=event_request.description,
        event_date=event_request.event_date,
        place=event_request.place,
    )
    if not event:
        raise HTTPException(status_code=400, detail="Event cannot be created")
    return {"event": event}


@router.patch("/{event_id}")
async def update_event(
    event_id: int,
    event_request: EventUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: you can only edit your own events")

    for field_name, value in event_request.model_dump(exclude_unset=True).items():
        setattr(event, field_name, value)

    return {"event": event_service.update_event(event_id, event)}


@router.patch("/{event_id}/archive")
async def archive_event(event_id: int, current_user: User = Depends(get_current_user)):
    return {"event": event_service.set_status(event_id, current_user.id, "archived")}


@router.patch("/{event_id}/restore")
async def restore_event(event_id: int, current_user: User = Depends(get_current_user)):
    return {"event": event_service.set_status(event_id, current_user.id, "active")}


@router.post("/{event_id}/copy", status_code=201)
async def copy_event(event_id: int, data: EventCopyRequest, current_user: User = Depends(get_current_user)):
    return {"event": event_service.copy_event(event_id, current_user.id, data)}


@router.delete("/{event_id}")
async def delete_event(event_id: int, current_user: User = Depends(get_current_user)):
    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: you can only delete your own events")
    event_service.delete_event(event_id)
    return {"deleted": True}
