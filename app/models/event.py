from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator


@dataclass
class Event:
    owner_id: int
    title: str

    id: int | None = None
    description: str | None = None
    event_date: str | None = None
    place: str | None = None
    public_token: str | None = None
    cover_image_id: int | None = None


class EventCreateRequest(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    
    description: str | None = None
    event_date: str | None = None
    place: str | None = None
    cover_image_id: int | None = Field(default=None, gt=0, le=9223372036854775807)


class EventUpdateRequest(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None = None
    description: str | None = None
    event_date: str | None = None
    place: str | None = None
    cover_image_id: int | None = Field(default=None, gt=0, le=9223372036854775807)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Title cannot be null")
        return value
