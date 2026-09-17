from fastapi import HTTPException

from app.models.reservation import Reservation
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.gift_repository import GiftRepository


class ReservationService:
    def __init__(self, reservation_repository: ReservationRepository, gift_repository: GiftRepository):
        self.reservation_repository = reservation_repository
        self.gift_repository = gift_repository

    def reserve_gift(
            self,
            gift_id: int,
            reserver_name: str | None = None,
            is_anonymous: bool = False,
    ) -> Reservation:
        existing = self.reservation_repository.get_reservation_by_gift(gift_id)

        if existing:
            raise HTTPException(status_code=409, detail="Gift is already reserved")

        reservation = Reservation(
            gift_id=gift_id,
            is_anonymous=is_anonymous,
            reserver_name=reserver_name,
        )

        result = self.reservation_repository.reserve_gift(reservation)
        self.gift_repository.update_gift_status(gift_id, "reserved")
        return result

    def unreserve_gift(self, reservation_id: int) -> None:
        reservation = self.reservation_repository.get_reservation_by_id(reservation_id)
        if not reservation:
            raise HTTPException(status_code=404, detail="Reservation not found")
        self.reservation_repository.unreserve_by_id(reservation_id)
        self.gift_repository.update_gift_status(reservation.gift_id, "available")

    def get_reservation(self, reservation_id: int) -> Reservation | None:
        return self.reservation_repository.get_reservation_by_id(reservation_id)