from app.models import Contribution
from app.repositories import ContributionRepository


class ContributionService:
    def __init__(self, contribution_repository: ContributionRepository):
        self.contribution_repository = contribution_repository

    def add_contribution(self, gift_id: int, amount: int, contributor_name: str | None = None, is_anonymous: bool = False) -> Contribution:
        raise NotImplementedError

    def get_gift_contributions(self, gift_id: int) -> list[Contribution]:
        return self.contribution_repository.get_contributions_by_gift(gift_id)

    def get_total_collected(self, gift_id: int) -> int:
        return self.contribution_repository.get_total_collected(gift_id)

    def delete_contribution(self, contribution_id: int) -> None:
        self.contribution_repository.delete_contribution(contribution_id)
