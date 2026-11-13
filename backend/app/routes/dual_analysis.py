"""Dual independent ML and Gemini analysis endpoints."""

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.services.dual_decision import run_dual_analysis
from app.services.gemini_analysis import GeminiUnavailableError
from app.services.message_analysis import classify_message
from app.services.url_classification import (
    URLInputError,
    URLPredictionError,
    classify_url,
)

router = APIRouter(prefix="/api/dual", tags=["dual decision"])


class MessageAnalysisRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    language: Literal["en", "bn"] = "en"

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message must not be empty or whitespace only.")
        return value


class URLAnalysisRequest(BaseModel):
    url: str = Field(min_length=1, max_length=5000)
    language: Literal["en", "bn"] = "en"

    @field_validator("url")
    @classmethod
    def url_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("URL must not be empty or whitespace only.")
        return value


@router.post("/message-check")
def dual_message_check(
    payload: MessageAnalysisRequest, request: Request
) -> dict[str, Any]:
    model = getattr(request.app.state, "message_model", None)
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Message analysis model is not available.",
        )
    ml_result = classify_message(payload.message, model)
    try:
        return run_dual_analysis(
            "message",
            payload.message,
            ml_result,
            getattr(request.app.state, "gemini_service", None),
            payload.language,
        )
    except GeminiUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "GEMINI_UNAVAILABLE",
                "message": "Analysis is temporarily unavailable. Please try again.",
            },
        ) from exc


@router.post("/url-check")
def dual_url_check(payload: URLAnalysisRequest, request: Request) -> dict[str, Any]:
    model = getattr(request.app.state, "url_model", None)
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="URL classification model is not available.",
        )
    try:
        ml_result = classify_url(payload.url, model)
    except URLInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except URLPredictionError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    try:
        return run_dual_analysis(
            "url",
            payload.url,
            ml_result,
            getattr(request.app.state, "gemini_service", None),
            payload.language,
        )
    except GeminiUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "GEMINI_UNAVAILABLE",
                "message": "Analysis is temporarily unavailable. Please try again.",
            },
        ) from exc