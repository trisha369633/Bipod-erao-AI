import unittest
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.url_classification import URLModelLoadError, load_url_model


class URLCheckAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.client_context.__exit__(None, None, None)

    def test_valid_url_returns_separate_model_result(self) -> None:
        response = self.client.post(
            "/api/url-check", json={"url": "https://example.test/path"}
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["url"], "https://example.test/path")
        self.assertIn(result["prediction"], {"phishing", "legitimate"})
        self.assertIn(result["risk_level"], {"high", "low"})
        self.assertGreaterEqual(result["model_confidence"], 0.0)
        self.assertLessEqual(result["model_confidence"], 1.0)
        self.assertTrue(result["message"])

    def test_invalid_and_unsupported_urls_return_422(self) -> None:
        for value in ("not-a-url", "ftp://example.test/file", "https://[broken"):
            with self.subTest(value=value):
                response = self.client.post("/api/url-check", json={"url": value})
                self.assertEqual(response.status_code, 422)

    def test_empty_url_returns_422(self) -> None:
        response = self.client.post("/api/url-check", json={"url": ""})
        self.assertEqual(response.status_code, 422)

    def test_missing_model_returns_503(self) -> None:
        model = app.state.url_model
        try:
            app.state.url_model = None
            response = self.client.post(
                "/api/url-check", json={"url": "https://example.test"}
            )
        finally:
            app.state.url_model = model
        self.assertEqual(response.status_code, 503)

    def test_prediction_error_returns_500(self) -> None:
        model = app.state.url_model
        broken_model = Mock()
        broken_model.predict.side_effect = ValueError("synthetic model failure")
        try:
            app.state.url_model = broken_model
            response = self.client.post(
                "/api/url-check", json={"url": "https://example.test"}
            )
        finally:
            app.state.url_model = model
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json()["detail"], "URL model could not analyze this URL."
        )

    def test_model_loading_error_is_reported(self) -> None:
        with patch(
            "app.services.url_classification.joblib.load",
            side_effect=OSError("synthetic load failure"),
        ):
            with self.assertRaises(URLModelLoadError):
                load_url_model()

    def test_message_check_route_still_works(self) -> None:
        response = self.client.post(
            "/api/message-check", json={"message": "Hello, how are you?"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(
            response.json()["predicted_label"], {"normal", "promo", "smish"}
        )


if __name__ == "__main__":
    unittest.main()
