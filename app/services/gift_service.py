from app.models import Gift
from app.repositories import GiftRepository, ContributionRepository


class GiftService:
    def __init__(self, gift_repository: GiftRepository, contribution_repository: ContributionRepository):
        self.gift_repository = gift_repository
        self.contribution_repository = contribution_repository

    def create_gift(self, gift: Gift) -> Gift:
        if not gift.event_id:
            raise HTTPException(status_code=400, detail="event_id is required")
        return self.gift_repository.create_gift(gift)

    def get_gift_by_id(self, gift_id: int) -> Gift:
        gift = self.gift_repository.get_gift_by_id(gift_id)
        if gift is None:
            raise HTTPException(status_code=404, detail="Gift not found")
        return gift

    def get_gifts_by_event(self, event_id: int) -> List[Gift]:
        return self.gift_repository.get_gifts_by_event(event_id)

    def update_gift_status(self, gift_id: int, status: str) -> Gift:
        gift = self.gift_repository.update_gift_status(gift_id, status)
        if gift is None:
            raise HTTPException(status_code=404, detail="Gift not found")
        return gift

    def delete_gift(self, gift_id: int) -> None:
        if not self.gift_repository.delete_gift(gift_id):
            raise HTTPException(status_code=404, detail="Gift not found")
