import secrets
from datetime import date, datetime
from sqlite3 import IntegrityError

from fastapi import HTTPException

from app.models import Event
from app.models.event import EventCopyRequest, EventStatus
from app.repositories import EventRepository
from app.repositories import GiftRepository
from app.repositories.image_repository import ImageRepository


class EventService:
    def __init__(
        self,
        event_repository: EventRepository,
        gift_repository: GiftRepository | None = None,
    ):
        self.event_repository = event_repository
        self.gift_repository = gift_repository
        self.image_repository = ImageRepository()

    def create_event(
        self,
        owner_id: int,
        title: str,
        description: str | None = None,
        event_date: str | None = None,
        end_date: str | None = None,
        place: str | None = None,
        cover_image_id: int | None = None,
    ) -> Event:
        self._validate_cover(cover_image_id)
        self._validate_dates(event_date, end_date)
        new_event = Event(
            owner_id=owner_id,
            title=title,
            description=description,
            event_date=event_date,
            end_date=end_date,
            place=place,
            public_token=secrets.token_urlsafe(16),
            cover_image_id=cover_image_id,
        )

        try:
            return self.event_repository.create_event(new_event)
        except IntegrityError as error:
            raise HTTPException(status_code=409, detail="Event references changed; reload and try again") from error

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
        source = self._owned_event(event_id, owner_id)
        if status == "active" and (source.end_date or source.event_date):
            try:
                event_day = date.fromisoformat((source.end_date or source.event_date)[:10])
            except ValueError:
                event_day = None
            if event_day is not None and event_day < date.today():
                raise HTTPException(status_code=409, detail="Choose a future date before restoring this event")
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

    def delete_event(self, event_id: int, owner_id: int, keep_gifts: bool = False) -> bool:
        return self.event_repository.delete_event(event_id, owner_id, keep_gifts)

    def update_event(self, event_id: int, event: Event) -> Event | None:
        self._validate_cover(event.cover_image_id)
        self._validate_dates(event.event_date, event.end_date)
        try:
            return self.event_repository.update_event(event_id, event)
        except IntegrityError as error:
            raise HTTPException(status_code=409, detail="Event references changed; reload and try again") from error

    def _validate_dates(self, start: str | None, end: str | None) -> None:
        if not end:
            return
        if not start:
            raise HTTPException(status_code=422, detail="Start date is required when an end date is set")
        try:
            start_value = datetime.fromisoformat(start)
            end_value = datetime.fromisoformat(end)
            if start_value.tzinfo is not None or end_value.tzinfo is not None:
                start_value = start_value.replace(tzinfo=None)
                end_value = end_value.replace(tzinfo=None)
            if end_value < start_value:
                raise HTTPException(status_code=422, detail="End date must not precede start date")
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid event date") from None

    def _validate_cover(self, image_id: int | None) -> None:
        if image_id is not None and self.image_repository.get_image_by_id(image_id) is None:
            raise HTTPException(status_code=404, detail="Cover image not found")

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
