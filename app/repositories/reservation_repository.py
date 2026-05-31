from app.models.reservation import Reservation
from app.database import get_connection


class ReservationRepository:
    def _row_to_reservation(self, row) -> Reservation:
        return Reservation(
            id=row["id"],
            gift_id=row["gift_id"],
            reserver_name=row["reserver_name"],
            is_anonymous=bool(row["is_anonymous"]),
        )

    def reserve_gift(self, reservation: Reservation) -> Reservation:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO reservations (
                    gift_id,
                    reserver_name,
                    is_anonymous
                )
                VALUES (?, ?, ?)
                """,
                (
                    reservation.gift_id,
                    reservation.reserver_name,
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
                "SELECT id, gift_id, reserver_name, is_anonymous FROM reservations WHERE id = ?",
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