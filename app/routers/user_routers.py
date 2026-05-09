from fastapi import APIRouter
from app.models.user import UserRegisterRequest
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
router = APIRouter(
    prefix="/users",
    tags=["users"]
)
users_service = UserService(UserRepository())

@router.get("/")
async def get_users():
    return {"users": users_service.list_users()}


@router.get("/{user_id}")
async def get_user(user_id: int):
    user = users_service.get_user(user_id)
    return {"user": user} if user else {"error": "User not found"}

@router.post("/")
async def register(user_request: UserRegisterRequest):
    user = users_service.create_user(user_request)
    return {"status": True, "user": user}




