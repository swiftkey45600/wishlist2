from fastapi import APIRouter, HTTPException
from app.repositories.marketplace_links_repository import MarketplacesLinksRepository

router = APIRouter(prefix="", tags=["marketplaces"])
repo = MarketplacesLinksRepository()


@router.get("/marketplaces")
def get_marketplaces():
    return repo.get_all()


@router.get("/marketplace/{slug}")
def get_marketplace(slug: str):
    marketplace = repo.get_by_slug(slug)
    if marketplace is None:
        raise HTTPException(status_code=404, detail="Marketplace not found")
    return marketplace