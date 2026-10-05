from dataclasses import dataclass, field
from app.models.marketplace import Marketplace
from app.models.tag import Tag

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
    tags: list[Tag] = field(default_factory=list)

@dataclass
class GiftCreateRequest(Gift):
    tag_ids: list[int] = field(default_factory=list)
