from app.database import get_connection
from app.models.tag import Tag


class TagRepository:
    def create_tag(self, tag: Tag) -> Tag:
        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO tags (event_id, name) VALUES (?, ?)",
                (tag.event_id, tag.name),
            )
            tag.id = cursor.lastrowid
        return tag

    def get_tags_by_event(self, event_id: int) -> list[Tag]:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT * FROM tags WHERE event_id = ? ORDER BY id",
                (event_id,),
            ).fetchall()
        return [Tag(**dict(row)) for row in rows]

    def get_tag_by_id(self, event_id: int, tag_id: int) -> Tag | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM tags WHERE event_id = ? AND id = ?",
                (event_id, tag_id),
            ).fetchone()
        return Tag(**dict(row)) if row is not None else None

    def update_tag(self, tag: Tag) -> Tag:
        with get_connection() as connection:
            connection.execute(
                "UPDATE tags SET name = ? WHERE event_id = ? AND id = ?",
                (tag.name, tag.event_id, tag.id),
            )
        return tag

    def delete_tag(self, event_id: int, tag_id: int) -> bool:
        with get_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM tags WHERE event_id = ? AND id = ?",
                (event_id, tag_id),
            )
        return cursor.rowcount > 0
