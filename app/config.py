import logging
import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

def env_path(name: str, default: str) -> Path:
    path = Path(os.getenv(name, default)).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


DATABASE_PATH = env_path("DATABASE_PATH", "wishlist.db")
UPLOAD_DIR = env_path("UPLOAD_DIR", "uploads/images")
if UPLOAD_DIR.is_dir() and not os.access(UPLOAD_DIR, os.W_OK):
    # Keep new uploads persistent when a deployed directory is owned by root.
    fallback_dir = DATABASE_PATH.parent / "images"
    logging.getLogger(__name__).warning(
        "Upload directory %s is not writable; using %s", UPLOAD_DIR, fallback_dir
    )
    UPLOAD_DIR = fallback_dir

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
