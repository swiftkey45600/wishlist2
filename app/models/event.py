from dataclasses import dataclass
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints, field_validator

EventStatus = Literal["active", "archived"]


@dataclass
class Event:
    owner_id: int
    title: str

    id: int | None = None
    description: str | None = None
    event_date: str | None = None
    place: str | None = None
    public_token: str | None = None
    status: EventStatus = "active"


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
