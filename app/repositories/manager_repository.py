from app.repositories.gift_repository import GiftRepository
from app.repositories.image_repository import ImageRepository
from app.models.gift import Gift
from app.models.image import Image


class ManagerRepository:
    def __init__(self, gift_repo: GiftRepository, image_repo: ImageRepository):
        self.gift_repo = gift_repo
        self.image_repo = image_repo


    def create_gift(self, gift: Gift):
        return self.gift_repo.create_gift(gift)

    def get_gift_by_id(self, gift_id: int):
        return self.gift_repo.get_gift_by_id(gift_id)

    def get_gifts_by_event(self, event_id: int):
        return self.gift_repo.get_gifts_by_event(event_id)

    def update_gift_status(self, gift_id: int, status: str):
        return self.gift_repo.update_gift_status(gift_id, status)

    def delete_gift(self, gift_id: int):
        return self.gift_repo.delete_gift(gift_id)



    def create_image(self, image: Image):
        return self.image_repo.create_image(image)

    def get_image_by_id(self, image_id: int):
        return self.image_repo.get_image_by_id(image_id)

    def get_image_by_hash(self, image_hash: str):
        return self.image_repo.get_image_by_hash(image_hash)

    def delete_image(self, image_id: int):
        return self.image_repo.delete_image(image_id)