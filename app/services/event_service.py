import secrets

from fastapi import HTTPException

from app.models import Event
from app.models.event import EventCopyRequest, EventStatus
from app.repositories import EventRepository
from app.repositories import GiftRepository


class EventService:
    def __init__(
        self,
        event_repository: EventRepository,
        gift_repository: GiftRepository | None = None,
    ):
        self.event_repository = event_repository
        self.gift_repository = gift_repository

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
            public_token=secrets.token_urlsafe(16),
        )

        return self.event_repository.create_event(new_event)

    #TODO фалйловая база данных - использование словарей для кеширования (айди и токены)
    def get_event(self, event_id: int) -> Event | None:
        return self.event_repository.get_event_by_id(event_id)

    def get_user_events(self, owner_id: int, status: EventStatus | None = None) -> list[Event]:
        return self.event_repository.get_events_by_user(owner_id, status)

    def _owned_event(self, event_id: int, owner_id: int) -> Event:
        event = self.get_event(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        if event.owner_id != owner_id:
            raise HTTPException(status_code=403, detail="Only the event owner can manage this event")
        return event

    def set_status(self, event_id: int, owner_id: int, status: EventStatus) -> Event:
        self._owned_event(event_id, owner_id)
        event = self.event_repository.set_status(event_id, owner_id, status)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        return event

    def copy_event(self, event_id: int, owner_id: int, data: EventCopyRequest) -> Event:
        self._owned_event(event_id, owner_id)
        event = self.event_repository.copy_event(event_id, owner_id, data.title, data.event_date)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        return event

    def get_event_by_token(self, public_token: str) -> Event | None:
        return self.event_repository.get_event_by_public_token(public_token)

    def list_events(self) -> list[Event]:
        return self.event_repository.list_events()

    def delete_event(self, event_id: int) -> bool:
        return self.event_repository.delete_event(event_id)

    def update_event(self, event_id: int, event: Event) -> Event | None:
        return self.event_repository.update_event(event_id, event)

    def get_price_statistics(self, event_id: int) -> dict:
        if self.gift_repository is None:
            raise RuntimeError("Gift repository is required for price statistics")

        gifts = self.gift_repository.get_gifts_by_event(event_id)
        ranges = [
            {
                "key": "under_1000",
                "label": "До 1 000 ₽",
                "min_price": 0,
                "max_price": 1000,
                "count": 0,
            },
            {
                "key": "from_1000_to_3000",
                "label": "1 000–3 000 ₽",
                "min_price": 1000,
                "max_price": 3000,
                "count": 0,
            },
            {
                "key": "from_3000_to_5000",
                "label": "3 000–5 000 ₽",
                "min_price": 3000,
                "max_price": 5000,
                "count": 0,
            },
            {
                "key": "from_5000",
                "label": "От 5 000 ₽",
                "min_price": 5000,
                "max_price": None,
                "count": 0,
            },
        ]

        for gift in gifts:
            if gift.price is None or gift.price < 0:
                continue
            for price_range in ranges:
                upper_bound = price_range["max_price"]
                if gift.price >= price_range["min_price"] and (
                    upper_bound is None or gift.price < upper_bound
                ):
                    price_range["count"] += 1
                    break

        return {
            "total_gifts": sum(price_range["count"] for price_range in ranges),
            "price_ranges": ranges,
        }
