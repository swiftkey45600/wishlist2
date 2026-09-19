from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import User, UserUpdateRequest
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


@router.patch("/me")
async def update_my_profile(
    user_request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
):
    if user_request.name is not None and not user_request.name.strip():
        raise HTTPException(status_code=400, detail="Name cannot be empty")
    if user_request.login is not None:
        if not user_request.login.strip():
            raise HTTPException(status_code=400, detail="Login cannot be empty")
        existing_user = user_repository.get_user_by_login(user_request.login.strip())
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=409, detail="Login already exists")

    updated_user = users_service.update_user(
        current_user.id,
        {
            "name": user_request.name.strip() if user_request.name is not None else None,
            "login": user_request.login.strip() if user_request.login is not None else None,
            "birthday": user_request.birthday,
            "gender": user_request.gender,
        },
    )
    return {
        "user": {
            "id": updated_user.id,
            "name": updated_user.name,
            "login": updated_user.login,
            "birthday": updated_user.birthday,
            "gender": updated_user.gender,
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



