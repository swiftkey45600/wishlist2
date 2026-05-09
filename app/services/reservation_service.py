from app.models import Reservation
from app.repositories import ReservationRepository


class ReservationService:
    def __init__(self, reservation_repository: ReservationRepository):
        self.reservation_repository = reservation_repository

    def reserve_gift(self, gift_id: int, reserver_name: str | None = None, is_anonymous: bool = False) -> Reservation:
        raise NotImplementedError

    def unreserve_gift(self, gift_id: int) -> None:
        self.reservation_repository.unreserve_gift(gift_id)

    def get_reservation(self, gift_id: int) -> Reservation | None:
        return self.reservation_repository.get_reservation_by_gift(gift_id)
