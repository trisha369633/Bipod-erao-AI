"""URL phishing model API endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.services.url_classification import (
    URLInputError,
    URLPredictionError,
    classify_url,
)

router = APIRouter(prefix="/api", tags=["URL classification"])


class URLCheckRequest(BaseModel):
    url: str = Field(min_length=1, max_length=5000)

    @field_validator("url")
    @classmethod
    def url_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("URL must not be empty or whitespace only.")
        return value


@router.post("/url-check")
def url_check(payload: URLCheckRequest, request: Request) -> dict[str, Any]:
    model = getattr(request.app.state, "url_model", None)
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="URL classification model is not available.",
        )
    try:
        return classify_url(payload.url, model)
    except URLInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except URLPredictionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
