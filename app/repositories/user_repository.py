from app.models import User


class UserRepository:
    def create_user(self, user: User) -> User:
        raise NotImplementedError

    def get_user_by_id(self, user_id: int) -> User | None:
        raise NotImplementedError

    def get_user_by_login(self, login: str) -> User | None:
        raise NotImplementedError

    def list_users(self) -> list[User]:
        raise NotImplementedError

    def delete_user(self, user_id: int) -> None:
        raise NotImplementedError
