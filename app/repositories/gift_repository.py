from app.models.gift import Gift, GiftFilters
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

    def get_gifts_by_event(self, event_id: int, filters: GiftFilters | None = None) -> list[Gift]:
        filters = filters or GiftFilters()
        conditions = ["gifts.event_id = ?"]
        parameters = [event_id]

        if filters.min_price is not None:
            conditions.append("gifts.price >= ?")
            parameters.append(filters.min_price)
        if filters.max_price is not None:
            conditions.append("gifts.price <= ?")
            parameters.append(filters.max_price)
        if filters.status is not None:
            conditions.append("gifts.status = ?")
            parameters.append(filters.status)
        if filters.q is not None and filters.q.strip():
            conditions.append("instr(casefold(gifts.title), ?) > 0")
            parameters.append(filters.q.strip().casefold())
        if filters.tags:
            tag_ids = list(dict.fromkeys(filters.tags))
            placeholders = ", ".join("?" for _ in tag_ids)
            conditions.append(
                f"""
                EXISTS (
                    SELECT 1
                    FROM gift_tags
                    JOIN tags ON tags.id = gift_tags.tag_id
                    WHERE gift_tags.gift_id = gifts.id
                      AND tags.event_id = gifts.event_id
                      AND gift_tags.tag_id IN ({placeholders})
                )
                """
            )
            parameters.extend(tag_ids)

        sort_columns = {
            "id": "gifts.id",
            "price": "gifts.price",
            "title": "casefold(gifts.title)",
        }
        sort_column = sort_columns[filters.sort_by]
        sort_direction = {"asc": "ASC", "desc": "DESC"}[filters.sort_order]
        order_by = f"{sort_column} {sort_direction}, gifts.id ASC"
        if filters.sort_by == "price":
            order_by = f"gifts.price IS NULL, {order_by}"

        with get_connection() as connection:
            connection.create_function("casefold", 1, lambda value: value.casefold() if value is not None else None)
            rows = connection.execute(
                f"""
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
                WHERE {" AND ".join(conditions)}
                ORDER BY {order_by}
                """,
                parameters,
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
        if not data:
            return self.get_gift_by_id(gift_id)

        set_clause = ", ".join(f"{field} = ?" for field in data)

        with get_connection() as connection:
            connection.execute(
                f"""
                UPDATE gifts
                SET {set_clause}
                WHERE id = ?
                """,
                (*data.values(), gift_id),
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
