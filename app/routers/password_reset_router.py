from html import escape
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse

from app.models.user import PasswordResetConfirmRequest, UserEmailRequest
from app.services.password_reset_service import PasswordResetService, RESET_REQUEST_MESSAGE
from app.utils.email_pages import PAGE_HEADERS


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


@router.get("/link", response_class=HTMLResponse, include_in_schema=False)
def password_reset_page(request: Request, token: Annotated[str, Query(min_length=43, max_length=43)]):
    # A GET from a mail preview/scanner never modifies credentials or consumes a token.
    action = request.scope.get("root_path", "").rstrip("/") + "/auth/password-reset/link"
    return HTMLResponse(
        '<!doctype html><html lang="ru"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Новый пароль — Wishlist</title><h1>Новый пароль</h1>'
        '<p>Задайте новый пароль. После сохранения потребуется войти заново на всех устройствах.</p>'
        f'<form method="post" action="{escape(action, quote=True)}">'
        f'<input type="hidden" name="token" value="{escape(token, quote=True)}">'
        '<p><label>Новый пароль <input name="new_password" type="password" autocomplete="new-password" '
        'minlength="8" maxlength="72" required></label></p>'
        '<p><label>Повторите пароль <input name="new_password_repeat" type="password" autocomplete="new-password" '
        'minlength="8" maxlength="72" required></label></p>'
        '<button type="submit">Сохранить пароль</button></form></html>', headers=PAGE_HEADERS,
    )


@router.post("/link", response_class=HTMLResponse, include_in_schema=False)
def reset_from_email(
    token: Annotated[str, Form(min_length=43, max_length=43)],
    new_password: Annotated[str, Form()],
    new_password_repeat: Annotated[str, Form()],
):
    if new_password != new_password_repeat:
        return HTMLResponse(
            '<!doctype html><html lang="ru"><meta charset="utf-8"><title>Ошибка — Wishlist</title>'
            '<h1>Пароли не совпадают</h1><p>Вернитесь к форме и повторите ввод.</p></html>',
            status_code=422, headers=PAGE_HEADERS,
        )
    try:
        service.confirm(token, new_password)
    except HTTPException as error:
        detail = "Ссылка недействительна, просрочена или уже использована." if error.status_code == 400 else str(error.detail)
        return HTMLResponse(
            '<!doctype html><html lang="ru"><meta charset="utf-8"><title>Ошибка — Wishlist</title>'
            f'<h1>Не удалось сменить пароль</h1><p>{escape(detail)}</p></html>',
            status_code=error.status_code, headers=PAGE_HEADERS,
        )
    return HTMLResponse(
        '<!doctype html><html lang="ru"><meta charset="utf-8"><title>Пароль изменён — Wishlist</title>'
        '<h1>Пароль изменён</h1><p>Вернитесь на сайт и войдите с новым паролем.</p></html>', headers=PAGE_HEADERS,
    )
