import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from email_validator import EmailNotValidError, validate_email


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

def env_path(name: str, default: str) -> Path:
    path = Path(os.getenv(name, default)).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


DATABASE_PATH = env_path("DATABASE_PATH", "wishlist.db")
UPLOAD_DIR = env_path("UPLOAD_DIR", "uploads/images")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]


def get_jwt_secret_key() -> str:
    secret = os.getenv("JWT_SECRET_KEY", "").strip()
    if not secret:
        raise RuntimeError("JWT_SECRET_KEY must be set in the environment or .env")
    return secret


class SMTPConfigurationError(RuntimeError):
    """Email delivery is unavailable because SMTP settings are missing or invalid."""


@dataclass(frozen=True)
class SMTPSettings:
    host: str
    port: int
    username: str
    password: str = field(repr=False)
    sender: str
    use_ssl: bool = True
    timeout: int = 10


def get_smtp_settings() -> SMTPSettings:
    # Read lazily: missing SMTP must not prevent login or other API operations.
    values = {name: os.getenv(name, "").strip() for name in (
        "SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "SMTP_FROM",
    )}
    missing = [name for name, value in values.items() if not value]
    if missing:
        raise SMTPConfigurationError("Email delivery is not configured: " + ", ".join(missing))
    if any(character in values["SMTP_HOST"] for character in "\r\n"):
        raise SMTPConfigurationError("Invalid SMTP_HOST")
    try:
        port = int(os.getenv("SMTP_PORT", "465"))
        timeout = int(os.getenv("SMTP_TIMEOUT", "10"))
    except ValueError:
        raise SMTPConfigurationError("SMTP_PORT and SMTP_TIMEOUT must be integers") from None
    if not 1 <= port <= 65535 or not 1 <= timeout <= 60:
        raise SMTPConfigurationError("SMTP_PORT must be 1–65535; SMTP_TIMEOUT must be 1–60 seconds")
    use_ssl = os.getenv("SMTP_USE_SSL", "true").strip().lower()
    if use_ssl not in {"true", "false", "1", "0"}:
        raise SMTPConfigurationError("SMTP_USE_SSL must be true or false")
    try:
        sender = validate_email(values["SMTP_FROM"], check_deliverability=False, allow_smtputf8=False).ascii_email
    except EmailNotValidError:
        raise SMTPConfigurationError("SMTP_FROM must be a valid email address") from None
    return SMTPSettings(
        host=values["SMTP_HOST"], port=port, username=values["SMTP_USERNAME"],
        password=values["SMTP_PASSWORD"], sender=sender, use_ssl=use_ssl in {"true", "1"}, timeout=timeout,
    )


def get_public_api_url() -> str:
    """Trusted link origin; never derive email links from a request Host header."""
    value = os.getenv("PUBLIC_API_URL", "http://127.0.0.1:8000").strip().rstrip("/")
    try:
        parsed = urlsplit(value)
        parsed.port  # Validate the port, if present.
        valid = (
            parsed.scheme in {"http", "https"} and parsed.hostname
            and not parsed.username and not parsed.password
            and not parsed.query and not parsed.fragment
            and not any(char.isspace() or char in '<>"\\' for char in value)
            and (parsed.scheme == "https" or parsed.hostname in {"localhost", "127.0.0.1", "::1"})
        )
    except ValueError:
        valid = False
    if not valid:
        raise SMTPConfigurationError("PUBLIC_API_URL must be an HTTPS API URL (HTTP is allowed only for localhost)")
    return value
