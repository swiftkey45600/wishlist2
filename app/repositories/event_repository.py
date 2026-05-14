from app.models import Event


class EventRepository:
    def __init__(self):
        self.events: list[Event] = []
        self._next_id = 1

    def create_event(self, event: Event) -> Event:
        event.id = self._next_id

        self.events.append(event)
        self._next_id += 1

        return event

    def get_event_by_id(self, event_id: int) -> Event | None:
        for event in self.events:
            if event.id == event_id:
                return event
        return None

    def get_events_by_user(self, owner_id: int) -> list[Event]:
        return [event for event in self.events if event.owner_id == owner_id]

    def get_event_by_public_token(self, public_token: str) -> Event | None:
        for event in self.events:
            if event.public_token == public_token:
                return event
        return None

    def list_events(self) -> list[Event]:
        return self.events.copy()

    def delete_event(self, event_id: int) -> bool:
        old_length = len(self.events)
        self.events = [event for event in self.events if event.id != event_id]
        return old_length > len(self.events)