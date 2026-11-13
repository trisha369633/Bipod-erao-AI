import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class FakeGemini:
    def __init__(self, prediction="smish"):
        self.prediction = prediction

    def classify(self, analysis_type, original_input):
        prediction = (
            self.prediction
            if analysis_type == "message"
            else "phishing"
        )
        return {
            "status": "available",
            "prediction": prediction,
            "confidence": 0.7,
            "confidence_note": "self-reported",
            "evidence": ["synthetic evidence"],
            "reasons": ["synthetic reason"],
        }


class FailingGemini:
    def classify(self, analysis_type, original_input):
        raise RuntimeError("synthetic API failure")


class DualAnalysisAPITests(unittest.TestCase):
    def test_dual_message_endpoint_returns_final_decision(self):
        with patch("app.main.load_gemini_service", return_value=FakeGemini()):
            with TestClient(app) as client:
                response = client.post(
                    "/api/dual/message-check",
                    json={"message": "synthetic message", "language": "en"},
                )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(set(body), {"final_decision", "decision_explanation"})
        self.assertIn(
            body["final_decision"]["prediction"],
            {"phishing", "legitimate"},
        )
        self.assertIsInstance(body["decision_explanation"], str)

    def test_dual_url_endpoint_returns_final_decision(self):
        with patch("app.main.load_gemini_service", return_value=FakeGemini()):
            with TestClient(app) as client:
                response = client.post(
                    "/api/dual/url-check",
                    json={"url": "https://example.com", "language": "bn"},
                )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(set(body), {"final_decision", "decision_explanation"})
        self.assertIn(
            body["final_decision"]["prediction"],
            {"phishing", "legitimate"},
        )
        self.assertIsInstance(body["decision_explanation"], str)

    def test_missing_gemini_service_returns_friendly_retryable_503(self):
        with patch("app.main.load_gemini_service", return_value=None):
            with TestClient(app) as client:
                response = client.post(
                    "/api/dual/message-check",
                    json={"message": "synthetic message"},
                )
        self.assertEqual(response.status_code, 503)
        detail = response.json()["detail"]
        self.assertEqual(detail["code"], "GEMINI_UNAVAILABLE")
        self.assertIn("try again", detail["message"].lower())

    def test_gemini_failure_returns_no_prediction_or_technical_detail(self):
        with patch("app.main.load_gemini_service", return_value=FailingGemini()):
            with TestClient(app) as client:
                response = client.post(
                    "/api/dual/url-check",
                    json={"url": "https://example.com"},
                )
        self.assertEqual(response.status_code, 503)
        body = response.json()
        self.assertEqual(body["detail"]["code"], "GEMINI_UNAVAILABLE")
        self.assertNotIn("synthetic API failure", str(body))

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
