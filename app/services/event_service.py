from app.models import Event
from app.repositories import EventRepository
from app.repositories import GiftRepository


class EventService:
    def __init__(self, event_repository: EventRepository, gift_repository: GiftRepository):
        self.event_repository = event_repository
        self.gift_repository = gift_repository

    def create_event(self, owner_id: int, title: str, description: str | None = None) -> Event:
        raise NotImplementedError

    def get_event(self, event_id: int) -> Event | None:
        return self.event_repository.get_event_by_id(event_id)

    def get_user_events(self, owner_id: int) -> list[Event]:
        return self.event_repository.get_events_by_user(owner_id)

    def get_event_by_token(self, public_token: str) -> Event | None:
        return self.event_repository.get_event_by_public_token(public_token)

    def delete_event(self, event_id: int) -> None:
        self.event_repository.delete_event(event_id)

    
