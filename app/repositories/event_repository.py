from app.models import Event
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
        )

    def create_event(self, event: Event) -> Event:
        with get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO events (owner_id, title, description, event_date, place, public_token) VALUES (?, ?, ?, ?, ?, ?)",
                (event.owner_id, event.title, event.description, event.event_date, event.place, event.public_token),
            )
            event.id = cursor.lastrowid
        return event

    def get_event_by_id(self, event_id: int) -> Event | None:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_event(row)

    def get_events_by_user(self, owner_id: int) -> list[Event]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM events WHERE owner_id = ?", (owner_id,)).fetchall()
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

    def delete_event(self, event_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM events WHERE id = ?", (event_id,))
        return cursor.rowcount > 0
