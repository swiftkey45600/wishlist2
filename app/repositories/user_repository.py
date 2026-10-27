from app.models import User
from app.models.user import UserRegisterRequest
from app.utils.security import hash_password
from app.database import get_connection


class UserRepository:
    @staticmethod
    def _row_to_user(row) -> User:
        return User(
            id=row["id"], name=row["name"], login=row["login"], password=row["password_hash"],
            birthday=row["birthday"], gender=row["gender"], email=row["email"],
            email_verified=bool(row["email_verified"]),
            auth_version=row["auth_version"],
        )

    def create_user(self, user: UserRegisterRequest) -> User:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO users (name, login, password_hash, email) VALUES (?, ?, ?, ?)",
                (user.name, user.login, hash_password(user.password), user.email)
            )
            return User(
                id=cursor.lastrowid,
                name=user.name,
                login=user.login,
                password="",
                email=user.email,
            )

    def get_user_by_id(self, user_id: int) -> User | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_user(row)

    def get_user_by_login(self, login: str | None) -> User | None:
        if not login:
            return None
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE login = ?", (login,)).fetchone()
        if row is None:
            return None
        return self._row_to_user(row)

    def list_users(self) -> list[User]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM users").fetchall()
        return [self._row_to_user(row) for row in rows]

    def set_email(self, user_id: int, email: str) -> User | None:
        return self.update_user(user_id, {"email": email})

    def delete_user(self, user_id: int) -> None:
        with get_connection() as conn:
            conn.execute("DELETE FROM users WHERE id = ?", (user_id,))

    def update_user(self, user_id: int, data: dict) -> User | None:
        fields = data.copy()
        if not fields:
            return self.get_user_by_id(user_id)

        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if user is None:
                return None
            if "email" in fields:
                fields["email"] = str(fields["email"]).casefold()
            changed_email = "email" in fields and fields["email"] != user["email"]
            if changed_email:
                fields["email_verified"] = 0
            if "password_hash" in fields:
                fields["auth_version"] = user["auth_version"] + 1
            set_clause = ", ".join(f"{key} = ?" for key in fields)
            conn.execute(
                f"UPDATE users SET {set_clause} WHERE id = ?",
                (*fields.values(), user_id),
            )
            if changed_email or "password_hash" in fields:
                conn.execute("DELETE FROM email_verification_tokens WHERE user_id = ?", (user_id,))
                conn.execute("DELETE FROM password_reset_tokens WHERE user_id = ?", (user_id,))
            return self._row_to_user(conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())
