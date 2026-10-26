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
    if not _column_exists(connection, "gifts", "contribution_goal"):
        connection.execute("ALTER TABLE gifts ADD COLUMN contribution_goal INTEGER CHECK (contribution_goal > 0)")
    if not _column_exists(connection, "reservations", "is_fundraising"):
        connection.execute("ALTER TABLE reservations ADD COLUMN is_fundraising INTEGER NOT NULL DEFAULT 0")
    if not _column_exists(connection, "reservations", "secret_word_hash"):
        connection.execute("ALTER TABLE reservations ADD COLUMN secret_word_hash TEXT")
    if not _column_exists(connection, "gifts", "image_id"):
        connection.execute("ALTER TABLE gifts ADD COLUMN image_id INTEGER")
    if not _column_exists(connection, "images", "owner_id"):
        # Existing images intentionally remain ownerless. They must not be
        # assigned to whichever user happens to run the migration.
        connection.execute("ALTER TABLE images ADD COLUMN owner_id INTEGER")
