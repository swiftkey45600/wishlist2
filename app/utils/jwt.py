from datetime import datetime, timedelta, timezone
from hashlib import sha256
from hmac import compare_digest
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import get_jwt_secret_key
from app.repositories.user_repository import UserRepository

_user_repository = UserRepository()

SECRET_KEY = get_jwt_secret_key()
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 90

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def get_optional_user(credentials: HTTPAuthorizationCredentials | None = Depends(optional_security)):
    if credentials is None:
        return None
    return get_current_user(credentials)


def _user_from_payload(payload):
    user_id = payload.get("user_id")
    if (
        not isinstance(user_id, int)
        or isinstance(user_id, bool)
        or not 0 < user_id <= 9223372036854775807
    ):
        return None

    user = _user_repository.get_user_by_id(user_id)
    if user is None:
        return None

    version = payload.get("auth_version", 0)
    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version != user.auth_version
    ):
        return None

    credential_id = payload.get("credential_id")
    if (
        not isinstance(credential_id, str)
        or len(credential_id) != 64
        or not credential_id.isascii()
    ):
        return None

    expected = sha256(user.password.encode("utf-8")).hexdigest()
    if not compare_digest(credential_id, expected):
        return None

    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    user_id = to_encode.get("user_id")
    user = None

    if (
        isinstance(user_id, int)
        and not isinstance(user_id, bool)
        and 0 < user_id <= 9223372036854775807
    ):
        user = _user_repository.get_user_by_id(user_id)
    elif user_id is None and isinstance(to_encode.get("sub"), str):
        user = _user_repository.get_user_by_login(to_encode["sub"])

    if user is not None:
        to_encode.update(
            user_id=user.id,
            credential_id=sha256(user.password.encode("utf-8")).hexdigest(),
        )
        to_encode.setdefault("auth_version", user.auth_version)

    if expires_delta is not None:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    user = _user_from_payload(payload)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user
