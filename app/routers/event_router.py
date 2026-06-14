from fastapi import APIRouter, HTTPException, Depends
from app.models.event import EventCreateRequest
from app.models.user import User
from app.services.event_service import EventService
from app.repositories.event_repository import EventRepository
from app.repositories.gift_repository import GiftRepository
from app.utils.jwt import get_current_user

router = APIRouter(
    prefix="/events",
    tags=["events"]
)

event_repository = EventRepository()
gift_repository = GiftRepository()
event_service = EventService(event_repository)

@router.get("/")
async def get_events(current_user: User = Depends(get_current_user)):
    return {"events": event_service.get_user_events(current_user.id)}



@router.get("/user/{owner_id}")
async def get_user_events(owner_id: int, current_user: User = Depends(get_current_user)):
    events = event_service.get_user_events(owner_id)
    if not events:
        raise HTTPException(status_code=404, detail="Owner has no events")
    return {"events": events}


@router.get("/public/{public_token}")
async def get_public_event(public_token: str):
    event = event_service.get_event_by_token(public_token)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    gifts = gift_repository.get_gifts_by_event(event.id)
    return {"event": event, "gifts": gifts}


@router.get("/{event_id}")
async def get_event(event_id: int, current_user: User = Depends(get_current_user)):
    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"event": event}


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


@router.delete("/{event_id}")
async def delete_event(event_id: int, current_user: User = Depends(get_current_user)):
    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: you can only delete your own events")
    event_service.delete_event(event_id)
    return {"deleted": True}
