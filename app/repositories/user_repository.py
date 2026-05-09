from app.models import User
from app.models.user import UserRegisterRequest

class UserRepository:
    def __init__(self):
        self.users: list[User] = [User(id=1, name="John Doe", login="johndoe", password_hash="hashedpassword")]
        self._next_id = 2

    def create_user(self, user: UserRegisterRequest) -> User:
        new_user = User(
            id=self._next_id,
            name=user.name,
            login=user.login,
            password_hash=user.password

        )
        self.users.append(new_user)
        self._next_id += 1
        return new_user

    def get_user_by_id(self, user_id: int) -> User | None:
        for user in self.users:
            if user.id == user_id:
                return user
        return None

    def get_user_by_login(self, login: str) -> User | None:
        for user in self.users:
            if user.login == login:
                return user
        return None

    def list_users(self) -> list[User]:
        return self.users.copy()

    def delete_user(self, user_id: int) -> None:
        self.users = [user for user in self.users if user.id != user_id]
