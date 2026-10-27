"""Request/response models."""

from typing import List, Optional

from pydantic import BaseModel, Field


class SplitRequest(BaseModel):
    word: str
    method: str = Field(default="charsplit")
    transliterate: Optional[str] = None


class SplitResponse(BaseModel):
    word: str
    splittable: bool
    components: List[str]
