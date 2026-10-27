from dataclasses import dataclass

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator


@dataclass
class User:
    name: str
    login: str
    password: str
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
    name: str
    login: str
    password: str
    email: EmailStr | None = None

@dataclass
class UserLoginRequest:
    login: str
    password: str


@dataclass
class UserUpdateRequest:
    name: str | None = None
    login: str | None = None
    password: str | None = None
    birthday: str | None = None
    gender: str | None = None
    email: EmailStr | None = None
