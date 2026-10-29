from dataclasses import dataclass
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

EventStatus = Literal["active", "archived"]


@dataclass
class Event:
    owner_id: int
    title: str

    id: int | None = None
    description: str | None = None
    event_date: str | None = None
    end_date: str | None = None
    place: str | None = None
    public_token: str | None = None
    status: EventStatus = "active"
    cover_image_id: int | None = None


class EventCopyRequest(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    event_date: str | None = None

    @field_validator("event_date")
    @classmethod
    def validate_event_date(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            return datetime.fromisoformat(value).isoformat()


class EventCreateRequest(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    
    description: str | None = None
    event_date: str | None = None
    end_date: str | None = None
    place: str | None = None
    cover_image_id: int | None = Field(default=None, gt=0, le=9223372036854775807)


class EventUpdateRequest(BaseModel):
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)] | None = None
    description: str | None = None
    event_date: str | None = None
    end_date: str | None = None
    place: str | None = None
    cover_image_id: int | None = Field(default=None, gt=0, le=9223372036854775807)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("Title cannot be null")
        return value
