from app.repositories.contribution_repository import ContributionRepository
from app.repositories.gift_repository import GiftRepository
from app.repositories.image_repository import ImageRepository
from app.repositories.marketplace_links_repository import MarketplacesLinksRepository
from app.repositories.event_repository import EventRepository
from app.repositories.reservation_repository import ReservationRepository
from app.services.gift_service import GiftService
from app.services.reservation_service import ReservationService


class GiftsManager(GiftService):
    
    def __init__(
        self,
        gift_repo: GiftRepository,
        image_repo: ImageRepository,
        marketplace_links_repo: MarketplacesLinksRepository | None = None,
        contribution_repo: ContributionRepository | None = None,
    ):
        event_repo = EventRepository()
        super().__init__(
            gift_repository=gift_repo,
            image_repository=image_repo,
            marketplace_links_repository=marketplace_links_repo or MarketplacesLinksRepository(),
            contribution_repository=contribution_repo or ContributionRepository(),
            event_repository=event_repo,
            reservation_service=ReservationService(ReservationRepository(), gift_repo, event_repo),
        )
