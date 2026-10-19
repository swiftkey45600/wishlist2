from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, StringConstraints, field_validator


@dataclass
class Event:
    owner_id: int
    title: str

    id: int | None = None
    description: str | None = None
    event_date: str | None = None
    place: str | None = None
    public_token: str | None = None


class EventCreateRequest(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    
    description: str | None = None
    event_date: str | None = None
    place: str | None = None


class EventUpdateRequest(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None = None
    description: str | None = None
    event_date: str | None = None
    place: str | None = None

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Title cannot be null")
        return value
