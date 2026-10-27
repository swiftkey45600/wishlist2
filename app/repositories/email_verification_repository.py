from app.database import get_connection


class EmailVerificationRepository:
    def create_pending(self, user_id: int, token_hash: str, now: int, lifetime: int) -> str:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            user = connection.execute("SELECT email, email_verified FROM users WHERE id = ?", (user_id,)).fetchone()
            if user is None or not user["email"]:
                raise ValueError("Set an email address before requesting verification")
            if user["email_verified"]:
                raise ValueError("Email is already verified")
            connection.execute(
                "DELETE FROM email_verification_tokens WHERE user_id = ? AND expires_at <= ?", (user_id, now)
            )
            connection.execute(
                "INSERT INTO email_verification_tokens (user_id, email, token_hash, expires_at) VALUES (?, ?, ?, ?)",
                (user_id, user["email"], token_hash, now + lifetime),
            )
            return user["email"]

    def discard_pending(self, token_hash: str) -> None:
        with get_connection() as connection:
            connection.execute(
                "DELETE FROM email_verification_tokens WHERE token_hash = ? AND activated_at IS NULL", (token_hash,)
            )

    def activate(self, token_hash: str, now: int) -> bool:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            token = connection.execute(
                """SELECT t.* FROM email_verification_tokens t JOIN users u ON u.id = t.user_id
                   WHERE t.token_hash = ? AND t.used_at IS NULL AND t.activated_at IS NULL
                     AND t.expires_at > ? AND u.email = t.email AND u.email_verified = 0
                     AND NOT EXISTS (
                         SELECT 1 FROM email_verification_tokens newer
                         WHERE newer.user_id = t.user_id AND newer.id > t.id AND newer.activated_at IS NOT NULL
                     )""", (token_hash, now)
            ).fetchone()
            if token is None:
                return False
            connection.execute(
                "UPDATE email_verification_tokens SET used_at = ? WHERE user_id = ? AND id < ? AND used_at IS NULL",
                (now, token["user_id"], token["id"]),
            )
            connection.execute(
                "UPDATE email_verification_tokens SET activated_at = ? WHERE id = ?", (now, token["id"])
            )
            return True

    def consume(self, token_hash: str, now: int) -> bool:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            token = connection.execute(
                """SELECT t.* FROM email_verification_tokens t JOIN users u ON u.id = t.user_id
                   WHERE t.token_hash = ? AND t.activated_at IS NOT NULL AND t.used_at IS NULL
                     AND t.expires_at > ? AND u.email = t.email AND u.email_verified = 0""",
                (token_hash, now),
            ).fetchone()
            if token is None:
                return False
            connection.execute("UPDATE users SET email_verified = 1 WHERE id = ?", (token["user_id"],))
            connection.execute(
                "UPDATE email_verification_tokens SET used_at = ? WHERE user_id = ? AND used_at IS NULL",
                (now, token["user_id"]),
            )
            return True
