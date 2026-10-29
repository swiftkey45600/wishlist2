from sqlite3 import IntegrityError

from app.models import User
from app.repositories import UserRepository
from app.models.user import UserRegisterRequest, UserLoginRequest
from app.utils.security import hash_password, verify_password


class UserConflictError(ValueError):
    pass


MIN_LOGIN_LENGTH = 3
MIN_PASSWORD_LENGTH = 8


def validate_login(login: str) -> str:
    normalized_login = login.strip()
    if len(normalized_login) < MIN_LOGIN_LENGTH:
        raise ValueError(
            f"Логин должен содержать не менее {MIN_LOGIN_LENGTH} символов"
        )
    return normalized_login


def validate_password(password: str) -> None:
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Пароль должен занимать не более 72 байт UTF-8")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(
            f"Пароль должен содержать не менее {MIN_PASSWORD_LENGTH} символов"
        )
    if len(set(password)) == 1:
        raise ValueError(
            "Пароль не может состоять из одного повторяющегося символа"
        )


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, register_request: UserRegisterRequest) -> User:
        register_request.login = validate_login(register_request.login)
        validate_password(register_request.password)

        if self.user_repository.get_user_by_login(register_request.login):
            raise ValueError("Login already exists")
        if register_request.email is not None:
            register_request.email = str(register_request.email).casefold()
        try:
            return self.user_repository.create_user(register_request)
        except IntegrityError as error:
            if error.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE":
                raise UserConflictError("Login or email already in use") from error
            raise

    def authenticate_user(self, login_request: UserLoginRequest) -> User:
        user = self.user_repository.get_user_by_login(login_request.login.strip())
        if not user:
          raise ValueError("No user with this login")

        if verify_password(login_request.password, user.password):
            return user
        raise ValueError("Invalid password")
    
    def get_user(self, user_id: int) -> User | None:
        return self.user_repository.get_user_by_id(user_id)

    def set_email(self, user_id: int, email: str) -> User | None:
        try:
            return self.user_repository.set_email(user_id, email)
        except IntegrityError as error:
            if error.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE":
                raise ValueError("Email already in use") from error
            raise

    def delete_user(self, user_id: int) -> None:
        self.user_repository.delete_user(user_id)

    def update_user(self, user_id: int, data: dict) -> User | None:
        data = data.copy()
        if data.get("password") is not None:
            password = data.pop("password")
            validate_password(password)
            data["password_hash"] = hash_password(password)
        try:
            return self.user_repository.update_user(user_id, data)
        except IntegrityError as error:
            if error.sqlite_errorname == "SQLITE_CONSTRAINT_UNIQUE":
                raise UserConflictError("Login or email already in use") from error
            raise

    def list_users(self) -> list[User]:
        return self.user_repository.list_users()
