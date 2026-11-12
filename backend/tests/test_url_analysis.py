import unittest

from app.services.url_analysis import analyze_submitted_text, analyze_url, extract_urls


class URLAnalysisTests(unittest.TestCase):
    def test_extracts_multiple_urls_and_markdown_target(self) -> None:
        message = "See https://example.com/a, www.example.org and [chat](https://wa.me/8801)."
        self.assertEqual(
            extract_urls(message),
            ["https://example.com/a", "www.example.org", "https://wa.me/8801"],
        )

    def test_markdown_url_label_does_not_merge_with_target(self) -> None:
        message = "[https://wa.me/8801](https://wa.me/8801)"
        self.assertEqual(extract_urls(message), ["https://wa.me/8801"])

    def test_https_url_is_not_claimed_safe_without_reputation(self) -> None:
        result = analyze_url("https://example.com")
        self.assertEqual(result["status"], "unknown")
        self.assertFalse(analyze_submitted_text("https://example.com")["live_reputation_available"])

    def test_domain_without_scheme_is_normalized_safely(self) -> None:
        result = analyze_url("Example.COM/path")
        self.assertEqual(result["normalized_url"], "https://example.com/path")
        self.assertEqual(result["status"], "unknown")

    def test_http_alone_is_not_suspicious(self) -> None:
        result = analyze_url("http://example.com")
        self.assertEqual(result["status"], "unknown")
        self.assertIn("http", result["indicators"])

    def test_ip_address_url_is_detected(self) -> None:
        result = analyze_url("http://192.0.2.10/login")
        self.assertEqual(result["status"], "suspicious")
        self.assertIn("ip_address", result["indicators"])

    def test_unusual_port_is_detected(self) -> None:
        result = analyze_url("https://example.com:8443")
        self.assertEqual(result["status"], "suspicious")
        self.assertIn("unusual_port", result["indicators"])

    def test_shortener_is_not_labeled_phishing_by_itself(self) -> None:
        result = analyze_url("https://bit.ly/abc123")
        self.assertEqual(result["status"], "unknown")
        self.assertIn("shortener", result["indicators"])

    def test_misleading_brand_domain_is_suspicious(self) -> None:
        result = analyze_url("https://paypal.com.login-example.test/verify")
        self.assertEqual(result["status"], "suspicious")
        self.assertIn("brand_impersonation", result["indicators"])

    def test_misleading_security_subdomain_is_detected(self) -> None:
        result = analyze_url("https://secure.login.example.test")
        self.assertEqual(result["status"], "suspicious")
        self.assertIn("misleading_subdomain", result["indicators"])

    def test_external_redirect_parameter_is_detected(self) -> None:
        result = analyze_url("https://example.com/redirect?url=https%3A%2F%2Fother.test")
        self.assertEqual(result["status"], "suspicious")
        self.assertIn("external_redirect", result["indicators"])

    def test_malformed_url_is_unknown(self) -> None:
        result = analyze_url("http://[invalid")
        self.assertEqual(result["status"], "unknown")
        self.assertIsNone(result["normalized_url"])

    def test_unsupported_scheme_is_not_rewritten_as_https(self) -> None:
        result = analyze_url("ftp://example.com/file")
        self.assertEqual(result["status"], "unknown")
        self.assertIsNone(result["normalized_url"])

    def test_whatsapp_url_is_not_labeled_phishing(self) -> None:
        result = analyze_url("https://wa.me/8801917788990")
        self.assertEqual(result["status"], "no_obvious_threat")
        self.assertIn("whatsapp", result["indicators"])

    def test_bangladesh_bank_kyc_context_is_reported_separately(self) -> None:
        result = analyze_submitted_text(
            "বাংলাদেশ ব্যাংক থেকে গুরুত্বপূর্ণ বার্তা। আপনার অ্যাকাউন্ট সচল রাখতে "
            "অবিলম্বে এই লিংকে ক্লিক করে KYC আপডেট করুন: "
            "https://wa.me/8801917788990"
        )
        self.assertEqual(len(result["urls"]), 1)
        self.assertEqual(result["urls"][0]["status"], "no_obvious_threat")
        self.assertIsNotNone(result["message_context"])
        self.assertIn("claims to be from Bangladesh Bank", result["message_context"]["en"])


if __name__ == "__main__":
    unittest.main()
