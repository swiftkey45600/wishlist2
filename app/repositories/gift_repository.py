from app.models.gift import Gift, GiftFilters
from app.models.tag import Tag
from app.database import get_connection
from app.utils.image_access import signed_image_url
from app.repositories.contribution_repository import ContributionRepository

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
            priority=row["priority"] if "priority" in row.keys() else "normal",
            description=row["description"],
            picture_url=row["picture_url"],
            marketplace_url=row["marketplace_url"],
            category_id=row["category_id"],
            image_id=row["image_id"],
            image_url=signed_image_url(row["image_id"]),
            reservation_id=row["reservation_id"] if "reservation_id" in row.keys() else None,
            tags=self._get_gift_tags(connection, row["id"]),
            contribution_goal=row["contribution_goal"],
            received=bool(row["received"]),
            carried_forward=bool(row["carried_forward"]),
            contribution_total=connection.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM contributions WHERE gift_id = ?", (row["id"],)
            ).fetchone()[0],
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
                    priority,
                    description,
                    picture_url,
                    marketplace_url,
                    category_id,
                    image_id,
                    contribution_goal
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    gift.event_id,
                    gift.title,
                    gift.price,
                    gift.status,
                    gift.priority,
                    gift.description,
                    gift.picture_url,
                    gift.marketplace_url,
                    gift.category_id,
                    gift.image_id,
                    gift.contribution_goal,
                ),
            )

            gift.id = cursor.lastrowid
            gift.contribution_total = 0
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
                    gifts.priority,
                    gifts.description,
                    gifts.picture_url,
                    gifts.marketplace_url,
                    gifts.category_id,
                    gifts.image_id,
                    gifts.contribution_goal,
                    gifts.received,
                    gifts.carried_forward,
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
            conditions.append("instr(casefold(gifts.title || ' ' || coalesce(gifts.description, '')), ?) > 0")
            parameters.append(filters.q.strip().casefold())
        if filters.tags:
            tag_ids = list(dict.fromkeys(tag for tag in filters.tags if tag != "untagged"))
            placeholders = ", ".join("?" for _ in tag_ids)
            tag_conditions = []
            if "untagged" in filters.tags:
                tag_conditions.append("NOT EXISTS (SELECT 1 FROM gift_tags WHERE gift_tags.gift_id = gifts.id)")
            if tag_ids:
                tag_conditions.append(
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
            conditions.append("(" + " OR ".join(tag_conditions) + ")")
            parameters.extend(tag_ids)

        sort_columns = {
            "id": "gifts.id",
            "price": "gifts.price",
            "title": "casefold(gifts.title)",
            "priority": "CASE gifts.priority WHEN 'high' THEN 3 WHEN 'normal' THEN 2 WHEN 'low' THEN 1 ELSE 2 END",
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
                    gifts.priority,
                    gifts.description,
                    gifts.picture_url,
                    gifts.marketplace_url,
                    gifts.category_id,
                    gifts.image_id,
                    gifts.contribution_goal,
                    gifts.received,
                    gifts.carried_forward,
                    reservations.id AS reservation_id
                FROM gifts
                LEFT JOIN reservations ON reservations.gift_id = gifts.id
                WHERE {" AND ".join(conditions)}
                ORDER BY {order_by}
                """,
                parameters,
            ).fetchall()

            return [self._row_to_gift(row, connection) for row in rows]

    def set_received(self, gift_id: int, owner_id: int, received: bool) -> Gift | None:
        with get_connection() as connection:
            row = connection.execute("""
                UPDATE gifts SET received = ? WHERE id = ? AND EXISTS (
                    SELECT 1 FROM events WHERE events.id = gifts.event_id AND events.owner_id = ?
                ) RETURNING id
            """, (int(received), gift_id, owner_id)).fetchone()
        return self.get_gift_by_id(gift_id) if row else None

    def carry_to_event(self, gift_id: int, owner_id: int, event_id: int) -> Gift | None:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            source = connection.execute("""
                SELECT gifts.* FROM gifts JOIN events ON events.id = gifts.event_id
                WHERE gifts.id = ? AND events.owner_id = ? AND events.status = 'archived'
                  AND gifts.received = 0 AND gifts.carried_forward = 0
            """, (gift_id, owner_id)).fetchone()
            target = connection.execute("SELECT id FROM events WHERE id = ? AND owner_id = ? AND status = 'active'", (event_id, owner_id)).fetchone()
            if source is None or target is None:
                return None
            new_id = connection.execute("""
                INSERT INTO gifts (event_id, title, price, status, priority, description, picture_url,
                    marketplace_url, category_id, image_id, contribution_goal)
                VALUES (?, ?, ?, 'available', ?, ?, ?, ?, ?, ?, ?)
            """, (event_id, source['title'], source['price'], source['priority'], source['description'],
                  source['picture_url'], source['marketplace_url'], source['category_id'], source['image_id'], source['contribution_goal'])).lastrowid
            for tag in connection.execute("SELECT tags.name FROM tags JOIN gift_tags ON tags.id = gift_tags.tag_id WHERE gift_tags.gift_id = ?", (gift_id,)).fetchall():
                connection.execute("INSERT OR IGNORE INTO tags (event_id, name) VALUES (?, ?)", (event_id, tag['name']))
                tag_id = connection.execute("SELECT id FROM tags WHERE event_id = ? AND name = ?", (event_id, tag['name'])).fetchone()['id']
                connection.execute("INSERT INTO gift_tags (gift_id, tag_id) VALUES (?, ?)", (new_id, tag_id))
            connection.execute("UPDATE gifts SET carried_forward = 1 WHERE id = ?", (gift_id,))
        return self.get_gift_by_id(new_id)

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
            connection.execute("BEGIN IMMEDIATE")
            gift = connection.execute("SELECT contribution_goal, status FROM gifts WHERE id = ?", (gift_id,)).fetchone()
            if gift is None:
                return None
            total = connection.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM contributions WHERE gift_id = ?", (gift_id,)
            ).fetchone()[0]
            goal = data.get("contribution_goal", gift["contribution_goal"])
            if goal is not None and gift["contribution_goal"] is None and gift["status"] != "available":
                raise ValueError("Fundraising can only be enabled for an available gift")
            if total and (goal is None or goal < total):
                raise ValueError("The fundraising goal cannot be removed or reduced below the collected amount")
            if data.get("status") == "available":
                if goal is not None and total >= goal:
                    raise ValueError("A fully funded gift must remain reserved")
                connection.execute("DELETE FROM reservations WHERE gift_id = ?", (gift_id,))
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

            ContributionRepository.sync_goal(connection, gift_id)
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
