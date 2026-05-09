from app.models import Gift
from app.repositories import GiftRepository, ContributionRepository


class GiftService:
    def __init__(self, gift_repository: GiftRepository, contribution_repository: ContributionRepository):
        self.gift_repository = gift_repository
        self.contribution_repository = contribution_repository

    def create_gift(self, event_id: int, title: str, price: int) -> Gift:
        raise NotImplementedError

    def get_gift(self, gift_id: int) -> Gift | None:
        return self.gift_repository.get_gift_by_id(gift_id)

    def get_event_gifts(self, event_id: int) -> list[Gift]:
        return self.gift_repository.get_gifts_by_event(event_id)

    def get_gift_progress(self, gift_id: int) -> float:
        raise NotImplementedError

    def update_gift_status(self, gift_id: int, status: str) -> None:
        self.gift_repository.update_gift_status(gift_id, status)

    def delete_gift(self, gift_id: int) -> None:
        self.gift_repository.delete_gift(gift_id)
