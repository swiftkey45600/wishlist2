import hashlib

from app.database import get_connection


class AuthMailRateLimitRepository:
    def check(self, email: str, client_ip: str, now: int, user_id: int | None = None) -> int | None:
        limits = [
            ("ip-hour", client_ip, 20, 3600),
            ("email-minute", email.casefold(), 1, 60),
            ("email-hour", email.casefold(), 5, 3600),
        ]
        if user_id is not None:
            limits.extend((("user-minute", str(user_id), 1, 60), ("user-hour", str(user_id), 5, 3600)))
        entries = [
            (hashlib.sha256(f"{scope}:{value}".encode()).hexdigest(), limit, window)
            for scope, value, limit, window in limits
        ]
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM auth_mail_rate_limits WHERE expires_at <= ?", (now,))
            retry_after = 0
            for key, limit, window in entries:
                row = connection.execute("SELECT attempts, expires_at FROM auth_mail_rate_limits WHERE key = ?", (key,)).fetchone()
                if row is not None and row["attempts"] >= limit:
                    retry_after = max(retry_after, row["expires_at"] - now)
            if retry_after:
                return retry_after
            for key, limit, window in entries:
                connection.execute(
                    """INSERT INTO auth_mail_rate_limits (key, attempts, expires_at) VALUES (?, 1, ?)
                       ON CONFLICT(key) DO UPDATE SET attempts = attempts + 1""", (key, now + window)
                )
        return None
