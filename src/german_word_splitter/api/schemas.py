"""Request/response models."""

from typing import List

from pydantic import BaseModel, Field


class SplitRequest(BaseModel):
    word: str
    method: str = Field(default="charsplit")


class SplitResponse(BaseModel):
    word: str
    splittable: bool
    components: List[str]
