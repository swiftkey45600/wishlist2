from dataclasses import dataclass


@dataclass
class User:
    name: str
    login: str
    password_hash: str
    id: int | None = None
    birthday: str | None = None
    gender: str | None = None

@dataclass
class UserRegisterRequest:
    name: str
    login: str
    password: str

@dataclass
class UserLoginRequest:
    login: str
    
    password: str
