import secrets

from app.models import Event
from app.models.event import EventStatus
from app.database import get_connection


class EventRepository:
    def _row_to_event(self, row) -> Event:
        return Event(
            id=row["id"],
            owner_id=row["owner_id"],
            title=row["title"],
            description=row["description"],
            event_date=row["event_date"],
            place=row["place"],
            public_token=row["public_token"],
            status=row["status"],
        )

    def create_event(self, event: Event) -> Event:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO events (owner_id, title, description, event_date, place, public_token, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (event.owner_id, event.title, event.description, event.event_date, event.place, event.public_token, event.status),
            )
            event.id = cursor.lastrowid
        return event

    def get_event_by_id(self, event_id: int) -> Event | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_event(row)

    def get_events_by_user(self, owner_id: int, status: EventStatus | None = None) -> list[Event]:
        with get_connection() as conn:
            query = "SELECT * FROM events WHERE owner_id = ?"
            parameters = [owner_id]
            if status is not None:
                query += " AND status = ?"
                parameters.append(status)
            rows = conn.execute(query + " ORDER BY id", parameters).fetchall()
        return [self._row_to_event(row) for row in rows]

    def get_event_by_public_token(self, public_token: str) -> Event | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM events WHERE public_token = ?", (public_token,)).fetchone()
        if row is None:
            return None
        return self._row_to_event(row)

    def list_events(self) -> list[Event]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM events").fetchall()
        return [self._row_to_event(row) for row in rows]

    def set_status(self, event_id: int, owner_id: int, status: EventStatus) -> Event | None:
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "UPDATE events SET status = ? WHERE id = ? AND owner_id = ? RETURNING *",
                (status, event_id, owner_id),
            ).fetchone()
            return self._row_to_event(row) if row is not None else None

    def copy_event(self, event_id: int, owner_id: int, title: str, event_date: str | None) -> Event | None:
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            source = conn.execute(
                "SELECT * FROM events WHERE id = ? AND owner_id = ?", (event_id, owner_id)
            ).fetchone()
            if source is None:
                return None
            cursor = conn.execute(
                """INSERT INTO events (owner_id, title, description, event_date, place, public_token, status)
                   VALUES (?, ?, ?, ?, ?, ?, 'active')""",
                (owner_id, title, source["description"], event_date, source["place"], secrets.token_urlsafe(16)),
            )
            new_id = cursor.lastrowid
            tag_ids = {}
            for tag in conn.execute("SELECT id, name FROM tags WHERE event_id = ? ORDER BY id", (event_id,)).fetchall():
                tag_ids[tag["id"]] = conn.execute(
                    "INSERT INTO tags (event_id, name) VALUES (?, ?)", (new_id, tag["name"])
                ).lastrowid
            for gift in conn.execute("SELECT * FROM gifts WHERE event_id = ? ORDER BY id", (event_id,)).fetchall():
                new_gift_id = conn.execute(
                    """INSERT INTO gifts (
                        event_id, title, price, status, description, picture_url,
                        marketplace_url, category_id, image_id, contribution_goal, share_in_recommendations
                    ) VALUES (?, ?, ?, 'available', ?, ?, ?, ?, ?, ?, 0)""",
                    (new_id, gift["title"], gift["price"], gift["description"], gift["picture_url"],
                     gift["marketplace_url"], gift["category_id"], gift["image_id"], gift["contribution_goal"]),
                ).lastrowid
                links = conn.execute("SELECT tag_id FROM gift_tags WHERE gift_id = ?", (gift["id"],)).fetchall()
                conn.executemany(
                    "INSERT INTO gift_tags (gift_id, tag_id) VALUES (?, ?)",
                    [(new_gift_id, tag_ids[link["tag_id"]]) for link in links if link["tag_id"] in tag_ids],
                )
            return self._row_to_event(conn.execute("SELECT * FROM events WHERE id = ?", (new_id,)).fetchone())

    def delete_event(self, event_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        return cursor.rowcount > 0

    def update_event(self, event_id: int, event: Event) -> Event | None:
        with get_connection() as conn:
            conn.execute(
                """
                UPDATE events
                SET title = ?, description = ?, event_date = ?, place = ?
                WHERE id = ?
                """,
                (event.title, event.description, event.event_date, event.place, event_id),
            )
        return self.get_event_by_id(event_id)
