import time

from fastapi import HTTPException

from app.repositories.auth_mail_rate_limit_repository import AuthMailRateLimitRepository


def check_mail_rate_limit(email: str, client_ip: str, user_id: int | None = None) -> None:
    retry = AuthMailRateLimitRepository().check(email, client_ip, int(time.time()), user_id)
    if retry is not None:
        raise HTTPException(
            status_code=429, detail="Too many email requests; try again later", headers={"Retry-After": str(retry)}
        )
