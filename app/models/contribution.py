from dataclasses import dataclass


@dataclass
class Contribution:
    gift_id: int
    amount: int
    is_anonymous: bool
    id: int | None = None
    contributor_name: str | None = None
