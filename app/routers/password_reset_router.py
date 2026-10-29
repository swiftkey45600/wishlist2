from html import escape
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from app.models.user import PasswordResetConfirmRequest, UserEmailRequest
from app.services.password_reset_service import PasswordResetService, RESET_REQUEST_MESSAGE
from app.utils.email_pages import email_page


router = APIRouter(prefix="/auth/password-reset", tags=["Password recovery"])
service = PasswordResetService()


@router.post("/request", status_code=202)
def request_password_reset(data: UserEmailRequest, request: Request, background_tasks: BackgroundTasks):
    email = str(data.email)
    service.prepare_request(email, request.client.host if request.client else "unknown")
    # Account lookup and SMTP happen after the same response for every address.
    background_tasks.add_task(service.send_reset_email, email)
    return {"message": RESET_REQUEST_MESSAGE}


@router.post("/confirm")
def confirm_password_reset(data: PasswordResetConfirmRequest):
    service.confirm(data.token.get_secret_value(), data.new_password.get_secret_value())
    return {"message": "Password changed. Sign in again with your new password."}


def _reset_form(request: Request, token: str, error: str = "", status_code: int = 200):
    action = request.scope.get("root_path", "").rstrip("/") + "/auth/password-reset/link"
    error_markup = f'<p class="form-error" role="alert">{escape(error)}</p>' if error else ""
    return email_page(
        "Новый пароль",
        "Задайте новый пароль для Wishlist. После сохранения потребуется войти заново на всех устройствах.",
        f'<form method="post" action="{escape(action, quote=True)}">'
        f'<input type="hidden" name="token" value="{escape(token, quote=True)}">'
        + error_markup
        + '<label>Новый пароль<input name="new_password" type="password" autocomplete="new-password" '
        'placeholder="Не менее 8 символов" minlength="8" maxlength="72" required></label>'
        '<label>Повторите пароль<input name="new_password_repeat" type="password" autocomplete="new-password" '
        'placeholder="Введите пароль ещё раз" minlength="8" maxlength="72" required></label>'
        '<button type="submit">Сохранить пароль</button></form>'
        '<p class="hint">Ссылка действует 30 минут и может быть использована один раз.</p>',
        icon="lock", status_code=status_code,
    )


@router.get("/link", response_class=HTMLResponse, include_in_schema=False)
def password_reset_page(request: Request, token: Annotated[str, Query(min_length=43, max_length=43)]):
    # A GET from a mail preview/scanner never modifies credentials or consumes a token.
    return _reset_form(request, token)


@router.post("/link", response_class=HTMLResponse, include_in_schema=False)
def reset_from_email(
    request: Request,
    token: Annotated[str, Form(min_length=43, max_length=43)],
    new_password: Annotated[str, Form()],
    new_password_repeat: Annotated[str, Form()],
):
    if new_password != new_password_repeat:
        return _reset_form(request, token, "Пароли не совпадают. Повторите ввод.", 422)
    try:
        service.confirm(token, new_password)
    except HTTPException as error:
        if error.status_code == 422:
            return _reset_form(request, token, str(error.detail), 422)
        if error.status_code != 400:
            raise
        return email_page(
            "Ссылка больше не действует",
            "Она уже использована или срок её действия истёк. Запросите новую ссылку на странице входа в Wishlist.",
            state="error", status_code=400,
        )
    return email_page(
        "Пароль изменён",
        "Всё готово! Вернитесь в Wishlist и войдите с новым паролем.",
        '<p class="hint">Старые сеансы завершены. Эту вкладку можно закрыть.</p>',
        state="success",
    )
