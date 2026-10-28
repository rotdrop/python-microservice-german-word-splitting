"""Request/response models."""

from typing import List, Optional

from pydantic import BaseModel, Field

from ..services.splitter_service import DEFAULT_METHOD


class SplitRequest(BaseModel):
    word: str
    method: str = Field(default=DEFAULT_METHOD)
    transliterate: Optional[str] = None


class SplitResponse(BaseModel):
    word: str
    splittable: bool
    components: List[str]


class InfoResponse(BaseModel):
    version: str
    default_method: str
    transliteration_locales: List[str]
