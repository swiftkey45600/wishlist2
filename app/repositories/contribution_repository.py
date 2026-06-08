from app.database import get_connection
from app.models import Contribution


class ContributionRepository:
    def create_contribution(self, contribution: Contribution) -> Contribution:
        raise NotImplementedError

    def get_contributions_by_gift(self, gift_id: int) -> list[Contribution]:
        raise NotImplementedError

    def get_total_collected(self, gift_id: int) -> int:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT COALESCE(SUM(amount), 0) AS total FROM contributions WHERE gift_id = ?",
                (gift_id,),
            ).fetchone()
            return int(row["total"])

    def delete_contribution(self, contribution_id: int) -> None:
        raise NotImplementedError
