from fastapi import HTTPException

from app.models.user import User
from app.repositories.event_repository import EventRepository
from app.repositories.gift_repository import GiftRepository
from app.repositories.gift_question_repository import GiftQuestionRepository
from app.repositories.reservation_repository import ReservationRepository


class GiftQuestionService:
    def __init__(self):
        self.questions = GiftQuestionRepository()
        self.gifts = GiftRepository()
        self.events = EventRepository()

    def _check_public_gift(self, public_token: str, gift_id: int) -> None:
        event = self.events.get_event_by_public_token(public_token)
        gift = self.gifts.get_gift_by_id(gift_id)
        if event is None or gift is None or gift.event_id != event.id:
            raise HTTPException(status_code=404, detail="Gift not found")

    def _check_owner(self, gift_id: int, current_user: User) -> None:
        gift = self.gifts.get_gift_by_id(gift_id)
        if gift is None:
            raise HTTPException(status_code=404, detail="Gift not found")
        event = self.events.get_event_by_id(gift.event_id)
        if event is None or event.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only the event owner can manage questions")

    def get_public_questions(self, public_token: str, gift_id: int):
        self._check_public_gift(public_token, gift_id)
        return self.questions.get_questions(gift_id)

    def create_question(self, public_token: str, gift_id: int, guest_name: str, text: str, client_ip: str):
        self._check_public_gift(public_token, gift_id)
        retry_after = ReservationRepository().check_guest_rate_limit(f"question:{client_ip}")
        if retry_after is not None:
            raise HTTPException(status_code=429, detail="Too many questions", headers={"Retry-After": str(retry_after)})
        return self.questions.create_question(gift_id, guest_name, text)

    def answer_question(self, gift_id: int, question_id: int, answer: str, current_user: User):
        self._check_owner(gift_id, current_user)
        question = self.questions.answer_question(gift_id, question_id, answer)
        if question is None:
            raise HTTPException(status_code=404, detail="Question not found")
        return question
