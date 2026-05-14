from dataclasses import dataclass


@dataclass
class Event:
    owner_id: int
    title: str

    id: int | None = None
    description: str | None = None
    event_date: str | None = None
    place: str | None = None
    public_token: str | None = None


@dataclass
class EventCreateRequest:
    title: str
    
    description: str | None = None
    event_date: str | None = None
    place: str | None = None