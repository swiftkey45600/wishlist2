from app.models import User
from app.repositories import UserRepository


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def register_user(self, name: str, login: str, password: str) -> User:
        raise NotImplementedError

    def authenticate_user(self, login: str, password: str) -> User | None:
        raise NotImplementedError

    def get_user(self, user_id: int) -> User | None:
        return self.user_repository.get_user_by_id(user_id)

    def delete_user(self, user_id: int) -> None:
        self.user_repository.delete_user(user_id)
