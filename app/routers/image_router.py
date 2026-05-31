import hashlib
from pathlib import Path
from uuid import uuid4
import shutil

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.models.image import Image
from app.repositories.image_repository import ImageRepository

router = APIRouter(tags=["Images"])
image_repository = ImageRepository()

UPLOAD_DIR = Path("uploads/images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@router.post("/images", response_model=Image)
async def upload_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Только изображения")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    image_hash = hashlib.sha256(image_bytes).hexdigest()

    existing_image = image_repository.get_image_by_hash(image_hash)
    if existing_image:
        raise HTTPException(status_code=409, detail="Image already exists")

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

    return image_repository.create_image(image)


@router.get("/images/{image_id}")
def get_image(image_id: int):
    image = image_repository.get_image_by_id(image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(path=image.image_path, media_type=image.image_type)


@router.delete("/images/{image_id}")
def delete_image(image_id: int):
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
