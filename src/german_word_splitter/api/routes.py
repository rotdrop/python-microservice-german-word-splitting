"""HTTP route handlers."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from ..errors import SplitterError
from ..services.splitter_service import SplitterService, get_service
from .schemas import SplitRequest, SplitResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/split", response_model=SplitResponse)
def split_word(
    request: SplitRequest, service: SplitterService = Depends(get_service)
) -> SplitResponse:
    word = request.word.strip()
    try:
        components = service.split(word, request.method)
    except SplitterError as exc:
        if exc.__cause__ is not None:
            logger.warning("Split failed: %s", exc, exc_info=exc.__cause__)
        raise HTTPException(status_code=400, detail=str(exc))
    return SplitResponse(word=word, splittable=len(components) > 1, components=components)
