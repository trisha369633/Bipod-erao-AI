"""Prepare a source-attributed staging copy of the Mendeley URL CSVs."""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

URL_DIRECTORY = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = Path(__file__).resolve().parent
NORMALIZER_DIRECTORY = URL_DIRECTORY
sys.path.insert(0, str(NORMALIZER_DIRECTORY))

from normalize_url import URLNormalizationError, normalize_url  # noqa: E402

SOURCES = (
    {
        "path": URL_DIRECTORY.parent.parent / "URL dataset.csv",
        "filename": "URL dataset.csv",
        "url_column": "url",
        "label_column": "type",
    },
    {
        "path": URL_DIRECTORY.parent.parent / "Phishing URLs.csv",
        "filename": "Phishing URLs.csv",
        "url_column": "url",
        "label_column": "Type",
    },
)
PREPARED_COLUMNS = (
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
INVALID_COLUMNS = (
    "source",
    "source_row",
    "original_url",
    "source_label",
    "quarantine_reason",
)
CONFLICT_COLUMNS = (
    "source",
    "source_row",
    "original_url",
    "normalized_url",
    "source_label",
    "normalized_label",
    "quarantine_reason",
)
LABEL_MAP = {"phishing": "phishing", "legitimate": "legitimate"}
DOI = "10.17632/vfszbj9b36.1"
LICENSE = "CC BY 4.0"


def _read_sources() -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    observations: list[dict[str, Any]] = []
    stats: dict[str, dict[str, int]] = {}
    for source in SOURCES:
        rows: list[dict[str, str]] = []
        with source["path"].open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames or not {
                source["url_column"],
                source["label_column"],
            }.issubset(reader.fieldnames):
                raise ValueError(f"Unexpected columns in {source['filename']}.")
            rows.extend(reader)

        stats[source["filename"]] = {
            "original_rows": len(rows),
            "valid_rows": 0,
            "invalid_rows": 0,
            "invalid_reason_counts": Counter(),
            "exact_duplicate_groups": 0,
            "exact_duplicate_extra_rows": 0,
            "normalized_duplicate_groups": 0,
            "normalized_duplicate_extra_rows": 0,
            "retained_unique_records": 0,
        }
        for row_number, row in enumerate(rows, start=2):
            original_url = row.get(source["url_column"]) or ""
            source_label = (row.get(source["label_column"]) or "").strip()
            normalized_label = LABEL_MAP.get(source_label.casefold())
            if normalized_label is None:
                raise ValueError(
                    f"Unexpected label in {source['filename']} row {row_number}."
                )
            try:
                normalized_url = normalize_url(original_url)
            except URLNormalizationError as exc:
                stats[source["filename"]]["invalid_rows"] += 1
                stats[source["filename"]]["invalid_reason_counts"][str(exc)] += 1
                observations.append(
                    {
                        "kind": "invalid",
                        "source": source["filename"],
                        "source_row": row_number,
                        "original_url": original_url,
                        "source_label": source_label,
                        "reason": str(exc),
                    }
                )
                continue

            stats[source["filename"]]["valid_rows"] += 1
            observations.append(
                {
                    "kind": "valid",
                    "source": source["filename"],
                    "source_row": row_number,
                    "original_url": original_url,
                    "normalized_url": normalized_url,
                    "source_label": source_label,
                    "label": normalized_label,
                }
            )
    return observations, stats


def _write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, Any]]) -> None:
    if path.suffix == ".gz":
        stream = gzip.open(path, "wt", encoding="utf-8", newline="")
    else:
        stream = path.open("w", encoding="utf-8", newline="")
    with stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def prepare() -> dict[str, Any]:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    observations, source_stats = _read_sources()
    valid = [item for item in observations if item["kind"] == "valid"]
    invalid_rows = [
        {
            "source": item["source"],
            "source_row": item["source_row"],
            "original_url": item["original_url"],
            "source_label": item["source_label"],
            "quarantine_reason": item["reason"],
        }
        for item in observations
        if item["kind"] == "invalid"
    ]

    raw_counts_by_source: dict[str, Counter[str]] = defaultdict(Counter)
    normalized_by_source: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in valid:
        raw_counts_by_source[item["source"]][item["original_url"]] += 1
        normalized_by_source[item["source"]][item["normalized_url"]].append(item)
        grouped[item["normalized_url"]].append(item)

    for filename, counts in raw_counts_by_source.items():
        source_stats[filename]["exact_duplicate_groups"] = sum(
            1 for count in counts.values() if count > 1
        )
        source_stats[filename]["exact_duplicate_extra_rows"] = sum(
            count - 1 for count in counts.values() if count > 1
        )
        source_stats[filename]["normalized_duplicate_groups"] = sum(
            1 for items in normalized_by_source[filename].values() if len(items) > 1
        )
        source_stats[filename]["normalized_duplicate_extra_rows"] = sum(
            len(items) - 1
            for items in normalized_by_source[filename].values()
            if len(items) > 1
        )

    conflicts: list[dict[str, Any]] = []
    prepared_rows: list[dict[str, Any]] = []
    final_labels: Counter[str] = Counter()
    final_source_counts: Counter[str] = Counter()
    agreeing_duplicate_groups = 0
    agreeing_duplicate_extra_rows = 0
    cross_source_duplicate_groups = 0

    collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
        "+00:00", "Z"
    )
    for normalized_url, items in grouped.items():
        labels = {item["label"] for item in items}
        if len(labels) > 1:
            for item in items:
                conflicts.append(
                    {
                        "source": item["source"],
                        "source_row": item["source_row"],
                        "original_url": item["original_url"],
                        "normalized_url": normalized_url,
                        "source_label": item["source_label"],
                        "normalized_label": item["label"],
                        "quarantine_reason": "Conflicting labels for normalized URL.",
                    }
                )
            continue

        if len(items) > 1:
            agreeing_duplicate_groups += 1
            agreeing_duplicate_extra_rows += len(items) - 1
        source_names = sorted({item["source"] for item in items})
        if len(source_names) > 1:
            cross_source_duplicate_groups += 1
        for name in source_names:
            source_stats[name]["retained_unique_records"] += 1
            final_source_counts[name] += 1

        label = next(iter(labels))
        source_evidence = [
            {
                "source_file": item["source"],
                "source_row": item["source_row"],
                "publisher_label": item["source_label"],
                "doi": DOI,
                "license": LICENSE,
                "independently_verified": False,
            }
            for item in sorted(items, key=lambda value: (value["source"], value["source_row"]))
        ]
        record_id = "url-" + hashlib.sha256(
            normalized_url.encode("utf-8")
        ).hexdigest()
        prepared_rows.append(
            {
                "record_id": record_id,
                "original_url": items[0]["original_url"],
                "normalized_url": normalized_url,
                "label": label,
                "source": "; ".join(source_names),
                "evidence": json.dumps(
                    {"source_observations": source_evidence},
                    ensure_ascii=False,
                    separators=(",", ":"),
                ),
                "collected_at": collected_at,
                "verified_at": "",
                "registrable_domain": "",
            }
        )
        final_labels[label] += 1

    prepared_rows.sort(key=lambda row: row["normalized_url"])
    invalid_rows.sort(key=lambda row: (row["source"], row["source_row"]))
    conflicts.sort(key=lambda row: (row["normalized_url"], row["source"], row["source_row"]))
    _write_csv(
        OUTPUT_DIRECTORY / "prepared_urls.csv.gz", PREPARED_COLUMNS, prepared_rows
    )
    _write_csv(
        OUTPUT_DIRECTORY / "quarantine_invalid_urls.csv", INVALID_COLUMNS, invalid_rows
    )
    _write_csv(
        OUTPUT_DIRECTORY / "quarantine_label_conflicts.csv",
        CONFLICT_COLUMNS,
        conflicts,
    )

    return {
        "collected_at": collected_at,
        "source_stats": source_stats,
        "original_rows": sum(item["original_rows"] for item in source_stats.values()),
        "valid_rows": sum(item["valid_rows"] for item in source_stats.values()),
        "invalid_rows": len(invalid_rows),
        "prepared_rows": len(prepared_rows),
        "valid_normalized_duplicate_extra_rows": sum(
            len(items) - 1 for items in grouped.values() if len(items) > 1
        ),
        "conflict_groups": len(
            {
                item["normalized_url"]
                for item in conflicts
            }
        ),
        "conflict_rows": len(conflicts),
        "agreeing_duplicate_groups": agreeing_duplicate_groups,
        "agreeing_duplicate_extra_rows": agreeing_duplicate_extra_rows,
        "cross_source_duplicate_groups": cross_source_duplicate_groups,
        "final_labels": dict(final_labels),
        "final_source_counts": dict(final_source_counts),
    }


def _write_readme(summary: dict[str, Any]) -> None:
    readme = f"""# Prepared Mendeley URL Dataset

This is a source-attributed staging dataset prepared from the two original CSVs
listed below. The originals were read only and were not changed.

## Attribution and license

Mendeley Data, **Phishing URL dataset**, DOI
[10.17632/vfszbj9b36.1](https://doi.org/10.17632/vfszbj9b36.1), version 1.
License: **CC BY 4.0**. Cite the Mendeley Data record and retain this attribution
when reusing or redistributing the prepared data.

Original filenames:

- `URL dataset.csv` — columns `url`, `type`; source labels `phishing` and `legitimate`.
- `Phishing URLs.csv` — columns `url`, `Type`; all source labels `Phishing`.

Both files are attributed to the same Mendeley Data DOI. The `source` field in
the prepared CSV retains the filename(s) contributing each deduplicated record;
the `evidence` field preserves source row references and publisher-provided
labels. Repeated URLs from both files are represented once, with both sources
retained.

## Preparation details

- Labels are standardized to exactly `phishing` and `legitimate`.
- URLs were normalized offline using the project's existing `normalize_url.py`.
  No URL was fetched and no redirect was followed.
- Unnormalizable rows are retained in `quarantine_invalid_urls.csv`.
- Conflicting normalized URL labels would be retained in
  `quarantine_label_conflicts.csv`; no such conflicts were found in this run.
- `collected_at` records the UTC time this staging copy was prepared.
- `verified_at` is blank because the source files do not provide per-URL
  verification timestamps; none were invented.
- `registrable_domain` is blank because this pipeline has no pinned Public
  Suffix List data and does not guess registrable domains.
- The publisher's labels are preserved as source claims; they have not been
  independently verified. This staging output is not model training approval.
- No message dataset or message-level label was used.

## Files

- `prepared_urls.csv.gz` — losslessly compressed, normalized, deduplicated records.
- `prepared_urls_with_domains.csv.gz` — compressed domain-enriched records generated
  by `train_url_model.py`.
- `quarantine_invalid_urls.csv` — every input row rejected by the normalizer.
- `quarantine_label_conflicts.csv` — all observations in any conflicting-label
  normalized URL group.
- `preparation_report.md` — detailed aggregate preparation counts and output
  paths; it does not print URL values.
- `validation_summary.md` — output of the existing URL dataset validator.
- `prepare_dataset.py` — reproducible local preparation utility.
- `compress_prepared_csvs.py` — streaming, lossless compressor; preserves source
  files unless run with `--replace-originals`.

## Lossless compression

Run `python3 compress_prepared_csvs.py` to create verified `.csv.gz` copies
while retaining the original CSVs. Add `--replace-originals` to remove each
uncompressed CSV only after its compressed copy is verified byte-for-byte and
is below 100 MB. No rows, columns, or cell values are changed.

The existing validator's accepted labels are `phishing`, `benign`, and
`unknown`, and it requires `verified_at` for binary labels. This prepared file
intentionally uses the requested publisher-aligned `legitimate` label and
leaves unavailable verification timestamps blank. Therefore, the existing
validator is expected to flag those schema/verification mismatches; do not
silently rewrite labels or fabricate timestamps to make the check pass.
"""
    (OUTPUT_DIRECTORY / "README.md").write_text(readme, encoding="utf-8")


def _write_report(summary: dict[str, Any]) -> None:
    source_lines = [
        "| Original source file | Input rows | Valid rows | Invalid rows | Exact duplicate groups / extra rows | Normalized duplicate groups / extra rows | Final unique records carrying source |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for filename, stats in summary["source_stats"].items():
        source_lines.append(
            "| `{}` | {:,} | {:,} | {:,} | {} / {} | {} / {} | {:,} |".format(
                filename,
                stats["original_rows"],
                stats["valid_rows"],
                stats["invalid_rows"],
                stats["exact_duplicate_groups"],
                stats["exact_duplicate_extra_rows"],
                stats["normalized_duplicate_groups"],
                stats["normalized_duplicate_extra_rows"],
                stats["retained_unique_records"],
            )
        )

    invalid_lines = []
    for filename, stats in summary["source_stats"].items():
        for reason, count in sorted(stats["invalid_reason_counts"].items()):
            invalid_lines.append(f"| `{filename}` | {reason} | {count:,} |")
    if not invalid_lines:
        invalid_lines.append("| — | None | 0 |")

    report = f"""# URL Dataset Preparation Report

**Prepared at:** `{summary['collected_at']}`  
**Attribution:** Mendeley Data, *Phishing URL dataset*, DOI
[10.17632/vfszbj9b36.1](https://doi.org/10.17632/vfszbj9b36.1), CC BY 4.0.

## Input and row counts

| Metric | Count |
|---|---:|
| Total original rows | {summary['original_rows']:,} |
| Valid and normalizable input rows | {summary['valid_rows']:,} |
| Invalid/unnormalizable rows quarantined | {summary['invalid_rows']:,} |
| Valid normalized duplicate extra rows removed | {summary['valid_normalized_duplicate_extra_rows']:,} |
| Conflicting normalized URL groups | {summary['conflict_groups']:,} |
| Observations placed in conflict quarantine | {summary['conflict_rows']:,} |
| Agreeing-label duplicate groups collapsed | {summary['agreeing_duplicate_groups']:,} |
| Agreeing-label duplicate extra rows collapsed | {summary['agreeing_duplicate_extra_rows']:,} |
| Cross-source normalized URL groups retained once | {summary['cross_source_duplicate_groups']:,} |
| Final prepared records | {summary['prepared_rows']:,} |

## Per-source counts

{chr(10).join(source_lines)}

Source-wise final record counts can overlap: a deduplicated record shared by
both source files is counted under both sources because both attributions are
preserved.

### Normalizer rejection reasons

| Source file | Reason | Rows |
|---|---|---:|
{chr(10).join(invalid_lines)}

## Final label distribution

| Standardized label | Records |
|---|---:|
| `phishing` | {summary['final_labels'].get('phishing', 0):,} |
| `legitimate` | {summary['final_labels'].get('legitimate', 0):,} |

Labels are standardized from the publishers' recorded values, not independently
verified URL verdicts. The source `Phishing URLs.csv` records the publisher
label `Phishing`; `URL dataset.csv` records `phishing` or `legitimate`.

## Deduplication and quarantine

All valid input URLs were normalized with the existing offline normalizer and
grouped by normalized URL. When labels agreed, one record was retained and its
`source`/`evidence` fields preserve the contributing source files and source row
references. If labels conflicted, every observation in that normalized group
was placed in the conflict quarantine, without selecting a label. No
conflicting groups were found. Invalid inputs were written to quarantine with
their original value and normalizer reason; none were silently discarded.

No source acquisition/collection or per-URL verification timestamp was supplied
in these files. `collected_at` is the staging preparation time; `verified_at`
is left blank rather than fabricated. `registrable_domain` is also blank
because no pinned Public Suffix List was used.

## Output files

- `backend/dataset/url/prepared_mendeley/prepared_urls.csv.gz`
- `backend/dataset/url/prepared_mendeley/quarantine_invalid_urls.csv`
- `backend/dataset/url/prepared_mendeley/quarantine_label_conflicts.csv`
- `backend/dataset/url/prepared_mendeley/README.md`
- `backend/dataset/url/prepared_mendeley/preparation_report.md`
- `backend/dataset/url/prepared_mendeley/validation_summary.md`
- `backend/dataset/url/prepared_mendeley/prepare_dataset.py`

## Validation limitation and readiness

The existing validator results describe the byte-identical CSV content before
gzip compression. It accepts binary labels `phishing` and `benign`, while this
task requires `phishing` and
`legitimate`; it also requires a `verified_at` timestamp for binary labels,
which neither source provides. The output preserves the requested labels and
does not invent verification timestamps, so validator findings on those
requirements must be interpreted as schema/provenance incompatibilities, not
as reasons to alter the labels or fabricate dates. See `validation_summary.md`.

No model was trained. Review the validator compatibility issue and the
publisher-supplied label provenance before treating this staging data as
training-ready.
"""
    (OUTPUT_DIRECTORY / "preparation_report.md").write_text(
        report, encoding="utf-8"
    )


if __name__ == "__main__":
    result = prepare()
    _write_readme(result)
    _write_report(result)
    print(json.dumps(result, indent=2, sort_keys=True))
