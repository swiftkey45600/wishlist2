from app.models import User
from app.repositories import UserRepository
from app.models.user import UserRegisterRequest, UserLoginRequest


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, user_request: UserRegisterRequest) -> User:
        return self.user_repository.create_user(user_request)

    def authenticate_user(self, login: str, password: str) -> User | None:
        raise NotImplementedError

    def get_user(self, user_id: int) -> User | None:
        return self.user_repository.get_user_by_id(user_id)

    def delete_user(self, user_id: int) -> None:
        self.user_repository.delete_user(user_id)

    def list_users(self) -> list[User]:
        return self.user_repository.list_users()
