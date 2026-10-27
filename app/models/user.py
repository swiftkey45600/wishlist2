from dataclasses import dataclass
from datetime import date
from typing import Annotated

from pydantic import BaseModel, StringConstraints, field_validator


@dataclass
class User:
    name: str
    login: str
    password: str
    id: int | None = None
    birthday: str | None = None
    gender: str | None = None

@dataclass
class UserRegisterRequest:
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    login: str
    password: str

@dataclass
class UserLoginRequest:
    login: str
    password: str


class UserUpdateRequest(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)] | None = None
    login: str | None = None
    password: str | None = None
    birthday: date | None = None
    gender: str | None = None

    @field_validator("name", "login", "password")
    @classmethod
    def validate_required_fields(cls, value):
        if value is None:
            raise ValueError("Name, login and password cannot be null")
        return value
