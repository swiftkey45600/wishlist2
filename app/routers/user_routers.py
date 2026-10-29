from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import User, UserEmailRequest, UserEmailResponse, UserUpdateRequest
from app.services.user_service import UserConflictError, UserService, validate_login
from app.repositories.user_repository import UserRepository
from app.utils.jwt import create_access_token, get_current_user
from app.models.identifiers import DatabaseId
from app.database import get_connection
from pydantic import BaseModel

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


class ReminderSettings(BaseModel):
    enabled: bool


@router.get("/me/reminders", response_model=ReminderSettings)
def get_reminder_settings(current_user: User = Depends(get_current_user)):
    with get_connection() as connection:
        row = connection.execute("SELECT event_reminders FROM users WHERE id = ?", (current_user.id,)).fetchone()
    return {"enabled": bool(row["event_reminders"])}


@router.put("/me/reminders", response_model=ReminderSettings)
def set_reminder_settings(settings: ReminderSettings, current_user: User = Depends(get_current_user)):
    with get_connection() as connection:
        if settings.enabled:
            row = connection.execute("SELECT email, email_verified FROM users WHERE id = ?", (current_user.id,)).fetchone()
            if not row["email"] or not row["email_verified"]:
                raise HTTPException(status_code=409, detail="A verified email is required")
        connection.execute("UPDATE users SET event_reminders = ? WHERE id = ?", (int(settings.enabled), current_user.id))
    return settings


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

    data = user_request.model_dump(exclude_unset=True, mode="json")
    if "login" in data:
        data["login"] = normalized_login
    try:
        updated_user = users_service.update_user(
            current_user.id,
            data,
        )
    except UserConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409 if str(error) == "Login already exists" else 400, detail=str(error)) from error
    return {
        "access_token": create_access_token({
            "sub": updated_user.login,
            "user_id": updated_user.id,
            "auth_version": updated_user.auth_version,
        }),
        "token_type": "bearer",
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

