import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.services.dual_decision import (
    build_final_decision,
    run_dual_analysis,
)
from app.services.gemini_analysis import (
    GeminiAnalysisService,
    GeminiAnalysisError,
    GeminiCircuitOpenError,
    describe_gemini_error,
)


class FakeGemini:
    def __init__(self, prediction, confidence=0.5):
        self.prediction = prediction
        self.confidence = confidence
        self.seen_input = None

    def classify(self, analysis_type, original_input):
        self.seen_input = (analysis_type, original_input)
        return {
            "status": "available",
            "prediction": self.prediction,
            "confidence": self.confidence,
            "confidence_note": "self-reported",
            "evidence": ["synthetic evidence"],
            "reasons": ["synthetic reason"],
        }


class FailingGemini:
    def __init__(self, error=None):
        self.error = error or RuntimeError("synthetic API failure")

    def classify(self, analysis_type, original_input):
        raise self.error


class InvalidJsonGeminiClient:
    class Models:
        def generate_content(self, **kwargs):
            return SimpleNamespace(text="not JSON")

    models = Models()


class FakeGeminiModels:
    def __init__(self, error):
        self.error = error
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return SimpleNamespace(
            text=(
                '{"prediction":"legitimate","confidence":0.8,'
                '"evidence":["no suspicious pattern"],"reasons":["test"]}'
            )
        )


class FakeApiError(RuntimeError):
    def __init__(self, status_code):
        super().__init__(f"synthetic Google API status {status_code}")
        self.code = status_code


def message_ml_result(prediction, confidence):
    return {
        "predicted_label": prediction,
        "confidence_scores": {prediction: confidence},
        "risk_level": "low",
    }


class DualDecisionTests(unittest.TestCase):
    def test_all_binary_combinations_follow_gemini_priority(self):
        combinations = (
            ("message", "smish", "smish", "phishing", "both"),
            ("message", "normal", "normal", "legitimate", "both"),
            ("message", "smish", "normal", "legitimate", "gemini"),
            ("message", "normal", "smish", "phishing", "gemini"),
            ("url", "phishing", "phishing", "phishing", "both"),
            ("url", "legitimate", "legitimate", "legitimate", "both"),
            ("url", "phishing", "legitimate", "legitimate", "gemini"),
            ("url", "legitimate", "phishing", "phishing", "gemini"),
        )
        for analysis_type, ml, gemini, expected, selected in combinations:
            with self.subTest(analysis_type=analysis_type, ml=ml, gemini=gemini):
                decision = build_final_decision(analysis_type, ml, gemini)
                self.assertEqual(decision["prediction"], expected)
                self.assertEqual(decision["selected_system"], selected)
                self.assertEqual(decision["agreed"], selected == "both")

    def test_message_promo_maps_to_legitimate(self):
        decision = build_final_decision("message", "promo", "normal")
        self.assertEqual(decision["prediction"], "legitimate")
        self.assertTrue(decision["agreed"])

    def test_gemini_receives_original_input_independently(self):
        gemini = FakeGemini("phishing", confidence=0.8)
        result = run_dual_analysis(
            "url",
            "https://synthetic.test/path",
            {
                "prediction": "legitimate",
                "model_confidence": 0.6,
                "risk_level": "low",
            },
            gemini,
            language="bn",
        )
        self.assertEqual(gemini.seen_input, ("url", "https://synthetic.test/path"))
        self.assertEqual(result["final_decision"]["prediction"], "phishing")
        self.assertIn("লিংক", result["decision_explanation"])

    def test_gemini_failure_uses_ml_only_decision(self):
        for error in (
            FakeApiError(429),
            FakeApiError(503),
            TimeoutError("synthetic timeout"),
        ):
            with self.subTest(error=type(error).__name__):
                result = run_dual_analysis(
                    "message",
                    "synthetic input",
                    message_ml_result("smish", 0.75),
                    FailingGemini(error),
                    language="en",
                )
                self.assertEqual(
                    result["final_decision"]["prediction"], "phishing"
                )
                self.assertNotIn("Gemini", str(result))

    def test_missing_gemini_client_falls_back_to_ml(self):
        result = run_dual_analysis(
            "message",
            "synthetic input",
            message_ml_result("promo", 0.75),
            None,
            language="en",
        )
        self.assertEqual(result["final_decision"]["prediction"], "legitimate")
        self.assertIn("No phishing", result["decision_explanation"])

    def test_quota_error_is_classified_and_api_key_is_redacted(self):
        api_key = "AIza123456789012345678901234567890"
        exception = RuntimeError(f"quota exhausted for {api_key}")
        exception.code = 429
        with patch.dict("os.environ", {"GEMINI_API_KEY": api_key}):
            diagnostic = describe_gemini_error(exception)
        self.assertEqual(diagnostic["status_code"], 429)
        self.assertEqual(diagnostic["category"], "quota_or_rate_limit")
        self.assertNotIn(api_key, diagnostic["message"])

    def test_temporary_server_and_timeout_errors_are_not_labeled_as_quota(self):
        self.assertEqual(
            describe_gemini_error(FakeApiError(503))["category"],
            "temporary_server_error",
        )
        self.assertEqual(
            describe_gemini_error(TimeoutError("synthetic timeout"))["category"],
            "network_or_timeout",
        )

    def test_invalid_gemini_response_is_not_mislabeled_as_network_failure(self):
        diagnostic = describe_gemini_error(GeminiAnalysisError("Invalid JSON."))
        self.assertEqual(diagnostic["category"], "invalid_response")

    def test_invalid_json_gemini_response_is_rejected(self):
        service = GeminiAnalysisService(InvalidJsonGeminiClient(), "test-model")
        with self.assertRaises(GeminiAnalysisError):
            service.classify("message", "synthetic input")

    def test_circuit_breaker_cools_down_then_allows_a_recovery_probe(self):
        clock = [100.0]
        models = FakeGeminiModels(FakeApiError(429))
        service = GeminiAnalysisService(SimpleNamespace(models=models), "test-model")

        with patch(
            "app.services.gemini_analysis.time.monotonic",
            side_effect=lambda: clock[0],
        ):
            for _ in range(3):
                with self.assertRaises(FakeApiError):
                    service.classify("url", "https://example.test")

            self.assertEqual(models.calls, 3)
            with self.assertRaises(GeminiCircuitOpenError):
                service.classify("url", "https://example.test")
            self.assertEqual(models.calls, 3)

            clock[0] += 31
            models.error = None
            result = service.classify("url", "https://example.test")

        self.assertEqual(models.calls, 4)
        self.assertEqual(result["prediction"], "legitimate")


if __name__ == "__main__":
    unittest.main()
