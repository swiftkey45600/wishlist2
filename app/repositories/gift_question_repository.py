from app.database import get_connection
from app.models.gift_question import GiftQuestion


class GiftQuestionRepository:
    def get_questions(self, gift_id: int) -> list[GiftQuestion]:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT * FROM gift_questions WHERE gift_id = ? ORDER BY id", (gift_id,)
            ).fetchall()
        return [GiftQuestion(**dict(row)) for row in rows]

    def create_question(self, gift_id: int, guest_name: str, text: str) -> GiftQuestion:
        with get_connection() as connection:
            cursor = connection.execute(
                "INSERT INTO gift_questions (gift_id, guest_name, text) VALUES (?, ?, ?)",
                (gift_id, guest_name, text),
            )
            row = connection.execute("SELECT * FROM gift_questions WHERE id = ?", (cursor.lastrowid,)).fetchone()
        return GiftQuestion(**dict(row))

    def answer_question(self, gift_id: int, question_id: int, answer: str) -> GiftQuestion | None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE gift_questions SET answer = ?, answered_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                WHERE id = ? AND gift_id = ?
                """,
                (answer, question_id, gift_id),
            )
            row = connection.execute(
                "SELECT * FROM gift_questions WHERE id = ? AND gift_id = ?", (question_id, gift_id)
            ).fetchone()
        return GiftQuestion(**dict(row)) if row is not None else None
