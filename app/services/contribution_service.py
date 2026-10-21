from fastapi import HTTPException

from app.models.contribution import Contribution, ContributionCreateRequest, ContributionResponse
from app.models.gift import Gift
from app.models.user import User
from app.repositories.contribution_repository import ContributionRepository
from app.repositories.event_repository import EventRepository
from app.repositories.gift_repository import GiftRepository
from app.repositories.reservation_repository import ReservationRepository
from app.utils.security import hash_password, verify_password


class ContributionService:
    def __init__(
        self,
        contribution_repository: ContributionRepository,
        gift_repository: GiftRepository | None = None,
        event_repository: EventRepository | None = None,
        reservation_repository: ReservationRepository | None = None,
    ):
        self.contribution_repository = contribution_repository
        self.gift_repository = gift_repository or GiftRepository()
        self.event_repository = event_repository or EventRepository()
        self.reservation_repository = reservation_repository or ReservationRepository()

    def _check_public_gift(self, public_token: str, gift_id: int) -> Gift:
        event = self.event_repository.get_event_by_public_token(public_token)
        gift = self.gift_repository.get_gift_by_id(gift_id)
        if event is None or gift is None or gift.event_id != event.id:
            raise HTTPException(status_code=404, detail="Gift not found")
        return gift

    def _check_rate_limit(self, client_ip: str, gift_id: int | None = None) -> None:
        retry_after = self.reservation_repository.check_guest_rate_limit(f"contribution:{client_ip}", gift_id)
        if retry_after is not None:
            raise HTTPException(status_code=429, detail="Too many contribution attempts", headers={"Retry-After": str(retry_after)})

    def _response(
        self, contribution: Contribution, current_user: User | None = None, can_withdraw: bool = True
    ) -> ContributionResponse:
        requires_word = (
            contribution.contributor_id is None
            and self.contribution_repository.get_secret_word_hash(contribution.id) is not None
        )
        is_author = current_user is not None and contribution.contributor_id == current_user.id
        return ContributionResponse(
            id=contribution.id,
            amount=contribution.amount,
            is_anonymous=contribution.is_anonymous,
            contributor_name=None if contribution.is_anonymous else contribution.contributor_name,
            can_cancel=can_withdraw and (requires_word or is_author),
            requires_secret_word=requires_word,
        )

    def add_contribution(
        self, public_token: str, gift_id: int, data: ContributionCreateRequest, current_user: User | None, client_ip: str
    ) -> ContributionResponse:
        self._check_public_gift(public_token, gift_id)
        secret_word_hash = None
        if current_user is None:
            if data.name is None or data.secret_word is None:
                raise HTTPException(status_code=422, detail="Name and secret word are required for guest contributions")
            self._check_rate_limit(client_ip)
            secret_word_hash = hash_password(data.secret_word.get_secret_value())
        contribution = Contribution(
            gift_id=gift_id,
            amount=data.amount,
            is_anonymous=data.is_anonymous,
            contributor_name=current_user.name if current_user else data.name,
            contributor_id=current_user.id if current_user else None,
        )
        try:
            created = self.contribution_repository.create_contribution(contribution, secret_word_hash)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return self._response(created, current_user)

    def get_gift_contributions(
        self, public_token: str, gift_id: int, current_user: User | None = None
    ) -> list[ContributionResponse]:
        gift = self._check_public_gift(public_token, gift_id)
        return [self._response(item, current_user, gift.status != "bought")
                for item in self.contribution_repository.get_contributions_by_gift(gift_id)]

    def get_owner_contributions(self, gift_id: int, current_user: User) -> list[ContributionResponse]:
        gift = self.gift_repository.get_gift_by_id(gift_id)
        if gift is None:
            raise HTTPException(status_code=404, detail="Gift not found")
        event = self.event_repository.get_event_by_id(gift.event_id)
        if event is None or event.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the event owner can view contributions by gift ID")
        return [self._response(item, current_user, gift.status != "bought")
                for item in self.contribution_repository.get_contributions_by_gift(gift_id)]

    def get_total_collected(self, gift_id: int) -> int:
        return self.contribution_repository.get_total_collected(gift_id)

    def delete_contribution(
        self, public_token: str, gift_id: int, contribution_id: int, current_user: User | None,
        secret_word: str | None, client_ip: str,
    ) -> None:
        self._check_public_gift(public_token, gift_id)
        contribution = self.contribution_repository.get_contribution_by_id(contribution_id)
        if contribution is None or contribution.gift_id != gift_id:
            raise HTTPException(status_code=404, detail="Contribution not found")
        contributor_id = None
        secret_word_hash = None
        if contribution.contributor_id is not None:
            if current_user is None or contribution.contributor_id != current_user.id:
                raise HTTPException(status_code=403, detail="You can only cancel your own contribution")
            contributor_id = current_user.id
        else:
            self._check_rate_limit(client_ip, gift_id)
            secret_word_hash = self.contribution_repository.get_secret_word_hash(contribution_id)
            if secret_word is None or secret_word_hash is None or not verify_password(secret_word, secret_word_hash):
                raise HTTPException(status_code=403, detail="Invalid secret word")
        try:
            deleted = self.contribution_repository.delete_contribution(contribution_id, contributor_id, secret_word_hash)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if not deleted:
            raise HTTPException(status_code=404, detail="Contribution not found")
