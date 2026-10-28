from app.database import get_connection


class PasswordResetRepository:
    def create_pending(self, email: str, token_hash: str, now: int, lifetime: int) -> bool:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            user = connection.execute(
                "SELECT id, email, auth_version FROM users WHERE email = ? AND email_verified = 1", (email,)
            ).fetchone()
            if user is None:
                return False
            connection.execute("DELETE FROM password_reset_tokens WHERE user_id = ? AND expires_at <= ?", (user["id"], now))
            connection.execute(
                """INSERT INTO password_reset_tokens (user_id, email, auth_version, token_hash, expires_at)
                   VALUES (?, ?, ?, ?, ?)""", (user["id"], user["email"], user["auth_version"], token_hash, now + lifetime)
            )
            return True

    def discard_pending(self, token_hash: str) -> None:
        with get_connection() as connection:
            connection.execute("DELETE FROM password_reset_tokens WHERE token_hash = ? AND activated_at IS NULL", (token_hash,))

    def activate(self, token_hash: str, now: int) -> bool:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            token = connection.execute(
                """SELECT t.* FROM password_reset_tokens t JOIN users u ON u.id = t.user_id
                   WHERE t.token_hash = ? AND t.used_at IS NULL AND t.activated_at IS NULL
                     AND t.expires_at > ? AND u.email = t.email AND u.email_verified = 1
                     AND u.auth_version = t.auth_version
                     AND NOT EXISTS (SELECT 1 FROM password_reset_tokens newer
                       WHERE newer.user_id = t.user_id AND newer.id > t.id AND newer.activated_at IS NOT NULL)""",
                (token_hash, now),
            ).fetchone()
            if token is None:
                return False
            connection.execute(
                "UPDATE password_reset_tokens SET used_at = ? WHERE user_id = ? AND id < ? AND used_at IS NULL",
                (now, token["user_id"], token["id"]),
            )
            connection.execute("UPDATE password_reset_tokens SET activated_at = ? WHERE id = ?", (now, token["id"]))
            return True

    @staticmethod
    def _valid_token(connection, token_hash: str, now: int):
        return connection.execute(
            """SELECT t.* FROM password_reset_tokens t JOIN users u ON u.id = t.user_id
               WHERE t.token_hash = ? AND t.used_at IS NULL AND t.activated_at IS NOT NULL
                 AND t.expires_at > ? AND u.email = t.email AND u.email_verified = 1 AND u.auth_version = t.auth_version""",
            (token_hash, now),
        ).fetchone()

    def is_valid(self, token_hash: str, now: int) -> bool:
        with get_connection() as connection:
            return self._valid_token(connection, token_hash, now) is not None

    def consume(self, token_hash: str, password_hash: str, now: int) -> bool:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            token = self._valid_token(connection, token_hash, now)
            if token is None:
                return False
            connection.execute(
                "UPDATE users SET password_hash = ?, auth_version = auth_version + 1 WHERE id = ?",
                (password_hash, token["user_id"]),
            )
            connection.execute(
                "UPDATE password_reset_tokens SET used_at = ? WHERE user_id = ? AND used_at IS NULL", (now, token["user_id"])
            )
            connection.execute("DELETE FROM email_verification_tokens WHERE user_id = ?", (token["user_id"],))
            return True
