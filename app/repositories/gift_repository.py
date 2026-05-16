from app.models import Gift


class GiftRepository:
    def __init__(self):
        self.gifts: List[Gift] = []
        self._next_id = 1

    def create_gift(self, gift: Gift) -> Gift:
        gift.id = self._next_id
        
        self.gifts.append(gift)
        self._next_id += 1

        return gift

    def get_gift_by_id(self, gift_id: int) -> Optional[Gift]:
        for gift in self.gifts:
            if gift.id == gift_id:
                return gift
        return None

    def get_gifts_by_event(self, event_id: int) -> List[Gift]:
        return [gift for gift in self.gifts if gift.event_id == event_id]

    def update_gift_status(self, gift_id: int, status: str) -> Optional[Gift]:
        gift = self.get_gift_by_id(gift_id)
        if gift:
            gift.status = status
        return gift

    def delete_gift(self, gift_id: int) -> bool:
        gift = self.get_gift_by_id(gift_id)
        if gift:
            self.gifts.remove(gift)
            return True
        return False
