from dataclasses import dataclass, field
from typing import Annotated, Literal
from pydantic import BaseModel, Field, StringConstraints, model_validator
from app.models.marketplace import Marketplace
from app.models.tag import Tag

@dataclass
class Gift:
    event_id: int
    title: str
    price: int | None
    status: str = "available"
    priority: Literal["high", "normal", "low"] = "normal"
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
    contribution_goal: int | None = None
    share_in_recommendations: bool = False

@dataclass
class GiftCreateRequest(Gift):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    price: Annotated[int, Field(gt=0, le=9223372036854775807)]
    status: Literal["available"] = "available"
    priority: Literal["high", "normal", "low"] = "normal"
    tag_ids: list[int] = field(default_factory=list)
    contribution_goal: Annotated[int, Field(gt=0, le=9223372036854775807)] | None = None


class GiftFilters(BaseModel):
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    tags: list[Annotated[int, Field(gt=0)] | Literal["untagged"]] = Field(default_factory=list)
    q: str | None = None
    status: Literal["available", "reserved", "bought"] | None = None
    sort_by: Literal["id", "price", "title", "priority"] = "id"
    sort_order: Literal["asc", "desc"] = "asc"
    show_reservations: bool = False

    @model_validator(mode="after")
    def validate_price_range(self):
        if self.min_price is not None and self.max_price is not None and self.min_price > self.max_price:
            raise ValueError("min_price must not exceed max_price")
        return self
