from sqlite3 import IntegrityError

from fastapi import HTTPException

from app.models.tag import Tag
from app.models.user import User
from app.repositories.event_repository import EventRepository
from app.repositories.tag_repository import TagRepository


class TagService:
    def __init__(self, tag_repository: TagRepository, event_repository: EventRepository):
        self.tag_repository = tag_repository
        self.event_repository = event_repository

    def _check_event(self, event_id: int, current_user: User | None = None) -> None:
        event = self.event_repository.get_event_by_id(event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        if current_user is not None and event.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the event owner can edit tags")

    def get_tags_by_event(self, event_id: int) -> list[Tag]:
        self._check_event(event_id)
        return self.tag_repository.get_tags_by_event(event_id)

    def get_tag_by_id(self, event_id: int, tag_id: int) -> Tag:
        self._check_event(event_id)
        tag = self.tag_repository.get_tag_by_id(event_id, tag_id)
        if tag is None:
            raise HTTPException(status_code=404, detail="Tag not found")
        return tag

    def create_tag(self, event_id: int, name: str, current_user: User) -> Tag:
        self._check_event(event_id, current_user)
        try:
            return self.tag_repository.create_tag(Tag(event_id=event_id, name=name))
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Tag name already exists in this event") from exc

    def update_tag(self, event_id: int, tag_id: int, name: str, current_user: User) -> Tag:
        self._check_event(event_id, current_user)
        tag = self.get_tag_by_id(event_id, tag_id)
        tag.name = name
        try:
            return self.tag_repository.update_tag(tag)
        except IntegrityError as exc:
            raise HTTPException(status_code=409, detail="Tag name already exists in this event") from exc

    def delete_tag(self, event_id: int, tag_id: int, current_user: User) -> None:
        self._check_event(event_id, current_user)
        if not self.tag_repository.delete_tag(event_id, tag_id):
            raise HTTPException(status_code=404, detail="Tag not found")
