from app.models import User
from app.repositories import UserRepository
from app.models.user import UserRegisterRequest, UserLoginRequest
from app.utils.security import hash_password, verify_password


class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def create_user(self, register_request: UserRegisterRequest) -> User:
        if self.user_repository.get_user_by_login(register_request.login):
            raise ValueError("Login already exists")
        
        return self.user_repository.create_user(register_request)

    def authenticate_user(self, login_request: UserLoginRequest) -> User:
        user = self.user_repository.get_user_by_login(login_request.login)
        if not user:
          raise ValueError("No user with this login")

        if verify_password(login_request.password, user.password):
            return user
        raise ValueError("Invalid password")
    
    def get_user(self, user_id: int) -> User | None:
        return self.user_repository.get_user_by_id(user_id)

    def delete_user(self, user_id: int) -> None:
        self.user_repository.delete_user(user_id)

    def list_users(self) -> list[User]:
        return self.user_repository.list_users()
