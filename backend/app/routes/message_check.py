"""Message classification API endpoint."""

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field, field_validator

from app.services.message_analysis import classify_message

router = APIRouter(prefix="/api", tags=["message analysis"])


class MessageCheckRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message must not be empty or whitespace only.")
        return value


@router.post("/message-check")
def message_check(
    payload: MessageCheckRequest, request: Request
) -> dict[str, Any]:
    model = getattr(request.app.state, "message_model", None)
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Message analysis model is not available.",
        )
    return classify_message(payload.message, model)
