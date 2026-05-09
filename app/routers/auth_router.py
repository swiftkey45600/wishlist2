from fastapi import APIRouter
from app.models.user import UserRegisterRequest
from app.models.user import UserLoginRequest
router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/")
async def authenticate(user_request: UserLoginRequest):
    return {"status": True, "user": user_request}
