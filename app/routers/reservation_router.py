from fastapi import APIRouter
from app.repositories.reservation_repository import ReservationRepository
from app.models.reservation import ReservationCreateRequest
from app.services.reservation_service import ReservationService


router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"]
)

reservation_repo = ReservationRepository()
reservation_service = ReservationService(reservation_repo)


@router.post("/")
def reserve_gift(request: ReservationCreateRequest):
    return reservation_service.reserve_gift(request.gift_id, request.reserver_name, request.is_anonymous)

@router.get("/{reservation_id}")
def get_reservation(reservation_id: int):
    return reservation_service.get_reservation(reservation_id)

@router.delete("/{reservation_id}")
def unreserve_gift(reservation_id: int):
    reservation_service.unreserve_gift(reservation_id)
    return {"message": "Reservation cancelled"}