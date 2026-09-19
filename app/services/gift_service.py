from typing import List

from fastapi import HTTPException

from app.models.gift import Gift
from app.repositories.contribution_repository import ContributionRepository
from app.repositories.gift_repository import GiftRepository
from app.repositories.image_repository import ImageRepository
from app.repositories.marketplace_links_repository import MarketplacesLinksRepository
from app.repositories.event_repository import EventRepository
from app.services.reservation_service import ReservationService
from app.models.user import User


class GiftService:
    def __init__(
        self,
        gift_repository: GiftRepository,
        image_repository: ImageRepository,
        marketplace_links_repository: MarketplacesLinksRepository,
        contribution_repository: ContributionRepository,
        event_repository: EventRepository,
        reservation_service: ReservationService,
    ):
        self.gift_repository = gift_repository
        self.image_repository = image_repository
        self.marketplace_links_repository = marketplace_links_repository
        self.contribution_repository = contribution_repository
        self.event_repository = event_repository
        self.reservation_service = reservation_service

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
        if status != "bought":
            raise HTTPException(status_code=400, detail="Invalid gift status")
        gift = self.gift_repository.update_gift_status(gift_id, status)
        if gift is None:
            raise HTTPException(status_code=404, detail="Gift not found")
        return self._prepare_gift_response(gift)

    def update_gift(
        self,
        gift_id: int,
        data: dict,
        current_user: User,
    ) -> Gift:
        gift = self.get_gift_by_id(gift_id)
        event = self.event_repository.get_event_by_id(gift.event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")

        if event.owner_id != current_user.id:
            if set(data) - {"is_reserved"}:
                raise HTTPException(status_code=403, detail="Only the event owner can edit a gift")
            if "is_reserved" not in data:
                raise HTTPException(status_code=400, detail="is_reserved is required")

            if data["is_reserved"]:
                self.reservation_service.reserve_gift(
                    gift_id,
                    reserver_name=current_user.name,
                    reserver_id=current_user.id,
                )
            else:
                self.reservation_service.unreserve_gift_by_user(gift_id, current_user.id)

            return self.get_gift_by_id(gift_id)

        if "is_reserved" in data:
            raise HTTPException(status_code=403, detail="Event owner cannot reserve their own gift")

        if data.get("image_id") is not None and self.image_repository.get_image_by_id(data["image_id"]) is None:
            raise HTTPException(status_code=404, detail="Image not found")

        if data.get("status") is not None and data["status"] not in {"available", "bought"}:
            raise HTTPException(status_code=400, detail="Invalid gift status")

        if data.get("status") == "available":
            self.reservation_service.clear_reservation_for_gift(gift_id)

        updated_gift = self.gift_repository.update_gift(gift_id, data)
        return self._prepare_gift_response(updated_gift)

    def delete_gift(self, gift_id: int) -> None:
        if not self.gift_repository.delete_gift(gift_id):
            raise HTTPException(status_code=404, detail="Gift not found")
