"""Validate a staged URL dataset and write a URL-redacted summary report."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from normalize_url import URLNormalizationError, normalize_url

REQUIRED_COLUMNS = (
    "record_id",
    "original_url",
    "normalized_url",
    "label",
    "source",
    "evidence",
    "collected_at",
    "verified_at",
    "registrable_domain",
)
VALID_LABELS = {"phishing", "benign", "unknown"}
DATA_DIRECTORY = Path(__file__).resolve().parent


def _is_missing(value: str | None) -> bool:
    return value is None or not value.strip()


def validate_rows(
    fieldnames: list[str] | None, rows: list[dict[str, str]]
) -> dict[str, Any]:
    """Validate parsed CSV rows without including URL strings in the result."""
    fields = fieldnames or []
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in fields]
    missing_values: dict[str, int] = {column: 0 for column in REQUIRED_COLUMNS}
    blocking_missing_values: dict[str, int] = defaultdict(int)
    required_value_columns = {
        "record_id",
        "original_url",
        "label",
        "source",
        "evidence",
        "collected_at",
    }
    malformed_urls: list[dict[str, Any]] = []
    normalization_mismatches: list[int] = []
    invalid_labels: list[dict[str, Any]] = []
    exact_url_rows: dict[str, list[int]] = defaultdict(list)
    normalized_url_rows: dict[str, list[tuple[int, str]]] = defaultdict(list)
    exact_row_keys: dict[str, list[int]] = defaultdict(list)

    for row_number, row in enumerate(rows, start=2):
        for column in REQUIRED_COLUMNS:
            value = row.get(column)
            if _is_missing(value):
                missing_values[column] += 1
                if column in required_value_columns:
                    blocking_missing_values[column] += 1

        original_url = row.get("original_url", "")
        normalized_value = row.get("normalized_url", "")
        label = row.get("label", "")

        if not _is_missing(original_url):
            exact_url_rows[original_url].append(row_number)
            try:
                computed = normalize_url(original_url)
            except URLNormalizationError as exc:
                malformed_urls.append({"row": row_number, "reason": str(exc)})
            else:
                normalized_url_rows[computed].append((row_number, label))
                if _is_missing(normalized_value) or normalized_value != computed:
                    normalization_mismatches.append(row_number)

        if label in {"phishing", "benign"} and _is_missing(row.get("verified_at")):
            blocking_missing_values["verified_at"] += 1

        if not _is_missing(label) and label not in VALID_LABELS:
            invalid_labels.append({"row": row_number, "label": label})

        # Stable row identity check excludes the CSV's physical line number.
        exact_key = json.dumps(
            [row.get(column, "") for column in fields],
            ensure_ascii=False,
            separators=(",", ":"),
        )
        exact_row_keys[exact_key].append(row_number)

    exact_duplicate_groups = [
        row_numbers for row_numbers in exact_url_rows.values() if len(row_numbers) > 1
    ]
    exact_duplicate_rows = sum(len(group) - 1 for group in exact_duplicate_groups)
    duplicate_row_groups = [
        row_numbers for row_numbers in exact_row_keys.values() if len(row_numbers) > 1
    ]
    duplicate_rows = sum(len(group) - 1 for group in duplicate_row_groups)
    normalized_duplicate_groups = [
        observations
        for observations in normalized_url_rows.values()
        if len(observations) > 1
    ]
    normalized_duplicate_rows = sum(
        len(group) - 1 for group in normalized_duplicate_groups
    )
    conflicting_labels = []
    for observations in normalized_duplicate_groups:
        labels = sorted({label for _, label in observations if label in VALID_LABELS})
        if len(labels) > 1:
            conflicting_labels.append(
                {
                    "rows": [row_number for row_number, _ in observations],
                    "labels": labels,
                }
            )

    summary = {
        "row_count": len(rows),
        "columns": fields,
        "missing_columns": missing_columns,
        "missing_values": missing_values,
        "blocking_missing_values": dict(blocking_missing_values),
        "invalid_labels": invalid_labels,
        "malformed_urls": malformed_urls,
        "normalization_mismatch_rows": normalization_mismatches,
        "exact_duplicate_row_count": duplicate_rows,
        "exact_duplicate_url_row_count": exact_duplicate_rows,
        "normalized_duplicate_group_count": len(normalized_duplicate_groups),
        "normalized_duplicate_row_count": normalized_duplicate_rows,
        "conflicting_label_groups": conflicting_labels,
        "binary_training_row_count": sum(
            1 for row in rows if row.get("label") in {"phishing", "benign"}
        ),
        "unknown_row_count": sum(1 for row in rows if row.get("label") == "unknown"),
        "unknown_rows_are_binary_training_eligible": False,
    }
    summary["has_errors"] = bool(
        missing_columns
        or blocking_missing_values
        or invalid_labels
        or malformed_urls
        or normalization_mismatches
        or conflicting_labels
    )
    return summary


def render_summary(summary: dict[str, Any]) -> str:
    """Render a Markdown report that contains no URL paths or query values."""
    lines = [
        "# URL Dataset Validation Summary",
        "",
        "This report contains aggregate counts and row numbers only; URL values, paths, and query parameters are omitted.",
        "",
        f"- Rows: {summary['row_count']}",
        f"- Exact duplicate rows: {summary['exact_duplicate_row_count']}",
        f"- Repeated exact original URLs (extra rows): {summary['exact_duplicate_url_row_count']}",
        f"- Normalized duplicate groups: {summary['normalized_duplicate_group_count']}",
        f"- Normalized duplicate extra rows: {summary['normalized_duplicate_row_count']}",
        f"- Binary-label rows (`phishing` or `benign`): {summary['binary_training_row_count']}",
        f"- `unknown` rows (excluded from binary training): {summary['unknown_row_count']}",
        "",
        "## Schema and missing values",
        "",
        f"- Missing required columns: {', '.join(summary['missing_columns']) or 'none'}",
        "",
        "| Column | Missing rows |",
        "|---|---:|",
    ]
    lines.extend(
        f"| `{column}` | {count} |"
        for column, count in summary["missing_values"].items()
    )

    lines.extend(["", "## Validation findings", ""])
    if not summary["has_errors"]:
        lines.append("No blocking schema, missing-value, label, URL, normalization, or conflicting-label errors found.")
    else:
        lines.append("Review the findings below before using this file.")

    lines.extend(
        [
            "",
            "- Required-value errors: "
            + (
                ", ".join(
                    f"{column} ({count})"
                    for column, count in summary["blocking_missing_values"].items()
                )
                or "none"
            ),
            f"- Invalid label rows: {_row_numbers(summary['invalid_labels'])}",
            f"- Malformed URL rows: {_row_numbers(summary['malformed_urls'])}",
            f"- Normalization mismatch rows: {_row_numbers(summary['normalization_mismatch_rows'])}",
            f"- Conflicting normalized URL label groups: {len(summary['conflicting_label_groups'])}",
        ]
    )
    for group in summary["conflicting_label_groups"]:
        lines.append(
            f"  - Rows {', '.join(map(str, group['rows']))}: labels "
            f"`{', '.join(group['labels'])}`; manual review required."
        )
    lines.extend(
        [
            "",
            "## Training eligibility",
            "",
            "`unknown` records are not binary training/evaluation examples. This validator does not determine whether any label is true, verify evidence or permissions, fetch URLs, or follow redirects.",
            "",
        ]
    )
    return "\n".join(lines)


def _row_numbers(items: list[Any]) -> str:
    if not items:
        return "none"
    if isinstance(items[0], int):
        return ", ".join(map(str, items))
    return ", ".join(str(item["row"]) for item in items)


def _path_inside_data_directory(value: str) -> Path:
    path = Path(value).expanduser().resolve()
    try:
        path.relative_to(DATA_DIRECTORY)
    except ValueError as exc:
        raise ValueError(f"Path must be inside {DATA_DIRECTORY}.") from exc
    return path


def validate_file(input_path: Path) -> dict[str, Any]:
    """Load a staged CSV and return validation findings without logging row data."""
    path = _path_inside_data_directory(str(input_path))
    if path == (DATA_DIRECTORY.parent.parent / "Phishing URLs.csv").resolve():
        raise ValueError("The provenance_unverified legacy dataset is not an allowed input.")
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            return validate_rows([], [])
        rows = list(reader)
        return validate_rows(reader.fieldnames, rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", help="CSV staged inside backend/dataset/url/")
    parser.add_argument(
        "--report",
        default=str(DATA_DIRECTORY / "validation_summary.md"),
        help="summary Markdown path inside backend/dataset/url/",
    )
    args = parser.parse_args(argv)
    try:
        input_path = _path_inside_data_directory(args.input)
        report_path = _path_inside_data_directory(args.report)
        summary = validate_file(input_path)
        report_path.write_text(render_summary(summary), encoding="utf-8")
    except (OSError, ValueError, csv.Error) as exc:
        print(f"Validation could not run: {exc}", file=sys.stderr)
        return 2

    print(
        f"Validated {summary['row_count']} rows; "
        f"{summary['unknown_row_count']} unknown rows excluded from binary targets. "
        f"Summary: {report_path}"
    )
    return 1 if summary["has_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
