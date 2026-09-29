from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.models.user import User
from app.repositories.image_repository import ImageRepository
from app.repositories.marketplace_links_repository import MarketplacesLinksRepository
from app.services.marketplace_service import MarketplaceParseError, MarketplaceService
from app.utils.jwt import get_current_user

router = APIRouter(prefix="", tags=["marketplaces"])
repo = MarketplacesLinksRepository()
marketplace_service = MarketplaceService(ImageRepository())


class MarketplaceParseRequest(BaseModel):
    url: str


@router.get("/marketplaces")
def get_marketplaces():
    return repo.get_all()


@router.get("/marketplace/{slug}")
def get_marketplace(slug: str):
    marketplace = repo.get_by_slug(slug)
    if marketplace is None:
        raise HTTPException(status_code=404, detail="Marketplace not found")
    return marketplace


@router.post("/marketplace/parse")
def parse_marketplace_product(
    data: MarketplaceParseRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        return marketplace_service.parse_product(data.url)
    except MarketplaceParseError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
