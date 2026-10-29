"""Image URLs are capabilities: knowing a numeric image ID is not access."""
from hashlib import sha256
from hmac import compare_digest, new as hmac_new

from app.config import get_jwt_secret_key
from app.database import get_connection


def image_key(image_id: int, image_hash: str) -> str:
    message = f"image:{image_id}:{image_hash}".encode()
    return hmac_new(get_jwt_secret_key().encode(), message, sha256).hexdigest()


def signed_image_url(image_id: int | None) -> str | None:
    if image_id is None:
        return None
    with get_connection() as conn:
        row = conn.execute("SELECT hash FROM images WHERE id=?", (image_id,)).fetchone()
    if row is None:
        return None
    return f"/images/{image_id}?key={image_key(image_id, row['hash'])}"


def valid_image_key(image, key: str | None) -> bool:
    return bool(key and len(key) == 64 and key.isascii()
                and compare_digest(key, image_key(image.id, image.hash)))


def can_use_image(conn, image_id: int, user_id: int) -> bool:
    # Existing attachments preserve access when migrating older installations.
    return conn.execute("""
        SELECT 1 FROM images WHERE id=? AND (
            owner_id=? OR EXISTS (SELECT 1 FROM image_upload_grants WHERE image_id=images.id AND user_id=?)
            OR EXISTS (SELECT 1 FROM personal_wishes WHERE image_id=images.id AND owner_id=?)
            OR EXISTS (SELECT 1 FROM events WHERE cover_image_id=images.id AND owner_id=?)
            OR EXISTS (SELECT 1 FROM gifts JOIN events ON events.id=gifts.event_id
                       WHERE gifts.image_id=images.id AND events.owner_id=?)
        )
    """, (image_id, user_id, user_id, user_id, user_id, user_id)).fetchone() is not None


def user_can_use_image(image_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        return can_use_image(conn, image_id, user_id)
