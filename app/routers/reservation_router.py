from fastapi import APIRouter, Depends, HTTPException
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.gift_repository import GiftRepository
from app.models.reservation import ReservationCreateRequest
from app.services.reservation_service import ReservationService
from app.repositories.gift_repository import GiftRepository
from app.models.user import User
from app.utils.jwt import get_current_user


router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"]
)

reservation_repo = ReservationRepository()
gift_repo = GiftRepository()
reservation_service = ReservationService(reservation_repo, gift_repo)


@router.post("/")
def reserve_gift(request: ReservationCreateRequest, current_user: User = Depends(get_current_user)):
    return reservation_service.reserve_gift(
        request.gift_id,
        current_user.name,
        request.is_anonymous,
        current_user.id,
    )

@router.get("/{reservation_id}")
def get_reservation(reservation_id: int):
    return reservation_service.get_reservation(reservation_id)

@router.delete("/{reservation_id}")
def unreserve_gift(reservation_id: int, current_user: User = Depends(get_current_user)):
    reservation = reservation_service.get_reservation(reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if reservation.reserver_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only cancel your own reservation")
    reservation_service.unreserve_gift(reservation_id)
    return {"message": "Reservation cancelled"}
