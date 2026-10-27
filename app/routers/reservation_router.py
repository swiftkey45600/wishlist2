from fastapi import APIRouter, Depends, HTTPException, Request
from app.models.identifiers import DatabaseId
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.gift_repository import GiftRepository
from app.models.reservation import (
    GuestReservationCancelRequest,
    GuestReservationCreateRequest,
    Reservation,
    ReservationCreateRequest,
)
from app.services.reservation_service import ReservationService
from app.models.user import User
from app.utils.jwt import get_current_user


router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"]
)
guest_router = APIRouter(prefix="/events/public", tags=["Reservations"])

reservation_repo = ReservationRepository()
gift_repo = GiftRepository()
reservation_service = ReservationService(reservation_repo, gift_repo)


@guest_router.post("/{public_token}/gifts/{gift_id}/reservation", response_model=Reservation)
def reserve_guest_gift(public_token: str, gift_id: DatabaseId, data: GuestReservationCreateRequest, request: Request):
    return reservation_service.reserve_guest_gift(
        public_token,
        gift_id,
        data.name,
        data.secret_word.get_secret_value(),
        request.client.host if request.client else "unknown",
    )


@guest_router.delete("/{public_token}/gifts/{gift_id}/reservation")
def unreserve_guest_gift(public_token: str, gift_id: DatabaseId, data: GuestReservationCancelRequest, request: Request):
    reservation_service.unreserve_guest_gift(
        public_token,
        gift_id,
        data.secret_word.get_secret_value(),
        request.client.host if request.client else "unknown",
    )
    return {"message": "Reservation cancelled"}


@router.post("/")
def reserve_gift(request: ReservationCreateRequest, current_user: User = Depends(get_current_user)):
    return reservation_service.reserve_gift(
        request.gift_id,
        current_user.name,
        request.is_anonymous,
        current_user.id,
        request.public_token,
    )

@router.get("/{reservation_id}")
def get_reservation(reservation_id: DatabaseId, current_user: User = Depends(get_current_user)):
    reservation = reservation_service.get_reservation(reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if reservation.reserver_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own reservation")
    return reservation

@router.delete("/{reservation_id}")
def unreserve_gift(reservation_id: DatabaseId, current_user: User = Depends(get_current_user)):
    reservation = reservation_service.get_reservation(reservation_id)
    if reservation is None:
        raise HTTPException(status_code=404, detail="Reservation not found")
    if reservation.reserver_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only cancel your own reservation")
    reservation_service.unreserve_gift(reservation_id, current_user.id)
    return {"message": "Reservation cancelled"}
