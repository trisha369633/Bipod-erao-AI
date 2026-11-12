"""Synthetic-only tests for the URL dataset preparation utilities."""

from __future__ import annotations

import unittest

from normalize_url import URLNormalizationError, normalize_url
from validate_dataset import REQUIRED_COLUMNS, render_summary, validate_rows


def make_row(
    record_id: str,
    original_url: str,
    normalized_url: str,
    label: str,
) -> dict[str, str]:
    return {
        "record_id": record_id,
        "original_url": original_url,
        "normalized_url": normalized_url,
        "label": label,
        "source": "synthetic-test",
        "evidence": "synthetic only; no real URL or verdict",
        "collected_at": "2026-01-01T00:00:00Z",
        "verified_at": "",
        "registrable_domain": "fake.test",
    }


class NormalizeURLTests(unittest.TestCase):
    def test_normalizes_scheme_hostname_and_default_port(self) -> None:
        self.assertEqual(
            normalize_url("HTTPS://FAKE-EXAMPLE.TEST:443/a%2Fb?q=FAKE"),
            "https://fake-example.test/a%2Fb?q=FAKE",
        )

    def test_normalizes_idna_hostname_and_preserves_query(self) -> None:
        self.assertEqual(
            normalize_url("https://BÜCHER.test:443/path?x=one%2Ftwo&y=FAKE"),
            "https://xn--bcher-kva.test/path?x=one%2Ftwo&y=FAKE",
        )

    def test_removes_http_default_port_and_preserves_path(self) -> None:
        self.assertEqual(
            normalize_url("http://fake.test:80/a/../b?x=1"),
            "http://fake.test/a/../b?x=1",
        )

    def test_rejects_missing_scheme_and_unsupported_scheme(self) -> None:
        for value in ("fake.test/path", "ftp://fake.test/path"):
            with self.subTest(value=value), self.assertRaises(URLNormalizationError):
                normalize_url(value)

    def test_rejects_malformed_authority(self) -> None:
        for value in ("https://[broken.test/", "https://fake.test:99999/"):
            with self.subTest(value=value), self.assertRaises(URLNormalizationError):
                normalize_url(value)


class ValidateRowsTests(unittest.TestCase):
    def test_accepts_valid_binary_and_unknown_rows(self) -> None:
        rows = [
            make_row(
                "fake-1",
                "https://fake-one.test/a?token=FAKE",
                "https://fake-one.test/a?token=FAKE",
                "phishing",
            ),
            make_row(
                "fake-2",
                "https://fake-two.test/",
                "https://fake-two.test/",
                "unknown",
            ),
        ]
        rows[0]["verified_at"] = "2026-01-02T00:00:00Z"
        summary = validate_rows(list(REQUIRED_COLUMNS), rows)
        self.assertFalse(summary["has_errors"])
        self.assertEqual(summary["binary_training_row_count"], 1)
        self.assertEqual(summary["unknown_row_count"], 1)
        self.assertFalse(summary["unknown_rows_are_binary_training_eligible"])

    def test_flags_missing_values_and_malformed_urls(self) -> None:
        row = make_row("fake-1", "https://[broken.test/", "", "phishing")
        row["evidence"] = ""
        summary = validate_rows(list(REQUIRED_COLUMNS), [row])
        self.assertTrue(summary["has_errors"])
        self.assertEqual(summary["malformed_urls"][0]["row"], 2)
        self.assertEqual(summary["missing_values"]["evidence"], 1)

    def test_binary_label_requires_verification_timestamp(self) -> None:
        row = make_row(
            "fake-1",
            "https://fake-one.test/",
            "https://fake-one.test/",
            "benign",
        )
        summary = validate_rows(list(REQUIRED_COLUMNS), [row])
        self.assertEqual(summary["blocking_missing_values"]["verified_at"], 1)
        self.assertTrue(summary["has_errors"])

    def test_flags_exact_and_normalized_duplicates_and_label_conflicts(self) -> None:
        first = make_row(
            "fake-1",
            "HTTPS://FAKE.test:443/a?x=FAKE",
            "https://fake.test/a?x=FAKE",
            "phishing",
        )
        second = make_row(
            "fake-2",
            "https://fake.test/a?x=FAKE",
            "https://fake.test/a?x=FAKE",
            "benign",
        )
        summary = validate_rows(list(REQUIRED_COLUMNS), [first, second])
        self.assertEqual(summary["exact_duplicate_url_row_count"], 0)
        self.assertEqual(summary["normalized_duplicate_group_count"], 1)
        self.assertEqual(len(summary["conflicting_label_groups"]), 1)
        self.assertTrue(summary["has_errors"])

    def test_summary_never_prints_url_path_or_query_value(self) -> None:
        row = make_row(
            "fake-1",
            "https://fake.test/private-path?secret=DO_NOT_PRINT",
            "https://fake.test/private-path?secret=DO_NOT_PRINT",
            "unknown",
        )
        summary = render_summary(validate_rows(list(REQUIRED_COLUMNS), [row]))
        self.assertNotIn("private-path", summary)
        self.assertNotIn("DO_NOT_PRINT", summary)
        self.assertNotIn("secret", summary)

    def test_missing_required_column_is_reported(self) -> None:
        fields = [column for column in REQUIRED_COLUMNS if column != "evidence"]
        summary = validate_rows(fields, [])
        self.assertEqual(summary["missing_columns"], ["evidence"])
        self.assertTrue(summary["has_errors"])


if __name__ == "__main__":
    unittest.main()
