from fastapi import APIRouter, Depends, HTTPException, status
from app.models.identifiers import DatabaseId
from app.models.user import User, UserUpdateRequest
from app.services.user_service import UserService, validate_login
from app.repositories.user_repository import UserRepository
from app.utils.jwt import create_access_token, get_current_user

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
    normalized_login = None
    if user_request.login is not None:
        try:
            normalized_login = validate_login(user_request.login)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        existing_user = user_repository.get_user_by_login(normalized_login)
        if existing_user and existing_user.id != current_user.id:
            raise HTTPException(status_code=409, detail="Login already exists")

    data = user_request.model_dump(exclude_unset=True, mode="json")
    if "login" in data:
        data["login"] = normalized_login
    try:
        updated_user = users_service.update_user(
            current_user.id,
            data,
        )
    except ValueError as error:
        raise HTTPException(status_code=409 if str(error) == "Login already exists" else 400, detail=str(error)) from error
    return {
        "access_token": create_access_token({"sub": updated_user.login, "user_id": updated_user.id}),
        "token_type": "bearer",
        "user": {
            "id": updated_user.id,
            "name": updated_user.name,
            "login": updated_user.login,
            "birthday": updated_user.birthday,
            "gender": updated_user.gender,
        }
    }


@router.get("/{user_id}")
async def get_user(user_id: DatabaseId, current_user: User = Depends(get_current_user)):
    if user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only view your own profile")
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
async def delete_user(user_id: DatabaseId, current_user: User = Depends(get_current_user)):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You can only delete your own account")

    users_service.delete_user(user_id)
    return {"status": "deleted"}

