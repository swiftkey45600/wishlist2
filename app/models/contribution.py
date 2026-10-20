from dataclasses import dataclass

from pydantic import BaseModel, Field, SecretStr, StringConstraints, field_validator
from typing import Annotated

from app.models.reservation import GuestReservationCancelRequest


@dataclass
class Contribution:
    gift_id: int
    amount: int
    is_anonymous: bool
    id: int | None = None
    contributor_name: str | None = None
    contributor_id: int | None = None


class ContributionCreateRequest(BaseModel):
    amount: int = Field(gt=0, le=9223372036854775807)
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)] | None = None
    secret_word: SecretStr | None = None
    is_anonymous: bool = False

    @field_validator("secret_word")
    @classmethod
    def validate_secret_word(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None:
            return GuestReservationCancelRequest.validate_secret_word(value)
        return value


class ContributionResponse(BaseModel):
    id: int
    amount: int
    is_anonymous: bool
    contributor_name: str | None
