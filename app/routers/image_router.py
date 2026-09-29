import hashlib
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app.models.image import Image
from app.models.user import User
from app.repositories.image_repository import ImageRepository
from app.utils.jwt import get_current_user

router = APIRouter(tags=["Images"])
image_repository = ImageRepository()

UPLOAD_DIR = Path("uploads/images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_SIZE = 5 * 1024 * 1024


def _with_image_url(image: Image, request: Request) -> Image:
    image.image_url = str(request.url_for("get_image", image_id=image.id))
    return image


@router.post("/images", response_model=Image)
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Только изображения")

    image_bytes = await file.read(MAX_IMAGE_SIZE + 1)
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(image_bytes) > MAX_IMAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Размер изображения не должен превышать 5 МБ",
        )

    image_hash = hashlib.sha256(image_bytes).hexdigest()

    existing_image = image_repository.get_image_by_hash(image_hash)
    if existing_image:
        return _with_image_url(existing_image, request)

    ext = Path(file.filename).suffix or ".jpg"
    filename = f"{uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / filename

    with file_path.open("wb") as buffer:
        buffer.write(image_bytes)

    image = Image(
        image_path=str(file_path),
        image_type=file.content_type,
        hash=image_hash
    )

    return _with_image_url(image_repository.create_image(image), request)


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

    image_path = Path(image.image_path)
    deleted = image_repository.delete_image(image_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Image not found")

    if image_path.exists():
        image_path.unlink()

    return {"message": "Image deleted"}
