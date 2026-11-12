import unittest

from app.services.dual_decision import build_final_decision, run_dual_analysis


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

    def explain_decision(
        self, analysis_type, language, ml_prediction, gemini_prediction, decision
    ):
        return f"{analysis_type}:{language}:{decision['status']}"


class FailingGemini:
    def classify(self, analysis_type, original_input):
        raise RuntimeError("synthetic API failure")


def message_ml_result(prediction, confidence):
    return {
        "predicted_label": prediction,
        "confidence_scores": {prediction: confidence},
        "risk_level": "low",
    }


class DualDecisionTests(unittest.TestCase):
    def test_agreement_selects_shared_prediction(self):
        decision = build_final_decision("smish", "smish", gemini_available=True)
        self.assertEqual(decision["status"], "agreement")
        self.assertEqual(decision["prediction"], "smish")
        self.assertEqual(decision["selected_system"], "both")
        self.assertTrue(decision["agreed"])

    def test_disagreement_requires_review_without_calibration(self):
        decision = build_final_decision(
            "normal", "smish", gemini_available=True
        )
        self.assertEqual(decision["status"], "review_required")
        self.assertIsNone(decision["prediction"])
        self.assertEqual(decision["selected_system"], "none")
        self.assertFalse(decision["agreed"])

    def test_raw_confidence_comparison_does_not_choose_disagreement_winner(self):
        gemini = FakeGemini("smish", confidence=0.99)
        result = run_dual_analysis(
            "message",
            "synthetic input",
            message_ml_result("normal", 0.51),
            gemini,
        )
        self.assertEqual(result["final_decision"]["status"], "review_required")
        self.assertIsNone(result["final_decision"]["prediction"])
        self.assertEqual(result["ml_analysis"]["confidence"], 0.51)
        self.assertEqual(result["gemini_analysis"]["confidence"], 0.99)

    def test_gemini_failure_falls_back_to_ml_and_has_explanation(self):
        result = run_dual_analysis(
            "message",
            "synthetic input",
            message_ml_result("promo", 0.75),
            FailingGemini(),
            language="en",
        )
        self.assertEqual(result["gemini_analysis"]["status"], "unavailable")
        self.assertEqual(result["final_decision"]["status"], "ml_fallback")
        self.assertEqual(result["final_decision"]["prediction"], "promo")
        self.assertEqual(result["final_decision"]["selected_system"], "ml")
        self.assertIn("fallback", result["decision_explanation"])

    def test_gemini_receives_input_independently_and_explains_after_decision(self):
        gemini = FakeGemini("phishing", confidence=0.8)
        result = run_dual_analysis(
            "url",
            "https://synthetic.test/path",
            {
                "prediction": "phishing",
                "model_confidence": 0.6,
                "risk_level": "high",
            },
            gemini,
            language="bn",
        )
        self.assertEqual(gemini.seen_input, ("url", "https://synthetic.test/path"))
        self.assertEqual(result["explanation_source"], "gemini")
        self.assertEqual(result["decision_explanation"], "url:bn:agreement")


if __name__ == "__main__":
    unittest.main()