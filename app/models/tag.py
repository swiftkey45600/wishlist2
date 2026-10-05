from dataclasses import dataclass

from pydantic import BaseModel, field_validator


@dataclass
class Tag:
    event_id: int
    name: str
    id: int | None = None


class TagRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Tag name cannot be empty")
        return value
