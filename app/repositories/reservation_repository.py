from app.models import Reservation


class ReservationRepository:
    def __init__(self):
        self.reservations: list[Reservation] = []
        self._next_id = 1

    def reserve_gift(self, reservation: Reservation) -> Reservation:
        reservation.id = self._next_id
        self.reservations.append(reservation)
        self._next_id += 1
        return reservation

    def unreserve_gift(self, gift_id: int) -> None:
        reservation = self.get_reservation_by_gift(gift_id)
        if reservation:
            self.reservations.remove(reservation)

    def get_reservation_by_gift(self, gift_id: int) -> Reservation | None:
        for reservation in self.reservations:
            if reservation.gift_id == gift_id:
                return reservation
        return None

