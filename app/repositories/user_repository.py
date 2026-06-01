from app.models import User
from app.models.user import UserRegisterRequest
from app.utils.security import hash_password
from app.database import get_connection


class UserRepository:

    def create_user(self, user: UserRegisterRequest) -> User:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (name, login, password_hash) VALUES (?, ?, ?)",
                (user.name, user.login, hash_password(user.password))
            )
            return User(
                id=cursor.lastrowid,
                name=user.name,
                login=user.login,
                password=hash_password(user.password)
            )

    def get_user_by_id(self, user_id: int) -> User | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            return None
        return User(id=row["id"], name=row["name"], login=row["login"],
                    password=row["password_hash"], birthday=row["birthday"], gender=row["gender"])

    def get_user_by_login(self, login: str | None) -> User | None:
        if not login:
            return None
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE login = ?", (login,)).fetchone()
        if row is None:
            return None
        return User(id=row["id"], name=row["name"], login=row["login"], password=row["password_hash"], birthday=row["birthday"], gender=row["gender"])

    def list_users(self) -> list[User]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM users").fetchall()
        return [User(id=r["id"], name=r["name"], login=r["login"], password=r["password_hash"], birthday=r["birthday"], gender=r["gender"]) for r in rows]

    def delete_user(self, user_id: int) -> None:
        with get_connection() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
