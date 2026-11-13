"""Reliability-aware result combination for separate message and URL analyses."""

from __future__ import annotations

import logging
from typing import Any

from app.services.gemini_analysis import (
    GeminiAnalysisService,
    GeminiUnavailableError,
    describe_gemini_error,
)

logger = logging.getLogger(__name__)

def binary_prediction(analysis_type: str, prediction: str) -> str:
    if analysis_type == "message":
        if prediction == "smish":
            return "phishing"
        if prediction in {"normal", "promo"}:
            return "legitimate"
    elif analysis_type == "url" and prediction in {"phishing", "legitimate"}:
        return prediction
    raise ValueError(f"Unsupported {analysis_type} prediction: {prediction}")


def build_final_decision(
    analysis_type: str,
    ml_prediction: str,
    gemini_prediction: str,
) -> dict[str, Any]:
    ml_binary = binary_prediction(analysis_type, ml_prediction)
    gemini_binary = binary_prediction(analysis_type, gemini_prediction)
    agreed = ml_binary == gemini_binary
    return {
        "status": "agreement" if agreed else "gemini_priority",
        "prediction": ml_binary if agreed else gemini_binary,
        "selected_system": "both" if agreed else "gemini",
        "agreed": agreed,
    }


def _fallback_explanation(
    language: str, analysis_type: str, prediction: str
) -> str:
    phishing = prediction == "phishing"
    if analysis_type == "message":
        if language == "bn":
            return (
                "মেসেজটিতে প্রতারণার লক্ষণ থাকতে পারে। লিংকে ক্লিক করবেন না বা "
                "গোপন তথ্য শেয়ার করবেন না।"
                if phishing
                else "ফিশিং শনাক্ত হয়নি। অপ্রত্যাশিত অনুরোধ হলে অফিসিয়াল মাধ্যমে যাচাই করুন।"
            )
        return (
            "This message may be fraudulent. Avoid its links and do not share private information."
            if phishing
            else "No phishing was identified. Verify unexpected requests through an official channel."
        )
    if language == "bn":
        return (
            "লিংকটি সন্দেহজনক হতে পারে। অফিসিয়াল ওয়েবসাইট থেকে ঠিকানা যাচাই করুন।"
            if phishing
            else "ফিশিং শনাক্ত হয়নি। সংবেদনশীল তথ্য দেওয়ার আগে ওয়েবসাইটটি যাচাই করুন।"
        )
    return (
        "This link may be suspicious. Verify it through the organization's official website."
        if phishing
        else "No phishing was identified. Verify the website before sharing sensitive information."
    )


def run_dual_analysis(
    analysis_type: str,
    original_input: str,
    ml_result: dict[str, Any],
    gemini_service: GeminiAnalysisService | None,
    language: str = "en",
) -> dict[str, Any]:
    ml_prediction = (
        ml_result["predicted_label"]
        if analysis_type == "message"
        else ml_result["prediction"]
    )

    if gemini_service is None:
        logger.error(
            "Gemini %s classification is unavailable: client is not configured.",
            analysis_type,
        )
        raise GeminiUnavailableError("Gemini client is not configured.")
    try:
        gemini_result = gemini_service.classify(analysis_type, original_input)
    except Exception as exc:
        diagnostic = describe_gemini_error(exc)
        logger.error(
            "Gemini %s classification failed: category=%s status=%s type=%s message=%s",
            analysis_type,
            diagnostic["category"],
            diagnostic["status_code"],
            diagnostic["exception_type"],
            diagnostic["message"],
        )
        raise GeminiUnavailableError("Gemini classification failed.") from exc

    decision = build_final_decision(
        analysis_type,
        ml_prediction,
        gemini_result["prediction"],
    )
    explanation = _fallback_explanation(
        language, analysis_type, decision["prediction"]
    )

    return {
        "final_decision": {"prediction": decision["prediction"]},
        "decision_explanation": explanation,
    }