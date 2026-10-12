import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app.config import UPLOAD_DIR
from app.models.image import Image, ImageResponse
from app.models.user import User
from app.repositories.image_repository import ImageRepository
from app.utils.images import (
    ImageTooLargeError,
    ImageValidationError,
    MAX_IMAGE_SIZE,
    validate_image_bytes,
)
from app.utils.jwt import get_current_user

router = APIRouter(tags=["Images"])
image_repository = ImageRepository()

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _with_image_url(image: Image, request: Request) -> ImageResponse:
    return ImageResponse(
        id=image.id,
        image_type=image.image_type,
        hash=image.hash,
        image_url=str(request.url_for("get_image", image_id=image.id)),
    )


@router.post("/images", response_model=ImageResponse)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    image_bytes = await file.read(MAX_IMAGE_SIZE + 1)
    try:
        validated_image = validate_image_bytes(image_bytes, file.content_type)
    except ImageTooLargeError as error:
        raise HTTPException(status_code=413, detail=str(error)) from error
    except ImageValidationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    image_hash = hashlib.sha256(image_bytes).hexdigest()

    existing_image = image_repository.get_image_by_hash(image_hash)
    if existing_image:
        return _with_image_url(existing_image, request)

    filename = f"{uuid4().hex}{validated_image.extension}"
    file_path = UPLOAD_DIR / filename

    with file_path.open("wb") as buffer:
        buffer.write(image_bytes)

    image = Image(
        image_path=str(file_path),
        image_type=validated_image.media_type,
        hash=image_hash,
        owner_id=current_user.id,
    )

    try:
        stored_image = image_repository.create_image(image)
    except ValueError:
        # Another request may have inserted the same hash after our lookup.
        file_path.unlink(missing_ok=True)
        stored_image = image_repository.get_image_by_hash(image_hash)
        if stored_image is None:
            raise HTTPException(status_code=409, detail="Image already exists")

    return _with_image_url(stored_image, request)


@router.get("/images/{image_id}")
def get_image(image_id: int):
    image = image_repository.get_image_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(path=image.image_path, media_type=image.image_type)


@router.delete("/images/{image_id}")
def delete_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
):
    image = image_repository.get_image_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    if image.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the image uploader can delete it")

    image_path = Path(image.image_path)
    deleted = image_repository.delete_image(image_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Image not found")

    if image_path.exists():
        image_path.unlink()

    return {"message": "Image deleted"}
