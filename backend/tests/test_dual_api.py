import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class FakeGemini:
    def classify(self, analysis_type, original_input):
        prediction = "smish" if analysis_type == "message" else "phishing"
        return {
            "status": "available",
            "prediction": prediction,
            "confidence": 0.7,
            "confidence_note": "self-reported",
            "evidence": ["synthetic evidence"],
            "reasons": ["synthetic reason"],
        }

    def explain_decision(
        self, analysis_type, language, ml_prediction, gemini_prediction, decision
    ):
        return "synthetic decision explanation"


class DualAnalysisAPITests(unittest.TestCase):
    def test_dual_message_endpoint_returns_both_analyses_and_decision(self):
        with patch("app.main.load_gemini_service", return_value=FakeGemini()):
            with TestClient(app) as client:
                response = client.post(
                    "/api/dual/message-check",
                    json={"message": "synthetic message", "language": "en"},
                )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn(body["ml_analysis"]["prediction"], {"normal", "promo", "smish"})
        self.assertEqual(body["gemini_analysis"]["prediction"], "smish")
        self.assertIn(
            body["final_decision"]["status"],
            {"agreement", "review_required"},
        )
        self.assertIn("ml_details", body)

    def test_dual_url_endpoint_returns_both_analyses(self):
        with patch("app.main.load_gemini_service", return_value=FakeGemini()):
            with TestClient(app) as client:
                response = client.post(
                    "/api/dual/url-check",
                    json={"url": "https://example.com", "language": "bn"},
                )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn(body["ml_analysis"]["prediction"], {"phishing", "legitimate"})
        self.assertEqual(body["gemini_analysis"]["prediction"], "phishing")
        self.assertIn(
            body["final_decision"]["status"],
            {"agreement", "review_required"},
        )
        self.assertEqual(body["explanation_source"], "gemini")

    def test_gemini_unavailable_uses_explicit_ml_fallback(self):
        with patch("app.main.load_gemini_service", return_value=None):
            with TestClient(app) as client:
                response = client.post(
                    "/api/dual/message-check",
                    json={"message": "synthetic message"},
                )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["gemini_analysis"]["status"], "unavailable")
        self.assertEqual(body["final_decision"]["status"], "ml_fallback")
        self.assertEqual(
            body["final_decision"]["prediction"],
            body["ml_analysis"]["prediction"],
        )

    def test_invalid_dual_url_is_rejected(self):
        with patch("app.main.load_gemini_service", return_value=None):
            with TestClient(app) as client:
                response = client.post(
                    "/api/dual/url-check",
                    json={"url": "ftp://example.com"},
                )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()