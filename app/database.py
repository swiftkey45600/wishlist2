from pathlib import Path
import sqlite3

from app.config import DATABASE_PATH

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "schema.sql"


class _Connection(sqlite3.Connection):
    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH, factory=_Connection)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema)

        columns = connection.execute("PRAGMA table_info(reservations)").fetchall()
        if "reserver_id" not in {column["name"] for column in columns}:
            connection.execute("ALTER TABLE reservations ADD COLUMN reserver_id INTEGER")
        _run_migrations(connection)
        connection.commit()

def _column_exists(connection: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row["name"] == column_name for row in rows)


def _run_migrations(connection: sqlite3.Connection) -> None:
    if not _column_exists(connection, "users", "email"):
        connection.execute("ALTER TABLE users ADD COLUMN email TEXT COLLATE NOCASE")
    if not _column_exists(connection, "users", "email_verified"):
        connection.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 0 CHECK (email_verified IN (0, 1))")
    if not _column_exists(connection, "users", "event_reminders"):
        connection.execute("ALTER TABLE users ADD COLUMN event_reminders INTEGER NOT NULL DEFAULT 0 CHECK (event_reminders IN (0, 1))")
    if not _column_exists(connection, "users", "auth_version"):
        connection.execute("ALTER TABLE users ADD COLUMN auth_version INTEGER NOT NULL DEFAULT 0 CHECK (auth_version >= 0)")
    connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique ON users(email COLLATE NOCASE)")
    if not _column_exists(connection, "events", "end_date"):
        connection.execute("ALTER TABLE events ADD COLUMN end_date TEXT")
    if not _column_exists(connection, "personal_wishes", "priority"):
        connection.execute("ALTER TABLE personal_wishes ADD COLUMN priority TEXT NOT NULL DEFAULT 'normal'")
    if not _column_exists(connection, "events", "status"):
        connection.execute(
            "ALTER TABLE events ADD COLUMN status TEXT NOT NULL DEFAULT 'active' "
            "CHECK (status IN ('active', 'archived'))"
        )
    connection.execute("CREATE INDEX IF NOT EXISTS events_owner_status ON events(owner_id, status)")
    if not _column_exists(connection, "events", "cover_image_id"):
        connection.execute(
            "ALTER TABLE events ADD COLUMN cover_image_id INTEGER REFERENCES images(id) ON DELETE SET NULL"
        )
    if not _column_exists(connection, "gifts", "received"):
        connection.execute("ALTER TABLE gifts ADD COLUMN received INTEGER NOT NULL DEFAULT 0 CHECK (received IN (0, 1))")
    if not _column_exists(connection, "gifts", "carried_forward"):
        connection.execute("ALTER TABLE gifts ADD COLUMN carried_forward INTEGER NOT NULL DEFAULT 0 CHECK (carried_forward IN (0, 1))")
    if not _column_exists(connection, "gifts", "contribution_goal"):
        connection.execute("ALTER TABLE gifts ADD COLUMN contribution_goal INTEGER CHECK (contribution_goal > 0)")
    if not _column_exists(connection, "reservations", "is_fundraising"):
        connection.execute("ALTER TABLE reservations ADD COLUMN is_fundraising INTEGER NOT NULL DEFAULT 0")
    if not _column_exists(connection, "gifts", "priority"):
        connection.execute(
            "ALTER TABLE gifts ADD COLUMN priority TEXT NOT NULL DEFAULT 'normal' "
            "CHECK (priority IN ('high', 'normal', 'low'))"
        )
    if not _column_exists(connection, "reservations", "secret_word_hash"):
        connection.execute("ALTER TABLE reservations ADD COLUMN secret_word_hash TEXT")
    if not _column_exists(connection, "gifts", "image_id"):
        connection.execute("ALTER TABLE gifts ADD COLUMN image_id INTEGER")
    if not _column_exists(connection, "images", "owner_id"):
        # Existing images intentionally remain ownerless. They must not be
        # assigned to whichever user happens to run the migration.
        connection.execute("ALTER TABLE images ADD COLUMN owner_id INTEGER")

    if not _column_exists(connection, "event_reminder_deliveries", "days_before"):
        # Preserve the day-before claims when upgrading to two reminder windows.
        connection.execute("ALTER TABLE event_reminder_deliveries RENAME TO event_reminder_deliveries_legacy")
        connection.execute("""
            CREATE TABLE event_reminder_deliveries (
                event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                event_date TEXT NOT NULL,
                days_before INTEGER NOT NULL DEFAULT 1 CHECK (days_before IN (1, 7)),
                PRIMARY KEY (event_id, user_id, event_date, days_before)
            )
        """)
        connection.execute("""
            INSERT INTO event_reminder_deliveries (event_id, user_id, event_date, days_before)
            SELECT event_id, user_id, event_date, 1 FROM event_reminder_deliveries_legacy
        """)
        connection.execute("DROP TABLE event_reminder_deliveries_legacy")
