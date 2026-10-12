from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict


@dataclass
class Image:
    image_path: str

    id: int | None = None
    image_type: str | None = None
    hash: str | None = None
    image_url: str | None = None
    owner_id: int | None = None


class ImageResponse(BaseModel):
    """Public image representation; the server filesystem path is private."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    image_type: str | None = None
    hash: str | None = None
    image_url: str
