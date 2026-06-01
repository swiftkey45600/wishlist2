from app.models.gift import Gift
from app.repositories.gift_repository import GiftRepository
from app.repositories.image_repository import ImageRepository


class GiftsManager:
    def __init__(self, gift_repo: GiftRepository, image_repo: ImageRepository):
        self.gift_repo = gift_repo
        self.image_repo = image_repo

    def create_gift(self, gift: Gift) -> Gift:
        return self.gift_repo.create_gift(gift)

    def get_gift_by_id(self, gift_id: int) -> Gift | None:
        gift = self.gift_repo.get_gift_by_id(gift_id)

        if gift is None:
            return None

        if gift.image_id is not None:
            image = self.image_repo.get_image_by_id(gift.image_id)
            gift.image = image

        return gift

    def get_gifts_by_event(self, event_id: int) -> list[Gift]:
        gifts = self.gift_repo.get_gifts_by_event(event_id)

        for gift in gifts:
            if gift.image_id is not None:
                image = self.image_repo.get_image_by_id(gift.image_id)
                gift.image = image

        return gifts

    def update_gift_status(self, gift_id: int, status: str) -> Gift | None:
        gift = self.gift_repo.update_gift_status(gift_id, status)

        if gift is None:
            return None

        if gift.image_id is not None:
            image = self.image_repo.get_image_by_id(gift.image_id)
            gift.image = image

        return gift

    def delete_gift(self, gift_id: int) -> bool:
        return self.gift_repo.delete_gift(gift_id)