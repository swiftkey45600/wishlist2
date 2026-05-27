from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.models.image import Image
from app.repositories.image_repository import ImageRepository


router = APIRouter(
    tags=["Images"]
)

image_repository = ImageRepository()


@router.post("/images", response_model=Image)
def create_image(image: Image):
    return image_repository.create_image(image)


@router.get("/images/{image_id}")
def get_image(image_id: int):
    image = image_repository.get_image_by_id(image_id)

    if image is None:
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(
        path=image.image_path,
        media_type=image.image_type,
    )


@router.delete("/images/{image_id}")
def delete_image(image_id: int):
    is_deleted = image_repository.delete_image(image_id)

    if not is_deleted:
        raise HTTPException(status_code=404, detail="Image not found")

    return {"message": "Image deleted"}
