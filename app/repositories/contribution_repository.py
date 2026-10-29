from app.database import get_connection
from app.models.contribution import Contribution


class ContributionRepository:
    @staticmethod
    def sync_goal(connection, gift_id: int) -> None:
        gift = connection.execute("SELECT status, contribution_goal FROM gifts WHERE id = ?", (gift_id,)).fetchone()
        total = connection.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM contributions WHERE gift_id = ?", (gift_id,)
        ).fetchone()[0]
        reservation = connection.execute(
            "SELECT id, is_fundraising FROM reservations WHERE gift_id = ?", (gift_id,)
        ).fetchone()
        funded = gift["contribution_goal"] is not None and total >= gift["contribution_goal"]
        if funded and gift["status"] != "bought":
            if reservation is not None and not reservation["is_fundraising"]:
                raise ValueError("Gift already has an individual reservation")
            if reservation is None:
                connection.execute(
                    "INSERT INTO reservations (gift_id, is_anonymous, is_fundraising) VALUES (?, 1, 1)", (gift_id,)
                )
            connection.execute("UPDATE gifts SET status = 'reserved' WHERE id = ?", (gift_id,))
        elif not funded and reservation is not None and reservation["is_fundraising"]:
            connection.execute("DELETE FROM reservations WHERE id = ?", (reservation["id"],))
            connection.execute("UPDATE gifts SET status = 'available' WHERE id = ? AND status = 'reserved'", (gift_id,))

    def create_contribution(self, contribution: Contribution, secret_word_hash: str | None = None) -> Contribution:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            gift = connection.execute(
                """SELECT gifts.status, gifts.contribution_goal, gifts.received, events.status AS event_status
                   FROM gifts JOIN events ON events.id = gifts.event_id WHERE gifts.id = ?""",
                (contribution.gift_id,)
            ).fetchone()
            if gift is None or gift["contribution_goal"] is None:
                raise ValueError("Fundraising is not enabled for this gift")
            if gift["received"]:
                raise ValueError("Gift is already received")
            if gift["event_status"] == "archived":
                raise ValueError("Event is archived")
            if gift["status"] != "available":
                raise ValueError("Gift is not available for contributions")
            if connection.execute("SELECT 1 FROM reservations WHERE gift_id = ?", (contribution.gift_id,)).fetchone():
                raise ValueError("Gift already has a reservation")
            total = connection.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM contributions WHERE gift_id = ?", (contribution.gift_id,)
            ).fetchone()[0]
            if contribution.amount <= 0 or contribution.amount + total > gift["contribution_goal"]:
                raise ValueError("Contribution exceeds the remaining fundraising goal")
            cursor = connection.execute(
                """
                INSERT INTO contributions (gift_id, amount, contributor_name, contributor_id, secret_word_hash, is_anonymous)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (contribution.gift_id, contribution.amount, contribution.contributor_name,
                 contribution.contributor_id, secret_word_hash, contribution.is_anonymous),
            )
            contribution.id = cursor.lastrowid
            self.sync_goal(connection, contribution.gift_id)
        return contribution

    def get_contributions_by_gift(self, gift_id: int) -> list[Contribution]:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT id, gift_id, amount, contributor_name, contributor_id, is_anonymous FROM contributions WHERE gift_id = ? ORDER BY id",
                (gift_id,),
            ).fetchall()
        return [Contribution(**dict(row)) for row in rows]

    def get_contribution_by_id(self, contribution_id: int) -> Contribution | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT id, gift_id, amount, contributor_name, contributor_id, is_anonymous FROM contributions WHERE id = ?",
                (contribution_id,),
            ).fetchone()
        return Contribution(**dict(row)) if row is not None else None

    def get_secret_word_hash(self, contribution_id: int) -> str | None:
        with get_connection() as connection:
            row = connection.execute("SELECT secret_word_hash FROM contributions WHERE id = ?", (contribution_id,)).fetchone()
        return row["secret_word_hash"] if row is not None else None

    def get_total_collected(self, gift_id: int) -> int:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(amount), 0) AS total FROM contributions WHERE gift_id = ?",
                (gift_id,),
            ).fetchone()
            return int(row["total"])

    def delete_contribution(
        self, contribution_id: int, contributor_id: int | None = None, secret_word_hash: str | None = None
    ) -> bool:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT contributions.gift_id, gifts.status FROM contributions JOIN gifts ON gifts.id = contributions.gift_id WHERE contributions.id = ?",
                (contribution_id,),
            ).fetchone()
            if row is None:
                return False
            if row["status"] == "bought":
                raise ValueError("Contributions to a bought gift cannot be cancelled")
            if contributor_id is not None:
                cursor = connection.execute(
                    "DELETE FROM contributions WHERE id = ? AND contributor_id = ?", (contribution_id, contributor_id)
                )
            elif secret_word_hash is not None:
                cursor = connection.execute(
                    "DELETE FROM contributions WHERE id = ? AND contributor_id IS NULL AND secret_word_hash = ?",
                    (contribution_id, secret_word_hash),
                )
            else:
                return False
            if not cursor.rowcount:
                return False
            self.sync_goal(connection, row["gift_id"])
        return True
