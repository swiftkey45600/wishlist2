from dataclasses import dataclass


@dataclass
class Image:
    image_path: str

    id: int | None = None
    image_type: str | None = None
    hash: str | None = None
