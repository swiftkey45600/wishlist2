"""Copy explicitly selected owned gifts without copying reservations or payments."""
import json
from fastapi import HTTPException
from app.database import get_connection
from app.models.gift_import import GiftImportItem
from app.repositories.event_repository import EventRepository
from app.repositories.gift_repository import GiftRepository
from app.utils.image_access import signed_image_url


def target_event(connection, event_id: int, owner_id: int):
    event = connection.execute("SELECT owner_id,status FROM events WHERE id=?", (event_id,)).fetchone()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    if event["owner_id"] != owner_id:
        raise HTTPException(status_code=404, detail="Event not found")
    if event["status"] != "active":
        raise HTTPException(status_code=409, detail="Cannot add gifts to an archived event")


def source_item(connection, item: GiftImportItem, owner_id: int, target_id: int):
    if item.kind == "wish":
        row = connection.execute("SELECT * FROM personal_wishes WHERE id=? AND owner_id=? AND received=0", (item.id, owner_id)).fetchone()
        tags = json.loads(row["tags_json"]) if row else []
    else:
        row = connection.execute("""
            SELECT gifts.* FROM gifts JOIN events ON events.id=gifts.event_id
            WHERE gifts.id=? AND events.owner_id=? AND gifts.event_id!=?
              AND gifts.received=0 AND gifts.carried_forward=0
        """, (item.id, owner_id, target_id)).fetchone()
        tags = [tag["name"] for tag in connection.execute("""
            SELECT tags.name FROM tags JOIN gift_tags ON gift_tags.tag_id=tags.id WHERE gift_tags.gift_id=?
        """, (item.id,))] if row else []
    if row is None:
        raise HTTPException(status_code=404, detail="Wish or gift not found")
    return row, tags


def imported_gift(connection, event_id: int, item: GiftImportItem):
    # The column is chosen only from a fixed set, never from user SQL.
    column = "source_wish_id" if item.kind == "wish" else "source_gift_id"
    return connection.execute(f"SELECT gift_id FROM event_gift_imports WHERE event_id=? AND {column}=?", (event_id, item.id)).fetchone()


class GiftImportService:
    def get_options(self, event_id: int, owner_id: int) -> list[dict]:
        EventRepository().archive_expired()
        with get_connection() as conn:
            target_event(conn, event_id, owner_id)
            wishes = conn.execute("""
                SELECT id,title,price,description,picture_url,image_id,priority,NULL AS source_title
                FROM personal_wishes WHERE owner_id=? AND received=0
            """, (owner_id,)).fetchall()
            gifts = conn.execute("""
                SELECT gifts.id,gifts.title,gifts.price,gifts.description,gifts.picture_url,gifts.image_id,gifts.priority,
                       events.title AS source_title
                FROM gifts JOIN events ON events.id=gifts.event_id
                WHERE events.owner_id=? AND events.id!=? AND gifts.received=0 AND gifts.carried_forward=0
            """, (owner_id, event_id)).fetchall()
            options = []
            for kind, rows in (("wish", wishes), ("gift", gifts)):
                for row in rows:
                    item = GiftImportItem(kind=kind, id=row["id"])
                    _, tags = source_item(conn, item, owner_id, event_id)
                    options.append({**dict(row), "kind": kind, "tags": tags,
                                    "image_url": signed_image_url(row["image_id"]),
                                    "already_added": imported_gift(conn, event_id, item) is not None})
            return options

    def add(self, event_id: int, owner_id: int, items: list[GiftImportItem]) -> list:
        EventRepository().archive_expired()
        ids = []
        seen = set()
        with get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            target_event(conn, event_id, owner_id)
            for item in items:
                identity = (item.kind, item.id)
                if identity in seen:
                    continue
                seen.add(identity)
                source, tags = source_item(conn, item, owner_id, event_id)
                existing = imported_gift(conn, event_id, item)
                if existing:
                    ids.append(existing["gift_id"])
                    continue
                if source["price"] is None:
                    raise HTTPException(status_code=422, detail="Set a price before adding to an event")
                goal = source["contribution_goal"] if item.kind == "gift" else None
                gift_id = conn.execute("""
                    INSERT INTO gifts (event_id,title,price,description,picture_url,marketplace_url,image_id,priority,contribution_goal)
                    VALUES (?,?,?,?,?,?,?,?,?)
                """, (event_id, source["title"], source["price"], source["description"], source["picture_url"],
                      source["marketplace_url"], source["image_id"], source["priority"], goal)).lastrowid
                for name in tags:
                    conn.execute("INSERT OR IGNORE INTO tags (event_id,name) VALUES (?,?)", (event_id, name))
                    tag_id = conn.execute("SELECT id FROM tags WHERE event_id=? AND name=?", (event_id, name)).fetchone()["id"]
                    conn.execute("INSERT OR IGNORE INTO gift_tags (gift_id,tag_id) VALUES (?,?)", (gift_id, tag_id))
                conn.execute("""
                    INSERT INTO event_gift_imports (gift_id,event_id,source_wish_id,source_gift_id) VALUES (?,?,?,?)
                """, (gift_id, event_id, item.id if item.kind == "wish" else None, item.id if item.kind == "gift" else None))
                ids.append(gift_id)
        repository = GiftRepository()
        return [repository.get_gift_by_id(gift_id) for gift_id in ids]
