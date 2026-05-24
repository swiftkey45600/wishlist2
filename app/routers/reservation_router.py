from fastapi import APIRouter
from app.models import Reservation
from app.repositories.reservation_repository import ReservationRepository
from app.services.reservation_service import ReservationService

router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"]
)

reservation_repo = ReservationRepository()
reservation_service = ReservationService(reservation_repo)


@router.post("/{gift_id}", response_model=Reservation)
def reserve_gift(gift_id: int, reserver_name: str | None = None, is_anonymous: bool = False):
    return reservation_service.reserve_gift(gift_id, reserver_name, is_anonymous)


@router.get("/{gift_id}", response_model=Reservation | None)
def get_reservation(gift_id: int):
    return reservation_service.get_reservation(gift_id)


@router.delete("/{gift_id}")
def unreserve_gift(gift_id: int):
    reservation_service.unreserve_gift(gift_id)
    return {"message": "Reservation cancelled"}