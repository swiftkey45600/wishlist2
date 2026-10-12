from dataclasses import dataclass, field
from typing import Annotated, Literal, Optional
from pydantic import BaseModel, Field, model_validator
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


class GiftFilters(BaseModel):
    min_price: int | None = Field(default=None, ge=0)
    max_price: int | None = Field(default=None, ge=0)
    tags: list[Annotated[int, Field(gt=0)]] = Field(default_factory=list)
    q: str | None = None
    status: Literal["available", "reserved", "bought"] | None = None
    sort_by: Literal["id", "price", "title"] = "id"
    sort_order: Literal["asc", "desc"] = "asc"

    @model_validator(mode="after")
    def validate_price_range(self):
        if self.min_price is not None and self.max_price is not None and self.min_price > self.max_price:
            raise ValueError("min_price must not exceed max_price")
        return self
