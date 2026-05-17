from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import User
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from app.utils.jwt import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

user_repository = UserRepository()
users_service = UserService(user_repository)


@router.get("/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "login": current_user.login,
            "birthday": current_user.birthday,
            "gender": current_user.gender
        }
    }


@router.get("/")
async def get_users(current_user: User = Depends(get_current_user)):
    users = users_service.list_users()
    return {
        "users": [
            {
                "id": u.id,
                "name": u.name,
                "login": u.login,
                "birthday": u.birthday,
                "gender": u.gender
            }
            for u in users
        ]
    }


@router.get("/{user_id}")
async def get_user(user_id: int, current_user: User = Depends(get_current_user)):
    user = users_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user": {
            "id": user.id,
            "name": user.name,
            "login": user.login,
            "birthday": user.birthday,
            "gender": user.gender
        }
    }


@router.delete("/{user_id}")
async def delete_user(user_id: int, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You can only delete your own account")

    users_service.delete_user(user_id)
    return {"status": "deleted"}




