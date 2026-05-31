from dataclasses import dataclass

@dataclass
class Marketplace:
    slug: str
    name: str
    base_url: str

    id: int | None = None
    logo_url: str | None = None