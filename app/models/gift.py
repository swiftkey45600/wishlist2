from dataclasses import dataclass


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
