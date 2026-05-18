from fastapi import APIRouter
from fastapi import HTTPException
from app.models.event import EventCreateRequest
from app.services.event_service import EventService
from app.repositories.event_repository import EventRepository

router = APIRouter(
    prefix="/events",
    tags=["events"]
)

event_repository = EventRepository()
event_service = EventService(event_repository)

@router.get("/")
async def get_events():
    return {"events": event_service.list_events()}

#TODO путь /users/user_id/events
@router.get("/user/{owner_id}")
async def get_user_events(owner_id: int):
    events = event_service.get_user_events(owner_id)
    return {"events": events} if events else {"error": "Owner has no events"}

@router.get("/{event_id}")
async def get_event(event_id: int):
    event = event_service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    else:
        return {"event": event}

@router.post("/")
async def create_event(event_request: EventCreateRequest):
    event = event_service.create_event(
        owner_id=1,
        title=event_request.title,
        description=event_request.description,
        event_date=event_request.event_date,
        place=event_request.place
    )
    return {"event": event} if event else {"error": "Event cannot be created"}


@router.delete("/{event_id}")
async def delete_event(event_id: int):
    is_deleted = event_service.delete_event(event_id)
    if not is_deleted:
        raise HTTPException(status_code=404, detail="Event not found")
    else:
        return {"deleted": True}
