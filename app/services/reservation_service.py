from fastapi import HTTPException

from app.models.reservation import Reservation
from app.repositories.gift_repository import GiftRepository
from app.repositories.reservation_repository import ReservationRepository


class ReservationService:
    def __init__(self, reservation_repository: ReservationRepository, gift_repository: GiftRepository):
        self.reservation_repository = reservation_repository
        self.gift_repository = gift_repository

    def reserve_gift(
            self,
            gift_id: int,
            reserver_name: str | None = None,
            is_anonymous: bool = False,
            reserver_id: int | None = None,
    ) -> Reservation:
        gift = self.gift_repository.get_gift_by_id(gift_id)
        if gift is None:
            raise HTTPException(status_code=404, detail="Gift not found")
        if gift.status != "available":
            raise HTTPException(status_code=409, detail="Gift is not available for reservation")

        existing = self.reservation_repository.get_reservation_by_gift(gift_id)

        if existing:
            raise HTTPException(status_code=409, detail="Gift is already reserved")

        reservation = Reservation(
            gift_id=gift_id,
            is_anonymous=is_anonymous,
            reserver_name=reserver_name,
            reserver_id=reserver_id,
        )

        created_reservation = self.reservation_repository.reserve_gift(reservation)
        self.gift_repository.update_gift_status(gift_id, "reserved")
        return created_reservation

    def unreserve_gift(self, reservation_id: int) -> None:
        reservation = self.get_reservation(reservation_id)
        if reservation is None:
            raise HTTPException(status_code=404, detail="Reservation not found")

        deleted = self.reservation_repository.unreserve_by_id(reservation_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Reservation not found")
        gift = self.gift_repository.get_gift_by_id(reservation.gift_id)
        if gift is not None and gift.status != "bought":
            self.gift_repository.update_gift_status(reservation.gift_id, "available")

    def unreserve_gift_by_user(self, gift_id: int, user_id: int) -> None:
        reservation = self.reservation_repository.get_reservation_by_gift(gift_id)
        if reservation is None:
            raise HTTPException(status_code=404, detail="Reservation not found")
        if reservation.reserver_id != user_id:
            raise HTTPException(status_code=403, detail="You can only cancel your own reservation")

        self.reservation_repository.unreserve_by_id(reservation.id)
        gift = self.gift_repository.get_gift_by_id(gift_id)
        if gift is not None and gift.status != "bought":
            self.gift_repository.update_gift_status(gift_id, "available")

    def get_reservation(self, reservation_id: int) -> Reservation | None:
        return self.reservation_repository.get_reservation_by_id(reservation_id)
