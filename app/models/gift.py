from dataclasses import dataclass, field
from typing import Optional
from app.models.marketplace import Marketplace

@dataclass
class Gift:
    event_id: int
    title: str
    price: int
    status: str = "available"
    id: int | None = None
    description: str | None = None
    picture_url: str | None = None
    marketplace_url: str | None = None
    category_id: int | None = None

    image_id: int | None = None

    image_url: str | None = None
    reservation_id: int | None = None
    marketplace_links: list[Marketplace] = field(default_factory=list)
    contribution_total: int = 0

@dataclass
class GiftCreateRequest:
    event_id: int
    title: str
    price: int

    description: Optional[str] = None
    picture_url: Optional[str] = None
    marketplace_url: Optional[str] = None
    category_id: Optional[int] = None

    image_id: Optional[int] = None
