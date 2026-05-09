from app.models import Contribution


class ContributionRepository:
    def create_contribution(self, contribution: Contribution) -> Contribution:
        raise NotImplementedError

    def get_contributions_by_gift(self, gift_id: int) -> list[Contribution]:
        raise NotImplementedError

    def get_total_collected(self, gift_id: int) -> int:
        raise NotImplementedError

    def delete_contribution(self, contribution_id: int) -> None:
        raise NotImplementedError
