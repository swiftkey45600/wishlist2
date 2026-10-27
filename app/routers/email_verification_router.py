from html import escape
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import HTMLResponse

from app.models.user import EmailVerificationConfirmRequest, User
from app.services.email_verification_service import EmailVerificationService, VERIFICATION_LIFETIME_SECONDS
from app.utils.jwt import get_current_user
from app.utils.email_pages import PAGE_HEADERS


router = APIRouter(prefix="/auth/email/verification", tags=["Email verification"])
service = EmailVerificationService()


@router.post("/request", status_code=202)
def request_email_verification(request: Request, current_user: User = Depends(get_current_user)):
    service.request(current_user.id, request.client.host if request.client else "unknown")
    return {"message": "Verification email sent", "expires_in": VERIFICATION_LIFETIME_SECONDS}


@router.post("/confirm")
def confirm_email(data: EmailVerificationConfirmRequest):
    service.confirm(data.token.get_secret_value())
    return {"message": "Email verified"}


@router.get("/link", response_class=HTMLResponse, include_in_schema=False)
def verification_page(request: Request, token: Annotated[str, Query(min_length=43, max_length=43)]):
    # GET never consumes a token: mail preview/link scanners cannot confirm it.
    action = request.scope.get("root_path", "").rstrip("/") + "/auth/email/verification/link"
    return HTMLResponse(
        '<!doctype html><html lang="ru"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Подтверждение почты — Wishlist</title><h1>Подтверждение почты</h1>'
        '<p>Нажмите кнопку, чтобы подтвердить адрес почты для аккаунта Wishlist.</p>'
        f'<form method="post" action="{escape(action, quote=True)}">'
        f'<input type="hidden" name="token" value="{escape(token, quote=True)}">'
        '<button type="submit">Подтвердить</button></form></html>',
        headers=PAGE_HEADERS,
    )


@router.post("/link", response_class=HTMLResponse, include_in_schema=False)
def confirm_from_email(token: Annotated[str, Form(min_length=43, max_length=43)]):
    service.confirm(token)
    return HTMLResponse(
        '<!doctype html><html lang="ru"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Почта подтверждена — Wishlist</title><h1>Почта подтверждена</h1>'
        '<p>Адрес почты подтверждён. Эту страницу можно закрыть.</p></html>',
        headers=PAGE_HEADERS,
    )
