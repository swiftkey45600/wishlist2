from dataclasses import dataclass
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


QuestionText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


@dataclass
class GiftQuestion:
    id: int
    gift_id: int
    guest_name: str
    text: str
    created_at: str
    answer: str | None = None
    answered_at: str | None = None


class GiftQuestionCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    guest_name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    text: QuestionText


class GiftQuestionAnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: QuestionText
