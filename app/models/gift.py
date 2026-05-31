from dataclasses import dataclass
from typing import Optional


@dataclass
class Gift:
    event_id: int
    title: str
    price: int
    status: str
    id: int | None = None
    description: str | None = None
    picture_url: str | None = None
    marketplace_url: str | None = None
    category_id: int | None = None

@dataclass
class GiftCreateRequest:
    event_id: int
    title: str
    price: int

    description: Optional[str] = None
    picture_url: Optional[str] = None
    marketplace_url: Optional[str] = None
    category_id: Optional[int] = None
