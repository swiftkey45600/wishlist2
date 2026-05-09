from app.models import Reservation


class ReservationRepository:
    def reserve_gift(self, reservation: Reservation) -> Reservation:
        raise NotImplementedError

    def unreserve_gift(self, gift_id: int) -> None:
        raise NotImplementedError

    def get_reservation_by_gift(self, gift_id: int) -> Reservation | None:
        raise NotImplementedError
