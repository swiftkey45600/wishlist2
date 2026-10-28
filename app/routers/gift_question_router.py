from fastapi import APIRouter, Depends, Request

from app.models.identifiers import DatabaseId
from app.models.gift_question import GiftQuestion, GiftQuestionAnswerRequest, GiftQuestionCreateRequest
from app.models.user import User
from app.services.gift_question_service import GiftQuestionService
from app.utils.jwt import get_current_user


router = APIRouter(tags=["gift questions"])
service = GiftQuestionService()


@router.get("/events/public/{public_token}/gifts/{gift_id}/questions", response_model=list[GiftQuestion])
def get_public_questions(public_token: str, gift_id: DatabaseId):
    return service.get_public_questions(public_token, gift_id)


@router.post("/events/public/{public_token}/gifts/{gift_id}/questions", response_model=GiftQuestion, status_code=201)
def create_question(public_token: str, gift_id: DatabaseId, data: GiftQuestionCreateRequest, request: Request):
    return service.create_question(
        public_token, gift_id, data.guest_name, data.text,
        request.client.host if request.client else "unknown",
    )


@router.patch("/gifts/{gift_id}/questions/{question_id}/answer", response_model=GiftQuestion)
def answer_question(
    gift_id: DatabaseId, question_id: DatabaseId, data: GiftQuestionAnswerRequest,
    current_user: User = Depends(get_current_user),
):
    return service.answer_question(gift_id, question_id, data.answer, current_user)


@router.delete("/gifts/{gift_id}/questions/{question_id}")
def delete_question(gift_id: DatabaseId, question_id: DatabaseId, current_user: User = Depends(get_current_user)):
    service.delete_question(gift_id, question_id, current_user)
    return {"deleted": True}
