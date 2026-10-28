import hashlib
import secrets
import time
from urllib.parse import urlencode

from fastapi import HTTPException

from app.config import SMTPConfigurationError, get_public_api_url, get_smtp_settings
from app.repositories.email_verification_repository import EmailVerificationRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_mail_rate_limit import check_mail_rate_limit
from app.services.email_service import EmailDeliveryError, EmailService


VERIFICATION_LIFETIME_SECONDS = 30 * 60


def verification_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class EmailVerificationService:
    def __init__(self):
        self.repository = EmailVerificationRepository()
        self.mail = EmailService()

    def request(self, user_id: int, client_ip: str = "unknown") -> None:
        # Fail before issuing a token if mail delivery/link configuration is missing.
        try:
            get_smtp_settings()
            api_url = get_public_api_url()
        except SMTPConfigurationError:
            raise HTTPException(status_code=503, detail="Email verification is not configured") from None
        user = UserRepository().get_user_by_id(user_id)
        if user is None or not user.email:
            raise HTTPException(status_code=409, detail="Set an email address before requesting verification")
        if user.email_verified:
            raise HTTPException(status_code=409, detail="Email is already verified")
        check_mail_rate_limit(user.email, client_ip, user_id)
        token = secrets.token_urlsafe(32)
        token_hash = verification_token_hash(token)
        try:
            email = self.repository.create_pending(user_id, token_hash, int(time.time()), VERIFICATION_LIFETIME_SECONDS)
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        link = api_url + "/auth/email/verification/link?" + urlencode({"token": token})
        try:
            self.mail.send(
                email,
                "Wishlist: подтвердите адрес почты",
                "Чтобы подтвердить адрес почты в Wishlist, откройте ссылку и нажмите «Подтвердить»:\n\n"
                + link
                + "\n\nСсылка действует 30 минут и может быть использована один раз."
                "\nЕсли вы не запрашивали подтверждение, не переходите по ссылке.",
            )
        except (EmailDeliveryError, SMTPConfigurationError, ValueError):
            self.repository.discard_pending(token_hash)
            raise HTTPException(status_code=503, detail="Verification email could not be sent; try again later") from None
        if not self.repository.activate(token_hash, int(time.time())):
            self.repository.discard_pending(token_hash)
            raise HTTPException(status_code=409, detail="Email changed or a newer verification link was sent; request a new link")

    def confirm(self, token: str) -> None:
        if not self.repository.consume(verification_token_hash(token), int(time.time())):
            raise HTTPException(status_code=400, detail="Verification link is invalid, expired or already used")
