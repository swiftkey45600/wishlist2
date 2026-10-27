import hashlib
import logging
import secrets
import time
from urllib.parse import urlencode

from fastapi import HTTPException

from app.config import SMTPConfigurationError, get_public_api_url, get_smtp_settings
from app.repositories.password_reset_repository import PasswordResetRepository
from app.services.auth_mail_rate_limit import check_mail_rate_limit
from app.services.email_service import EmailDeliveryError, EmailService
from app.services.user_service import validate_password
from app.utils.security import hash_password


RESET_LIFETIME_SECONDS = 30 * 60
RESET_REQUEST_MESSAGE = "Request accepted. If password recovery is available for this address, check your email."
logger = logging.getLogger(__name__)


def reset_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class PasswordResetService:
    def __init__(self):
        self.repository = PasswordResetRepository()
        self.mail = EmailService()

    def prepare_request(self, email: str, client_ip: str) -> None:
        # Configuration and limits apply equally to registered and unknown addresses.
        try:
            get_smtp_settings()
            get_public_api_url()
        except SMTPConfigurationError:
            raise HTTPException(status_code=503, detail="Password recovery email is not configured") from None
        check_mail_rate_limit(email, client_ip)

    def send_reset_email(self, email: str) -> None:
        # Executed after the generic HTTP response, without revealing account existence.
        token = secrets.token_urlsafe(32)
        token_hash = reset_token_hash(token)
        if not self.repository.create_pending(email, token_hash, int(time.time()), RESET_LIFETIME_SECONDS):
            return
        try:
            link = get_public_api_url() + "/auth/password-reset/link?" + urlencode({"token": token})
            self.mail.send(
                email, "Wishlist: восстановление пароля",
                "Для смены пароля в Wishlist откройте ссылку:\n\n" + link
                + "\n\nСсылка действует 30 минут и используется один раз."
                "\nЕсли вы не запрашивали смену пароля, проигнорируйте это письмо. Ваш пароль не изменится.",
            )
        except (EmailDeliveryError, SMTPConfigurationError, ValueError):
            self.repository.discard_pending(token_hash)
            # Never log the address, token, password, provider response or email body.
            logger.warning("Password recovery email could not be sent")
            return
        if not self.repository.activate(token_hash, int(time.time())):
            self.repository.discard_pending(token_hash)

    def confirm(self, token: str, new_password: str) -> None:
        try:
            validate_password(new_password)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        token_hash = reset_token_hash(token)
        # Avoid expensive bcrypt hashing for arbitrary invalid/used tokens.
        if not self.repository.is_valid(token_hash, int(time.time())):
            raise HTTPException(status_code=400, detail="Reset link is invalid, expired or already used")
        password_hash = hash_password(new_password)
        if not self.repository.consume(token_hash, password_hash, int(time.time())):
            raise HTTPException(status_code=400, detail="Reset link is invalid, expired or already used")
