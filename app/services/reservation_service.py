from fastapi import HTTPException

from app.models.reservation import Reservation
from app.repositories.reservation_repository import ReservationRepository


class ReservationService:
    def __init__(self, reservation_repository: ReservationRepository):
        self.reservation_repository = reservation_repository

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

        return self.reservation_repository.reserve_gift(reservation)

    def unreserve_gift(self, gift_id: int) -> None:
        deleted = self.reservation_repository.unreserve_gift(gift_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Reservation not found")

    def get_reservation(self, gift_id: int) -> Reservation | None:
        return self.reservation_repository.get_reservation_by_gift(gift_id)