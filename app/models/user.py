from dataclasses import dataclass, field
from datetime import date
from typing import Annotated

from pydantic import BaseModel, StringConstraints, field_validator

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator


@dataclass
class User:
    name: str
    login: str
    password: str = field(repr=False)
    id: int | None = None
    birthday: str | None = None
    gender: str | None = None
    email: str | None = None
    email_verified: bool = False
    auth_version: int = 0


class UserEmailRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(max_length=254)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.casefold()


class UserEmailResponse(BaseModel):
    email: str | None
    email_verified: bool


class EmailVerificationConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: SecretStr = Field(min_length=43, max_length=43)


class PasswordResetConfirmRequest(EmailVerificationConfirmRequest):
    new_password: SecretStr = Field(min_length=8, max_length=72)

@dataclass
class UserRegisterRequest:
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    login: str
    password: str = field(repr=False)
    email: EmailStr | None = None

@dataclass
class UserLoginRequest:
    login: str
    password: str = field(repr=False)


class UserUpdateRequest(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)] | None = None
    login: str | None = None
    password: str | None = Field(default=None, repr=False)
    birthday: date | None = None
    gender: str | None = None
    email: EmailStr | None = None

    @field_validator("name", "login", "password")
    @classmethod
    def validate_required_fields(cls, value):
        if value is None:
            raise ValueError("Name, login and password cannot be null")
        return value
