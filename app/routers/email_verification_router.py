from html import escape
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from app.models.user import EmailVerificationConfirmRequest, User
from app.services.email_verification_service import EmailVerificationService, VERIFICATION_LIFETIME_SECONDS
from app.utils.jwt import get_current_user
from app.utils.email_pages import email_page


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
    return email_page(
        "Подтверждение почты",
        "Остался один шаг: подтвердите адрес электронной почты для вашего аккаунта Wishlist.",
        f'<form method="post" action="{escape(action, quote=True)}">'
        f'<input type="hidden" name="token" value="{escape(token, quote=True)}">'
        '<button type="submit">Подтвердить почту</button></form>'
        '<p class="hint">Ссылка действует 30 минут. Если вы не запрашивали подтверждение, просто закройте страницу.</p>',
    )


@router.post("/link", response_class=HTMLResponse, include_in_schema=False)
def confirm_from_email(token: Annotated[str, Form(min_length=43, max_length=43)]):
    try:
        service.confirm(token)
    except HTTPException as error:
        if error.status_code != 400:
            raise
        return email_page(
            "Ссылка больше не действует",
            "Она уже использована или срок её действия истёк. Если почта ещё не подтверждена, запросите новое письмо в профиле.",
            state="error", status_code=400,
        )
    return email_page(
        "Почта подтверждена",
        "Всё готово! Адрес электронной почты подтверждён.",
        '<p class="hint">Можно вернуться в профиль Wishlist. Эту вкладку можно закрыть.</p>',
        state="success",
    )
