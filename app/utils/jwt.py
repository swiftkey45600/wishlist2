from datetime import datetime, timedelta, timezone
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
    payload = verify_token(credentials.credentials)
    return _user_from_payload(payload) if payload else None


def _user_from_payload(payload):
    user_id = payload.get("user_id")
    user = None
    if isinstance(user_id, int) and not isinstance(user_id, bool) and 0 < user_id <= 9223372036854775807:
        user = _user_repository.get_user_by_id(user_id)
    # Compatibility with tokens issued before user_id was included.
    elif user_id is None:
        user = _user_repository.get_user_by_login(payload.get("sub"))
    # Legacy tokens without a version remain valid only until the first password change.
    version = payload.get("auth_version", 0)
    if user is None or not isinstance(version, int) or isinstance(version, bool) or version != user.auth_version:
        return None
    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


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
