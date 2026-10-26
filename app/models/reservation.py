from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

@dataclass
class Reservation:
    gift_id: int
    is_anonymous: bool
    id: int | None = None
    reserver_name: str | None = None
    reserver_id: int | None = None

@dataclass
class ReservationCreateRequest:
    gift_id: int
    is_anonymous: bool
    reserver_name: str | None = None


class PublicGiftReservationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_reserved: bool


class GuestReservationCancelRequest(BaseModel):
    secret_word: SecretStr

    @field_validator("secret_word")
    @classmethod
    def validate_secret_word(cls, value: SecretStr) -> SecretStr:
        word = value.get_secret_value()
        if not word.strip() or len(word.encode("utf-8")) > 72:
            raise ValueError("Secret word must be non-empty and at most 72 UTF-8 bytes")
        return value


class GuestReservationCreateRequest(GuestReservationCancelRequest):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name cannot be empty")
        return value
