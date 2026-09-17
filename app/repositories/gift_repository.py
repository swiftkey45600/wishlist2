from app.models.gift import Gift
from app.database import get_connection

class GiftRepository:
    def _row_to_gift(self, row) -> Gift:
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
        )

    def create_gift(self, gift: Gift) -> Gift:
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

            connection.commit()
            gift.id = cursor.lastrowid

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

            return self._row_to_gift(row)

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

            return [self._row_to_gift(row) for row in rows]

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
        fields = {k: v for k, v in data.items() if v is not None}
        if not fields:
            return self.get_gift_by_id(gift_id)
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        with get_connection() as connection:
            connection.execute(
                f"UPDATE gifts SET {set_clause} WHERE id = ?",
                (*fields.values(), gift_id),
            )
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
