from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR.parent / "wishlist.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with get_connection() as connection:
        schema = SCHEMA_PATH.read_text(encoding="utf-8")
        connection.executescript(schema)
        _run_migrations(connection)
        connection.commit()

def _column_exists(connection: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return any(row["name"] == column_name for row in rows)


def _run_migrations(connection: sqlite3.Connection) -> None:
    if not _column_exists(connection, "gifts", "image_id"):
        connection.execute("ALTER TABLE gifts ADD COLUMN image_id INTEGER")