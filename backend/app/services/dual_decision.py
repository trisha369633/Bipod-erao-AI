"""Reliability-aware result combination for separate message and URL analyses."""

from __future__ import annotations

import logging
from typing import Any

from app.services.gemini_analysis import GeminiAnalysisService

logger = logging.getLogger(__name__)

RELIABILITY_POLICY = {
    "calibration_available": False,
    "method": "agreement_or_abstain",
    "description": (
        "Raw ML probabilities and Gemini self-reported confidence are not "
        "comparable reliability measures. Agreement is returned as consensus; "
        "disagreement requires human review until representative, held-out "
        "calibration data exists for both systems."
    ),
}


def build_final_decision(
    ml_prediction: str,
    gemini_prediction: str | None,
    gemini_available: bool,
) -> dict[str, Any]:
    if not gemini_available or gemini_prediction is None:
        return {
            "status": "ml_fallback",
            "prediction": ml_prediction,
            "selected_system": "ml",
            "agreed": None,
            "reason": (
                "Gemini analysis was unavailable. The ML prediction is shown as "
                "a single-system fallback, not a dual-system decision."
            ),
        }

    if ml_prediction == gemini_prediction:
        return {
            "status": "agreement",
            "prediction": ml_prediction,
            "selected_system": "both",
            "agreed": True,
            "reason": (
                "Both systems independently returned the same label. This is "
                "consensus, not a calibrated guarantee of correctness."
            ),
        }

    return {
        "status": "review_required",
        "prediction": None,
        "selected_system": "none",
        "agreed": False,
        "reason": (
            "The systems disagreed. Neither system has validated comparative "
            "reliability calibration, so raw confidence scores are not used to "
            "choose a winner; human review is required."
        ),
    }


def _fallback_explanation(
    language: str, decision: dict[str, Any], ml_prediction: str
) -> str:
    if language == "bn":
        if decision["status"] == "agreement":
            return "দুটি সিস্টেম স্বাধীনভাবে একই ফল দিয়েছে। এটি সম্মতি, নিশ্চিত সঠিকতার প্রমাণ নয়।"
        if decision["status"] == "review_required":
            return "দুটি সিস্টেমের ফল আলাদা এবং তুলনামূলক নির্ভরযোগ্যতার যাচাইকৃত ক্যালিব্রেশন নেই। তাই নিশ্চিত ফল না দিয়ে মানবীয় পর্যালোচনা দরকার।"
        return f"Gemini বিশ্লেষণ পাওয়া যায়নি। একক-সিস্টেম বিকল্প হিসেবে ML ফল “{ml_prediction}” দেখানো হয়েছে।"
    if decision["status"] == "agreement":
        return "Both systems independently returned the same result. This is agreement, not proof that the prediction is correct."
    if decision["status"] == "review_required":
        return "The systems disagree and there is no validated calibration to compare their reliability. The result is therefore marked for human review."
    return (
        "Gemini analysis was unavailable. The ML result is shown as a "
        f"single-system fallback: {ml_prediction}."
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
    ml_confidence = (
        (ml_result.get("confidence_scores") or {}).get(ml_prediction)
        if analysis_type == "message"
        else ml_result.get("model_confidence")
    )
    ml_analysis = {
        "prediction": ml_prediction,
        "confidence": ml_confidence,
        "confidence_note": (
            "Model confidence score; not calibrated as a real-world probability."
        ),
        "risk_level": ml_result.get("risk_level"),
    }

    gemini_result: dict[str, Any]
    if gemini_service is None:
        gemini_result = {
            "status": "unavailable",
            "prediction": None,
            "confidence": None,
            "confidence_note": (
                "Gemini confidence is unavailable because Gemini analysis is not configured."
            ),
            "evidence": [],
            "reasons": [],
        }
    else:
        try:
            gemini_result = gemini_service.classify(analysis_type, original_input)
        except Exception as exc:
            logger.warning(
                "Gemini %s classification failed (%s).",
                analysis_type,
                type(exc).__name__,
            )
            gemini_result = {
                "status": "unavailable",
                "prediction": None,
                "confidence": None,
                "confidence_note": (
                    "Gemini confidence is unavailable because analysis failed."
                ),
                "evidence": [],
                "reasons": [],
            }

    decision = build_final_decision(
        ml_prediction,
        gemini_result.get("prediction"),
        gemini_result["status"] == "available",
    )
    explanation = _fallback_explanation(language, decision, ml_prediction)
    explanation_source = "fallback"
    if gemini_service is not None and gemini_result["status"] == "available":
        try:
            explanation = gemini_service.explain_decision(
                analysis_type,
                language,
                ml_prediction,
                gemini_result["prediction"],
                decision,
            )
            explanation_source = "gemini"
        except Exception as exc:
            logger.warning(
                "Gemini %s decision explanation failed (%s).",
                analysis_type,
                type(exc).__name__,
            )

    return {
        "analysis_type": analysis_type,
        "ml_analysis": ml_analysis,
        "ml_details": ml_result,
        "gemini_analysis": gemini_result,
        "agreement": decision["agreed"],
        "final_decision": decision,
        "decision_explanation": explanation,
        "explanation_source": explanation_source,
        "reliability_policy": RELIABILITY_POLICY,
    }