from fastapi import APIRouter, HTTPException, status
from app.models.user import UserRegisterRequest, UserLoginRequest
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.utils.jwt import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

user_repository = UserRepository()
user_service = UserService(user_repository)


@router.post("/login")
async def login(user_request: UserLoginRequest):
    try:
        user = user_service.authenticate_user(user_request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    token = create_access_token(data={
        "sub": user.login,
        "user_id": user.id
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "login": user.login
        }
    }


@router.post("/register")
async def register(user_request: UserRegisterRequest):
    try:
        user = user_service.create_user(user_request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    token = create_access_token(data={
        "sub": user.login,
        "user_id": user.id
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "login": user.login
        }
    }
