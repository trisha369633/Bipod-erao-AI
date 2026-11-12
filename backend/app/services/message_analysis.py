"""Inference and transparent rule indicators for message classification."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import joblib

EXPECTED_LABELS = {"normal", "promo", "smish"}

INDICATOR_PATTERNS = [
    (
        "credential_request",
        re.compile(
            r"(?:(?:otp|o\.t\.p\.|pin|password|passcode|bank(?:ing)? details?|"
            r"card details?).{0,35}(?:share|send|provide|enter|give|verify|"
            r"পাঠান|দিন|দেন|শেয়ার|শেয়ার|লিখুন|জানান|দিন|দিবেন)|"
            r"(?:share|send|provide|enter|give|verify|পাঠান|দিন|দেন|"
            r"শেয়ার|শেয়ার|লিখুন|জানান).{0,35}(?:otp|o\.t\.p\.|pin|"
            r"password|passcode|ব্যাংক.{0,8}(?:তথ্য|বিবরণ)|"
            r"কার্ডের তথ্য))",
            re.IGNORECASE,
        ),
        {
            "en": "The message asks for a credential or financial detail.",
            "bn": "মেসেজে পরিচয়-যাচাইয়ের গোপন তথ্য বা আর্থিক বিবরণ চাওয়া হয়েছে।",
        },
    ),
    (
        "urgent_verification",
        re.compile(
            r"(?:(?:urgent|immediately|right now|within \d+ (?:minutes?|hours?)|"
            r"account.{0,15}(?:suspend|block|close)|verify.{0,15}account|"
            r"জরুরি|এখনই|অবিলম্বে|অ্যাকাউন্ট.{0,12}(?:বন্ধ|ব্লক|স্থগিত)|"
            r"যাচাই.{0,12}(?:করুন|করতে হবে)).{0,45}"
            r"(?:verify|confirm|account|access|যাচাই|নিশ্চিত|অ্যাকাউন্ট|"
            r"প্রবেশ|বন্ধ|ব্লক)|"
            r"(?:verify|confirm|যাচাই|নিশ্চিত).{0,45}"
            r"(?:urgent|immediately|right now|account|জরুরি|এখনই|"
            r"অ্যাকাউন্ট|বন্ধ|ব্লক))",
            re.IGNORECASE,
        ),
        {
            "en": "Urgent language is paired with an account verification or access request.",
            "bn": "জরুরি ভাষার সঙ্গে অ্যাকাউন্ট যাচাই বা প্রবেশাধিকার চাওয়ার কথা আছে।",
        },
    ),
    (
        "prize_or_lottery_claim",
        re.compile(
            r"(?:\b(?:you(?:'ve| have)? won|winner|prize|lottery|claim your "
            r"(?:reward|prize)|lucky draw)\b|"
            r"(?:জিতেছেন|জিতেছ|পুরস্কার|লটারি|লটারিতে|ভাগ্যবান বিজয়ী|"
            r"ভাগ্যবান বিজয়ী)|"
            r"\b(?:jitechen|jitechhen|purashkar|lottery jite|"
            r"lucky draw|prize claim)\b)",
            re.IGNORECASE,
        ),
        {
            "en": "The message contains a prize, lottery, or winner claim.",
            "bn": "মেসেজে পুরস্কার, লটারি বা বিজয়ী হওয়ার দাবি আছে।",
        },
    ),
    (
        "shortened_url",
        re.compile(
            r"(?<![\w.-])(?:https?://)?(?:www\.)?"
            r"(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|is\.gd|cutt\.ly|"
            r"rb\.gy|rebrand\.ly|ow\.ly|shorturl\.at)/[^\s<>]+",
            re.IGNORECASE,
        ),
        {
            "en": "The message contains a URL from a known link-shortening domain.",
            "bn": "মেসেজে পরিচিত URL সংক্ষিপ্তকরণ ডোমেইনের লিংক আছে।",
        },
    ),
    (
        "payment_or_recovery_request",
        re.compile(
            r"(?:\b(?:send money|transfer (?:money|funds)|pay (?:now|a fee)|"
            r"payment required|account recovery|recover your account|"
            r"unlock your account|refund processing)\b|"
            r"(?:টাকা পাঠান|টাকা দিন|পেমেন্ট করুন|পেমেন্ট দিন|ফি জমা|"
            r"অ্যাকাউন্ট পুনরুদ্ধার|অ্যাকাউন্ট খুলে|টাকা ফেরত পেতে)|"
            r"\b(?:taka pathan|taka din|payment korun|fee din|"
            r"account recovery|account unlock)\b)",
            re.IGNORECASE,
        ),
        {
            "en": "The message asks for a payment, money transfer, or account recovery action.",
            "bn": "মেসেজে পেমেন্ট, টাকা পাঠানো বা অ্যাকাউন্ট পুনরুদ্ধারের অনুরোধ আছে।",
        },
    ),
]

SAFETY_ADVICE = {
    "en": [
        "Never share your OTP, PIN, password, or banking details in response to an unsolicited message.",
        "Do not click suspicious links or send money before verifying the request.",
        "Contact the organization through a phone number or website you find independently.",
    ],
    "bn": [
        "অপ্রত্যাশিত মেসেজের উত্তরে OTP, PIN, পাসওয়ার্ড বা ব্যাংকিং তথ্য শেয়ার করবেন না।",
        "অনুরোধ যাচাই না করে সন্দেহজনক লিংকে ক্লিক বা টাকা পাঠাবেন না।",
        "নিজে থেকে খুঁজে পাওয়া ফোন নম্বর বা ওয়েবসাইটের মাধ্যমে প্রতিষ্ঠানের সঙ্গে যোগাযোগ করুন।",
    ],
}

EXPLANATION = {
    "model": {
        "en": "The TF-IDF and Logistic Regression model classified text patterns; it does not understand the message's full meaning.",
        "bn": "TF-IDF ও Logistic Regression মডেলটি টেক্সটের ধরনভিত্তিক বৈশিষ্ট্য থেকে শ্রেণিবিন্যাস করেছে; এটি মেসেজের পূর্ণ অর্থ বোঝে না।",
    },
    "rule_based": {
        "en": "Rule-based indicators are separate from the model classification and appear only when matching text is found.",
        "bn": "নিয়মভিত্তিক সূচকগুলো মডেলের শ্রেণিবিন্যাস থেকে আলাদা এবং মিল থাকা টেক্সট পাওয়া গেলেই দেখানো হয়।",
    },
}

CONFIDENCE_NOTE = {
    "en": "These are model confidence scores, not calibrated real-world probabilities of fraud.",
    "bn": "এগুলো মডেলের আত্মবিশ্বাসের স্কোর; বাস্তব প্রতারণার ক্যালিব্রেটেড সম্ভাবনা নয়।",
}

RISK_SCORE_NOTE = {
    "en": "Formula: normal starts at 10, promo at 20, smish at 40, plus 15 per distinct matched indicator (capped at 100). Low is below 35, medium 35–69, high 70–100. This is not a calibrated probability or guarantee.",
    "bn": "সূত্র: সাধারণ ১০, প্রচারমূলক ২০, স্মিশিং ৪০ দিয়ে শুরু; প্রতিটি আলাদা মেলা সূচকে ১৫ যোগ হয় (সর্বোচ্চ ১০০)। ৩৫-এর কম কম, ৩৫–৬৯ মাঝারি, ৭০–১০০ উচ্চ। এটি ক্যালিব্রেটেড সম্ভাবনা বা নিশ্চয়তা নয়।",
}

MODEL_CLASS_POINTS = {"normal": 10, "promo": 20, "smish": 40}
POINTS_PER_INDICATOR = 15


def load_message_model() -> Any:
    """Load and validate the saved pipeline once during application startup."""
    backend_dir = Path(__file__).resolve().parents[2]
    model_path = backend_dir / "trained_model" / "message_baseline.joblib"
    if not model_path.is_file():
        raise FileNotFoundError(f"Trained message model not found: {model_path}")

    model = joblib.load(model_path)
    classifier = getattr(model, "named_steps", {}).get("classifier")
    classes = set(getattr(classifier, "classes_", []))
    if classes != EXPECTED_LABELS:
        raise ValueError(
            f"Message model classes must be {sorted(EXPECTED_LABELS)}; "
            f"found {sorted(classes)}."
        )
    if not callable(getattr(model, "predict", None)):
        raise TypeError("Saved message pipeline does not provide predict().")
    return model


def find_indicators(message: str) -> list[dict[str, Any]]:
    """Return only rule patterns with matches in the submitted text."""
    indicators = []
    for code, pattern, description in INDICATOR_PATTERNS:
        matches = list(dict.fromkeys(match.group(0).strip() for match in pattern.finditer(message)))
        if matches:
            indicators.append(
                {"code": code, "matches": matches, "description": description}
            )
    return indicators


def classify_message(message: str, model: Any) -> dict[str, Any]:
    predicted_label = str(model.predict([message])[0])
    if predicted_label not in EXPECTED_LABELS:
        raise ValueError(f"Unexpected predicted message label: {predicted_label}")

    confidence_scores = None
    predict_proba = getattr(model, "predict_proba", None)
    if callable(predict_proba):
        probabilities = predict_proba([message])[0]
        class_labels = model.named_steps["classifier"].classes_
        confidence_scores = {
            str(label): float(score)
            for label, score in zip(class_labels, probabilities)
        }

    indicators = find_indicators(message)
    risk_score = min(
        100,
        MODEL_CLASS_POINTS[predicted_label]
        + POINTS_PER_INDICATOR * len(indicators),
    )
    risk_level = "high" if risk_score >= 70 else "medium" if risk_score >= 35 else "low"

    return {
        "predicted_label": predicted_label,
        "confidence_scores": confidence_scores,
        "confidence_note": CONFIDENCE_NOTE,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "risk_score_note": RISK_SCORE_NOTE,
        "explanation": EXPLANATION,
        "suspicious_indicators": indicators,
        "safety_advice": SAFETY_ADVICE,
    }
