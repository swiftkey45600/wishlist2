from app.models.gift import Gift
from app.models.tag import Tag
from app.database import get_connection

class GiftRepository:
    def _get_gift_tags(self, connection, gift_id: int) -> list[Tag]:
        rows = connection.execute(
            """
            SELECT tags.*
            FROM tags
            JOIN gift_tags ON gift_tags.tag_id = tags.id
            WHERE gift_tags.gift_id = ?
            ORDER BY tags.id
            """,
            (gift_id,),
        ).fetchall()
        return [Tag(**dict(row)) for row in rows]

    def _replace_gift_tags(self, connection, gift_id: int, tag_ids: list[int]) -> None:
        connection.execute("DELETE FROM gift_tags WHERE gift_id = ?", (gift_id,))
        connection.executemany(
            "INSERT INTO gift_tags (gift_id, tag_id) VALUES (?, ?)",
            [(gift_id, tag_id) for tag_id in dict.fromkeys(tag_ids)],
        )

    def _row_to_gift(self, row, connection) -> Gift:
        return Gift(
            id=row["id"],
            event_id=row["event_id"],
            title=row["title"],
            price=row["price"],
            status=row["status"],
            description=row["description"],
            picture_url=row["picture_url"],
            marketplace_url=row["marketplace_url"],
            category_id=row["category_id"],
            image_id=row["image_id"],
            reservation_id=row["reservation_id"] if "reservation_id" in row.keys() else None,
            tags=self._get_gift_tags(connection, row["id"]),
        )

    def create_gift(self, gift: Gift, tag_ids: list[int] | None = None) -> Gift:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO gifts (
                    event_id,
                    title,
                    price,
                    status,
                    description,
                    picture_url,
                    marketplace_url,
                    category_id,
                    image_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    gift.event_id,
                    gift.title,
                    gift.price,
                    gift.status,
                    gift.description,
                    gift.picture_url,
                    gift.marketplace_url,
                    gift.category_id,
                    gift.image_id,
                ),
            )

            gift.id = cursor.lastrowid
            self._replace_gift_tags(connection, gift.id, tag_ids or [])
            gift.tags = self._get_gift_tags(connection, gift.id)
            connection.commit()

            return gift

    def get_gift_by_id(self, gift_id: int) -> Gift | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    gifts.id,
                    gifts.event_id,
                    gifts.title,
                    gifts.price,
                    gifts.status,
                    gifts.description,
                    gifts.picture_url,
                    gifts.marketplace_url,
                    gifts.category_id,
                    gifts.image_id,
                    reservations.id AS reservation_id
                FROM gifts
                LEFT JOIN reservations ON reservations.gift_id = gifts.id
                WHERE gifts.id = ?
                """,
                (gift_id,),
            ).fetchone()

            if row is None:
                return None

            return self._row_to_gift(row, connection)

    def get_gifts_by_event(self, event_id: int) -> list[Gift]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    gifts.id,
                    gifts.event_id,
                    gifts.title,
                    gifts.price,
                    gifts.status,
                    gifts.description,
                    gifts.picture_url,
                    gifts.marketplace_url,
                    gifts.category_id,
                    gifts.image_id,
                    reservations.id AS reservation_id
                FROM gifts
                LEFT JOIN reservations ON reservations.gift_id = gifts.id
                WHERE gifts.event_id = ?
                """,
                (event_id,),
            ).fetchall()

            return [self._row_to_gift(row, connection) for row in rows]

    def update_gift_status(self, gift_id: int, status: str) -> Gift | None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE gifts
                SET status = ?
                WHERE id = ?
                """,
                (status, gift_id),
            )

            connection.commit()

        return self.get_gift_by_id(gift_id)

    def update_gift(self, gift_id: int, data: dict) -> Gift | None:
        if not data:
            return self.get_gift_by_id(gift_id)

        data = data.copy()
        tag_ids = data.pop("tag_ids", None)

        with get_connection() as connection:
            if data:
                set_clause = ", ".join(f"{field} = ?" for field in data)
                connection.execute(
                    f"""
                    UPDATE gifts
                    SET {set_clause}
                    WHERE id = ?
                    """,
                    (*data.values(), gift_id),
                )

            if tag_ids is not None:
                self._replace_gift_tags(connection, gift_id, tag_ids)

            connection.commit()

        return self.get_gift_by_id(gift_id)

    def delete_gift(self, gift_id: int) -> bool:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                DELETE FROM gifts
                WHERE id = ?
                """,
                (gift_id,),
            )

            connection.commit()

            return cursor.rowcount > 0
