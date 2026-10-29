from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from app.models.identifiers import DatabaseId


class GiftImportItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["wish", "gift"]
    id: DatabaseId


class GiftImportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[GiftImportItem] = Field(min_length=1, max_length=50)
