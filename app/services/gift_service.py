from typing import List

from fastapi import HTTPException

from app.models.gift import Gift
from app.repositories.contribution_repository import ContributionRepository
from app.repositories.gift_repository import GiftRepository
from app.repositories.image_repository import ImageRepository
from app.repositories.marketplace_links_repository import MarketplacesLinksRepository


class GiftService:
    def __init__(
        self,
        gift_repository: GiftRepository,
        image_repository: ImageRepository,
        marketplace_links_repository: MarketplacesLinksRepository,
        contribution_repository: ContributionRepository,
    ):
        self.gift_repository = gift_repository
        self.image_repository = image_repository
        self.marketplace_links_repository = marketplace_links_repository
        self.contribution_repository = contribution_repository

    def _get_image_url(self, image_id: int) -> str:
        return f"/images/{image_id}"

    def _fill_image(self, gift: Gift) -> None:
        if gift.image_id is None:
            return

        image = self.image_repository.get_image_by_id(gift.image_id)
        if image is None:
            return

        gift.image_url = self._get_image_url(image.id)
        if gift.picture_url is None:
            gift.picture_url = gift.image_url

    def _fill_marketplace_links(self, gift: Gift) -> None:
        gift.marketplace_links = self.marketplace_links_repository.get_all()

    def _fill_contribution_total(self, gift: Gift) -> None:
        gift.contribution_total = 0

    def _prepare_gift_response(self, gift: Gift) -> Gift:
        self._fill_image(gift)
        self._fill_marketplace_links(gift)
        return gift

    def create_gift(self, gift: Gift) -> Gift:
        if not gift.event_id:
            raise HTTPException(status_code=400, detail="event_id is required")

        if gift.image_id is not None and self.image_repository.get_image_by_id(gift.image_id) is None:
            raise HTTPException(status_code=404, detail="Image not found")

        created_gift = self.gift_repository.create_gift(gift)
        return self._prepare_gift_response(created_gift)

    def get_gift_by_id(self, gift_id: int) -> Gift:
        gift = self.gift_repository.get_gift_by_id(gift_id)
        if gift is None:
            raise HTTPException(status_code=404, detail="Gift not found")
        return self._prepare_gift_response(gift)

    def get_gifts_by_event(self, event_id: int) -> List[Gift]:
        gifts = self.gift_repository.get_gifts_by_event(event_id)
        return [self._prepare_gift_response(gift) for gift in gifts]

    def update_gift_status(self, gift_id: int, status: str) -> Gift:
        gift = self.gift_repository.update_gift_status(gift_id, status)
        if gift is None:
            raise HTTPException(status_code=404, detail="Gift not found")
        return self._prepare_gift_response(gift)

    def delete_gift(self, gift_id: int) -> None:
        if not self.gift_repository.delete_gift(gift_id):
            raise HTTPException(status_code=404, detail="Gift not found")