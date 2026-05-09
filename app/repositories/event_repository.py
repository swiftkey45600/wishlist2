from app.models import Event


class EventRepository:
    def create_event(self, event: Event) -> Event:
        raise NotImplementedError

    def get_event_by_id(self, event_id: int) -> Event | None:
        raise NotImplementedError

    def get_events_by_user(self, owner_id: int) -> list[Event]:
        raise NotImplementedError

    def get_event_by_public_token(self, public_token: str) -> Event | None:
        raise NotImplementedError

    def delete_event(self, event_id: int) -> None:
        raise NotImplementedError
