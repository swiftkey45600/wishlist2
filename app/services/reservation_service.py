from sqlite3 import IntegrityError

from fastapi import HTTPException

from app.models.gift import Gift
from app.models.reservation import Reservation
from app.repositories.gift_repository import GiftRepository
from app.repositories.reservation_repository import ReservationRepository
from app.repositories.event_repository import EventRepository
from app.utils.security import hash_password, verify_password


class ReservationService:
    def __init__(
        self,
        reservation_repository: ReservationRepository,
        gift_repository: GiftRepository,
        event_repository: EventRepository | None = None,
    ):
        self.reservation_repository = reservation_repository
        self.gift_repository = gift_repository
        self.event_repository = event_repository or EventRepository()

    def _check_guest_rate_limit(self, client_ip: str, gift_id: int | None = None) -> None:
        retry_after = self.reservation_repository.check_guest_rate_limit(client_ip, gift_id)
        if retry_after is not None:
            raise HTTPException(
                status_code=429,
                detail="Too many reservation attempts. Try again later",
                headers={"Retry-After": str(retry_after)},
            )

    def _get_public_gift(self, public_token: str, gift_id: int) -> Gift:
        event = self.event_repository.get_event_by_public_token(public_token)
        gift = self.gift_repository.get_gift_by_id(gift_id)
        if event is None or gift is None or gift.event_id != event.id:
            raise HTTPException(status_code=404, detail="Gift not found")
        return gift

    def reserve_guest_gift(
        self, public_token: str, gift_id: int, name: str, secret_word: str, client_ip: str
    ) -> Reservation:
        self._check_guest_rate_limit(client_ip)
        gift = self._get_public_gift(public_token, gift_id)
        event = self.event_repository.get_event_by_public_token(public_token)
        if event is not None and event.status == "archived":
            raise HTTPException(status_code=409, detail="Event is archived")
        if gift.status != "available" or gift.contribution_goal is not None:
            raise HTTPException(status_code=409, detail="Gift is not available for reservation")
        reservation = Reservation(gift_id=gift_id, is_anonymous=False, reserver_name=name)
        try:
            return self.reservation_repository.reserve_guest_gift(reservation, hash_password(secret_word))
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Gift is not available for reservation") from exc

    def unreserve_guest_gift(self, public_token: str, gift_id: int, secret_word: str, client_ip: str) -> None:
        self._get_public_gift(public_token, gift_id)
        self._check_guest_rate_limit(client_ip, gift_id)
        reservation = self.reservation_repository.get_reservation_by_gift(gift_id)
        if reservation is None:
            raise HTTPException(status_code=404, detail="Reservation not found")
        secret_word_hash = self.reservation_repository.get_secret_word_hash(reservation.id)
        if reservation.reserver_id is not None or secret_word_hash is None:
            raise HTTPException(status_code=403, detail="This reservation cannot be cancelled with a secret word")
        if not verify_password(secret_word, secret_word_hash):
            raise HTTPException(status_code=403, detail="Invalid secret word")
        if not self.reservation_repository.unreserve_guest_gift(reservation, secret_word_hash):
            raise HTTPException(status_code=404, detail="Reservation not found")

    def reserve_gift(
            self,
            gift_id: int,
            reserver_name: str | None = None,
            is_anonymous: bool = False,
            reserver_id: int | None = None,
    ) -> Reservation:
        gift = self.gift_repository.get_gift_by_id(gift_id)
        if gift is None:
            raise HTTPException(status_code=404, detail="Gift not found")
        event = self.event_repository.get_event_by_id(gift.event_id)
        if event is not None and event.status == "archived":
            raise HTTPException(status_code=409, detail="Event is archived")
        if event is not None and event.owner_id == reserver_id:
            raise HTTPException(status_code=403, detail="Event owner cannot reserve their own gift")
        if gift.status != "available" or gift.contribution_goal is not None:
            raise HTTPException(status_code=409, detail="Gift is not available for reservation")

        existing = self.reservation_repository.get_reservation_by_gift(gift_id)

        if existing:
            raise HTTPException(status_code=409, detail="Gift is already reserved")

        reservation = Reservation(
            gift_id=gift_id,
            is_anonymous=is_anonymous,
            reserver_name=reserver_name,
            reserver_id=reserver_id,
        )

        try:
            return self.reservation_repository.reserve_gift(reservation)
        except IntegrityError as error:
            raise HTTPException(status_code=409, detail="Gift is not available for reservation") from error

    def unreserve_gift(self, reservation_id: int) -> None:
        reservation = self.get_reservation(reservation_id)
        if reservation is None:
            raise HTTPException(status_code=404, detail="Reservation not found")

        deleted = self.reservation_repository.unreserve_by_id(reservation_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Reservation not found")
        gift = self.gift_repository.get_gift_by_id(reservation.gift_id)
        if gift is not None and gift.status != "bought":
            self.gift_repository.update_gift_status(reservation.gift_id, "available")

    def unreserve_gift_by_user(self, gift_id: int, user_id: int) -> None:
        reservation = self.reservation_repository.get_reservation_by_gift(gift_id)
        if reservation is None:
            raise HTTPException(status_code=404, detail="Reservation not found")
        if reservation.reserver_id != user_id:
            raise HTTPException(status_code=403, detail="You can only cancel your own reservation")

        self.reservation_repository.unreserve_by_id(reservation.id)
        gift = self.gift_repository.get_gift_by_id(gift_id)
        if gift is not None and gift.status != "bought":
            self.gift_repository.update_gift_status(gift_id, "available")

    def clear_reservation_for_gift(self, gift_id: int) -> None:
        reservation = self.reservation_repository.get_reservation_by_gift(gift_id)
        if reservation is not None:
            self.unreserve_gift(reservation.id)

    def get_reservation(self, reservation_id: int) -> Reservation | None:
        return self.reservation_repository.get_reservation_by_id(reservation_id)
