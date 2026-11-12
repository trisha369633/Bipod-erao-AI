"""Independent URL analysis endpoints."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator

from app.services.url_analysis import analyze_submitted_text

router = APIRouter(prefix="/api", tags=["URL analysis"])


class URLAnalysisRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)

    @field_validator("message")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Text must not be empty or whitespace only.")
        return value


class LinkAnalysisRequest(BaseModel):
    url: str = Field(min_length=1, max_length=5000)

    @field_validator("url")
    @classmethod
    def url_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("URL must not be empty or whitespace only.")
        return value


@router.post("/url-analysis")
def url_analysis(payload: URLAnalysisRequest) -> dict[str, Any]:
    return analyze_submitted_text(payload.message)


@router.post("/analyze/link")
def link_analysis(payload: LinkAnalysisRequest) -> dict[str, Any]:
    return analyze_submitted_text(payload.url)
