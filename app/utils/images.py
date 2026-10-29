"""Shared validation for user and marketplace image downloads."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
import warnings

from PIL import Image as PillowImage
from PIL import UnidentifiedImageError


MAX_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_IMAGE_TYPES = frozenset(
    {"image/jpeg", "image/png", "image/webp", "image/gif"}
)

_FORMAT_TO_MEDIA_TYPE = {
    "JPEG": "image/jpeg",
    # iPhone photos can be JPEG-compatible multi-picture files detected as MPO.
    "MPO": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
    "GIF": "image/gif",
}
_MEDIA_TYPE_TO_EXTENSION = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


class ImageValidationError(ValueError):
    """The bytes are not a supported, fully decodable image."""


class ImageTooLargeError(ImageValidationError):
    """The image exceeds the application size limit."""


@dataclass(frozen=True)
class ValidatedImage:
    """Metadata detected by Pillow after decoding the complete image."""

    media_type: str
    extension: str


def validate_image_bytes(
    image_bytes: bytes,
    declared_content_type: str | None = None,
) -> ValidatedImage:
    """Validate and identify a JPEG, PNG, WebP, or GIF byte stream.

    ``verify`` checks the encoded stream and a second ``load`` pass forces
    Pillow to decode pixel data. The second pass is required because Pillow's
    ``verify`` intentionally does not decode the image.
    """

    if not image_bytes:
        raise ImageValidationError("Изображение пустое")
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise ImageTooLargeError("Размер изображения не должен превышать 5 МБ")

    declared = (
        declared_content_type.split(";", 1)[0].strip().lower()
        if declared_content_type
        else None
    )
    if declared is not None and declared not in ALLOWED_IMAGE_TYPES:
        raise ImageValidationError("Только изображения JPEG, PNG, WebP или GIF")

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", PillowImage.DecompressionBombWarning)
            with PillowImage.open(BytesIO(image_bytes)) as image:
                image.verify()

            # verify() invalidates the image object, so open the stream again.
            with PillowImage.open(BytesIO(image_bytes)) as image:
                image.load()
                media_type = _FORMAT_TO_MEDIA_TYPE.get((image.format or "").upper())
    except (
        PillowImage.DecompressionBombError,
        PillowImage.DecompressionBombWarning,
        OSError,
        SyntaxError,
        ValueError,
        UnidentifiedImageError,
    ) as error:
        raise ImageValidationError("Файл не является корректным изображением") from error

    if media_type is None:
        raise ImageValidationError("Поддерживаются только JPEG, PNG, WebP и GIF")
    if declared is not None and declared != media_type:
        raise ImageValidationError("Тип содержимого не соответствует изображению")

    return ValidatedImage(
        media_type=media_type,
        extension=_MEDIA_TYPE_TO_EXTENSION[media_type],
    )


# Short alias for callers that do not need to emphasize that the input is bytes.
validate_image = validate_image_bytes


__all__ = [
    "ALLOWED_IMAGE_TYPES",
    "ImageTooLargeError",
    "ImageValidationError",
    "MAX_IMAGE_SIZE",
    "ValidatedImage",
    "validate_image",
    "validate_image_bytes",
]
