from dataclasses import dataclass


@dataclass
class Reservation:
    gift_id: int
    is_anonymous: bool
    id: int | None = None
    reserver_name: str | None = None

@dataclass
class ReservationCreateRequest:
    gift_id: int
    is_anonymous: bool
    reserver_name: str | None = None
