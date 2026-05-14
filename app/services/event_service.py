from app.models import Event
from app.repositories import EventRepository
from app.repositories import GiftRepository


class EventService:
    def __init__(
        self, event_repository: EventRepository, #gift_repository: GiftRepository
    ):
        self.event_repository = event_repository
        #self.gift_repository = gift_repository

    def create_event(
        self,
        owner_id: int,
        title: str,
        description: str | None = None,
        event_date: str | None = None,
        place: str | None = None,
    ) -> Event:
        new_event = Event(
            owner_id=owner_id,
            title=title,
            description=description,
            event_date=event_date,
            place=place,
        )

        return self.event_repository.create_event(new_event)

    def get_event(self, event_id: int) -> Event | None:
        return self.event_repository.get_event_by_id(event_id)

    def get_user_events(self, owner_id: int) -> list[Event]:
        return self.event_repository.get_events_by_user(owner_id)

    def get_event_by_token(self, public_token: str) -> Event | None:
        return self.event_repository.get_event_by_public_token(public_token)

    def list_events(self) -> list[Event]:
        return self.event_repository.list_events()

    def delete_event(self, event_id: int) -> bool:
        return self.event_repository.delete_event(event_id)
