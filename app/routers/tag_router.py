from fastapi import APIRouter, Depends

from app.models.tag import Tag, TagRequest
from app.models.user import User
from app.repositories.event_repository import EventRepository
from app.repositories.tag_repository import TagRepository
from app.services.tag_service import TagService
from app.utils.jwt import get_current_user


router = APIRouter(prefix="/events/{event_id}/tags", tags=["Tags"])
tag_service = TagService(TagRepository(), EventRepository())


@router.get("", response_model=list[Tag])
def get_tags_by_event(event_id: int):
    return tag_service.get_tags_by_event(event_id)


@router.get("/{tag_id}", response_model=Tag)
def get_tag(event_id: int, tag_id: int):
    return tag_service.get_tag_by_id(event_id, tag_id)


@router.post("", response_model=Tag)
def create_tag(event_id: int, data: TagRequest, current_user: User = Depends(get_current_user)):
    return tag_service.create_tag(event_id, data.name, current_user)


@router.patch("/{tag_id}", response_model=Tag)
def update_tag(event_id: int, tag_id: int, data: TagRequest, current_user: User = Depends(get_current_user)):
    return tag_service.update_tag(event_id, tag_id, data.name, current_user)


@router.delete("/{tag_id}")
def delete_tag(event_id: int, tag_id: int, current_user: User = Depends(get_current_user)):
    tag_service.delete_tag(event_id, tag_id, current_user)
    return {"message": "Tag deleted"}
