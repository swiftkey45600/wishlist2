from fastapi import APIRouter, Body, Depends, Request

from app.models.contribution import ContributionCreateRequest, ContributionResponse
from app.models.reservation import GuestReservationCancelRequest
from app.models.user import User
from app.repositories.contribution_repository import ContributionRepository
from app.services.contribution_service import ContributionService
from app.utils.jwt import get_current_user, get_optional_user


router = APIRouter(tags=["Contributions"])
contribution_service = ContributionService(ContributionRepository())


@router.get("/gifts/{gift_id}/contributions", response_model=list[ContributionResponse])
def get_owner_contributions(gift_id: int, current_user: User = Depends(get_current_user)):
    return contribution_service.get_owner_contributions(gift_id, current_user)


@router.get("/events/public/{public_token}/gifts/{gift_id}/contributions", response_model=list[ContributionResponse])
def get_public_contributions(public_token: str, gift_id: int, current_user: User | None = Depends(get_optional_user)):
    return contribution_service.get_gift_contributions(public_token, gift_id, current_user)


@router.post("/events/public/{public_token}/gifts/{gift_id}/contributions", response_model=ContributionResponse)
def add_contribution(
    public_token: str, gift_id: int, data: ContributionCreateRequest, request: Request,
    current_user: User | None = Depends(get_optional_user),
):
    return contribution_service.add_contribution(
        public_token, gift_id, data, current_user, request.client.host if request.client else "unknown"
    )


@router.delete("/events/public/{public_token}/gifts/{gift_id}/contributions/{contribution_id}")
def delete_contribution(
    public_token: str, gift_id: int, contribution_id: int, request: Request,
    data: GuestReservationCancelRequest | None = Body(default=None),
    current_user: User | None = Depends(get_optional_user),
):
    contribution_service.delete_contribution(
        public_token, gift_id, contribution_id, current_user,
        data.secret_word.get_secret_value() if data else None,
        request.client.host if request.client else "unknown",
    )
    return {"message": "Contribution cancelled"}
