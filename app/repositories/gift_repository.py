from app.models import Gift


class GiftRepository:
    def create_gift(self, gift: Gift) -> Gift:
        raise NotImplementedError

    def get_gift_by_id(self, gift_id: int) -> Gift | None:
        raise NotImplementedError

    def get_gifts_by_event(self, event_id: int) -> list[Gift]:
        raise NotImplementedError

    def update_gift_status(self, gift_id: int, status: str) -> None:
        raise NotImplementedError

    def delete_gift(self, gift_id: int) -> None:
        raise NotImplementedError
