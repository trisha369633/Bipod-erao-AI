"""Inference service for the independently trained URL phishing model."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import joblib

from dataset.url.normalize_url import URLNormalizationError, normalize_url

EXPECTED_LABELS = {"phishing", "legitimate"}

LEGITIMATE_MESSAGE = (
    "No phishing pattern was detected by the URL model. "
    "This does not guarantee that the website is safe."
)
PHISHING_MESSAGE = (
    "The URL model detected patterns associated with phishing. "
    "Do not enter credentials or payment details."
)


class URLInputError(ValueError):
    """Raised when a submitted URL is not a valid absolute HTTP(S) URL."""


class URLModelLoadError(RuntimeError):
    """Raised when the saved URL model cannot be loaded or validated."""


class URLPredictionError(RuntimeError):
    """Raised when the loaded URL model cannot produce a valid prediction."""


def load_url_model() -> Any:
    """Load and validate the saved URL pipeline once during app startup."""
    backend_dir = Path(__file__).resolve().parents[2]
    model_path = backend_dir / "trained_model" / "url_phishing_char_tfidf_logreg.joblib"
    try:
        if not model_path.is_file():
            raise FileNotFoundError("Saved URL model artifact is missing.")
        model = joblib.load(model_path)
        classes = set(getattr(model, "classes_", []))
        if classes != EXPECTED_LABELS:
            raise ValueError(
                f"URL model classes must be {sorted(EXPECTED_LABELS)}; "
                f"found {sorted(classes)}."
            )
        if not callable(getattr(model, "predict", None)):
            raise TypeError("Saved URL pipeline does not provide predict().")
        if not callable(getattr(model, "predict_proba", None)):
            raise TypeError("Saved URL pipeline does not provide predict_proba().")
        return model
    except URLModelLoadError:
        raise
    except (
        AttributeError,
        EOFError,
        ImportError,
        OSError,
        pickle.UnpicklingError,
        TypeError,
        ValueError,
    ) as exc:
        raise URLModelLoadError(
            "Saved URL classification model could not be loaded or validated."
        ) from exc


def classify_url(url: str, model: Any) -> dict[str, Any]:
    """Validate and classify one URL; confidence is a model score, not a guarantee."""
    try:
        normalized_url = normalize_url(url)
    except URLNormalizationError as exc:
        raise URLInputError(
            "URL must be a valid absolute HTTP or HTTPS URL."
        ) from exc

    try:
        prediction = str(model.predict([normalized_url])[0])
        classes = [str(label) for label in model.classes_]
        if prediction not in EXPECTED_LABELS or prediction not in classes:
            raise URLPredictionError("URL model returned an unsupported prediction.")
        probabilities = model.predict_proba([normalized_url])[0]
        if len(probabilities) != len(classes):
            raise URLPredictionError("URL model returned invalid confidence scores.")
        model_confidence = float(probabilities[classes.index(prediction)])
        if not 0.0 <= model_confidence <= 1.0:
            raise URLPredictionError("URL model returned an invalid confidence score.")
    except URLPredictionError:
        raise
    except (AttributeError, IndexError, TypeError, ValueError, RuntimeError) as exc:
        raise URLPredictionError("URL model could not analyze this URL.") from exc

    return {
        "url": url,
        "prediction": prediction,
        "risk_level": "high" if prediction == "phishing" else "low",
        "model_confidence": model_confidence,
        "message": (
            PHISHING_MESSAGE if prediction == "phishing" else LEGITIMATE_MESSAGE
        ),
    }
