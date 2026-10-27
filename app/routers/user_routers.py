from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import User, UserEmailRequest, UserEmailResponse, UserUpdateRequest
from app.services.user_service import UserConflictError, UserService, validate_login
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
            "gender": current_user.gender,
            "email": current_user.email,
            "email_verified": current_user.email_verified,
        }
    }


@router.get("/me/email", response_model=UserEmailResponse)
def get_my_email(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "email_verified": current_user.email_verified}


@router.post("/me/email", response_model=UserEmailResponse)
def save_my_email(data: UserEmailRequest, current_user: User = Depends(get_current_user)):
    try:
        user = users_service.set_email(current_user.id, str(data.email))
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {"email": user.email, "email_verified": user.email_verified}


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

    try:
        updated_user = users_service.update_user(
            current_user.id,
            {
                "name": user_request.name.strip() if user_request.name is not None else None,
                "login": normalized_login,
                "password": user_request.password,
                "birthday": user_request.birthday,
                "gender": user_request.gender,
                "email": str(user_request.email).casefold() if user_request.email is not None else None,
            },
        )
    except UserConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {
        "user": {
            "id": updated_user.id,
            "name": updated_user.name,
            "login": updated_user.login,
            "birthday": updated_user.birthday,
            "gender": updated_user.gender,
            "email": updated_user.email,
            "email_verified": updated_user.email_verified,
        }
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

