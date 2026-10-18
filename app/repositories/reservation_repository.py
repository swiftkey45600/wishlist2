import time
from sqlite3 import IntegrityError

from app.models.reservation import Reservation
from app.database import get_connection


class ReservationRepository:
    def check_guest_rate_limit(self, client_ip: str, gift_id: int | None = None) -> int | None:
        now = int(time.time())
        limits = [(f"create:ip:{client_ip}", 10)] if gift_id is None else [
            (f"cancel:ip:{client_ip}", 5),
            (f"cancel:gift:{gift_id}", 5),
        ]
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM guest_reservation_rate_limits WHERE expires_at <= ?", (now,))
            retry_after = 0
            for key, limit in limits:
                row = connection.execute(
                    "SELECT attempts, expires_at FROM guest_reservation_rate_limits WHERE key = ?", (key,)
                ).fetchone()
                if row is not None and row["attempts"] >= limit:
                    retry_after = max(retry_after, row["expires_at"] - now)
            if retry_after:
                return retry_after
            for key, _ in limits:
                connection.execute(
                    """
                    INSERT INTO guest_reservation_rate_limits (key, attempts, expires_at)
                    VALUES (?, 1, ?)
                    ON CONFLICT(key) DO UPDATE SET attempts = attempts + 1
                    """,
                    (key, now + 60),
                )
        return None

    def reserve_guest_gift(self, reservation: Reservation, secret_word_hash: str) -> Reservation:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                "UPDATE gifts SET status = 'reserved' WHERE id = ? AND status = 'available'",
                (reservation.gift_id,),
            )
            if not cursor.rowcount:
                raise IntegrityError("Gift is not available for reservation")
            cursor = connection.execute(
                """
                INSERT INTO reservations (gift_id, reserver_name, is_anonymous, secret_word_hash)
                VALUES (?, ?, ?, ?)
                """,
                (reservation.gift_id, reservation.reserver_name, reservation.is_anonymous, secret_word_hash),
            )
            reservation.id = cursor.lastrowid
        return reservation

    def get_secret_word_hash(self, reservation_id: int) -> str | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT secret_word_hash FROM reservations WHERE id = ?", (reservation_id,)
            ).fetchone()
        return row["secret_word_hash"] if row is not None else None

    def unreserve_guest_gift(self, reservation: Reservation, secret_word_hash: str) -> bool:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            cursor = connection.execute(
                "DELETE FROM reservations WHERE id = ? AND secret_word_hash = ? AND reserver_id IS NULL",
                (reservation.id, secret_word_hash),
            )
            if not cursor.rowcount:
                return False
            connection.execute(
                "UPDATE gifts SET status = 'available' WHERE id = ? AND status = 'reserved'",
                (reservation.gift_id,),
            )
        return True

    def _row_to_reservation(self, row) -> Reservation:
        return Reservation(
            id=row["id"],
            gift_id=row["gift_id"],
            reserver_name=row["reserver_name"],
            reserver_id=row["reserver_id"],
            is_anonymous=bool(row["is_anonymous"]),
        )

    def reserve_gift(self, reservation: Reservation) -> Reservation:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            changed = connection.execute(
                "UPDATE gifts SET status = 'reserved' WHERE id = ? AND status = 'available'",
                (reservation.gift_id,),
            )
            if not changed.rowcount:
                raise IntegrityError("Gift is not available for reservation")
            cursor = connection.execute(
                """
                INSERT INTO reservations (
                    gift_id,
                    reserver_name,
                    reserver_id,
                    is_anonymous
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    reservation.gift_id,
                    reservation.reserver_name,
                    reservation.reserver_id,
                    reservation.is_anonymous,
                ),
            )

            connection.commit()
            reservation.id = cursor.lastrowid

            return reservation

    def unreserve_gift(self, gift_id: int) -> bool:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                DELETE FROM reservations
                WHERE gift_id = ?
                """,
                (gift_id,),
            )

            connection.commit()

            return cursor.rowcount > 0

    def get_reservation_by_gift(self, gift_id: int) -> Reservation | None:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT
                    id,
                    gift_id,
                    reserver_name,
                    reserver_id,
                    is_anonymous
                FROM reservations
                WHERE gift_id = ?
                """,
                (gift_id,),
            ).fetchone()

            if row is None:
                return None

            return self._row_to_reservation(row)

    def get_reservation_by_id(self, reservation_id: int) -> Reservation | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT id, gift_id, reserver_name, reserver_id, is_anonymous FROM reservations WHERE id = ?",
                (reservation_id,),
            ).fetchone()
            if row is None:
                return None
            return self._row_to_reservation(row)

    def unreserve_by_id(self, reservation_id: int) -> bool:
        with get_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM reservations WHERE id = ?", (reservation_id,)
            )
            connection.commit()
            return cursor.rowcount > 0
