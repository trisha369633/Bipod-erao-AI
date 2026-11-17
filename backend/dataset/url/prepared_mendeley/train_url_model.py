"""Derive offline registrable-domain groups and train the URL baseline."""

from __future__ import annotations

import csv
import gzip
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

import joblib
import numpy as np
import sklearn
import tldextract
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline

DATA_DIRECTORY = Path(__file__).resolve().parent
MODEL_DIRECTORY = DATA_DIRECTORY.parents[2] / "trained_model"
INPUT_CSV = DATA_DIRECTORY / "prepared_urls.csv.gz"
DOMAIN_CSV = DATA_DIRECTORY / "prepared_urls_with_domains.csv.gz"
UNRESOLVED_CSV = DATA_DIRECTORY / "unresolved_registrable_domains.csv"
MODEL_PATH = MODEL_DIRECTORY / "url_phishing_char_tfidf_logreg.joblib"
REPORT_JSON = MODEL_DIRECTORY / "url_phishing_evaluation.json"
REPORT_MARKDOWN = MODEL_DIRECTORY / "url_phishing_model_report.md"
RANDOM_STATE = 42
TEST_SIZE = 0.2
LABELS = ["legitimate", "phishing"]
PSL_EXTRACTOR = tldextract.TLDExtract(
    suffix_list_urls=(),
    cache_dir=None,
    fallback_to_snapshot=True,
    include_psl_private_domains=True,
)


def main() -> None:
    MODEL_DIRECTORY.mkdir(parents=True, exist_ok=True)
    with gzip.open(INPUT_CSV, "rt", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not {
            "record_id",
            "normalized_url",
            "label",
            "source",
        }.issubset(reader.fieldnames):
            raise ValueError(f"Unexpected prepared dataset schema: {INPUT_CSV}")
        source_fields = list(reader.fieldnames)
        rows = list(reader)

    enriched_rows: list[dict[str, str]] = []
    unresolved_rows: list[dict[str, str]] = []
    for row_number, row in enumerate(rows, start=2):
        hostname = urlsplit(row["normalized_url"]).hostname or ""
        extracted = PSL_EXTRACTOR(hostname)
        registrable_domain = extracted.top_domain_under_public_suffix
        row["registrable_domain"] = registrable_domain
        enriched_rows.append(row)
        if not registrable_domain:
            unresolved_rows.append(
                {
                    "record_id": row["record_id"],
                    "source": row["source"],
                    "hostname": hostname,
                    "prepared_csv_row": str(row_number),
                    "reason": "Bundled PSL snapshot returned no registrable domain.",
                }
            )

    with gzip.open(DOMAIN_CSV, "wt", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=[*source_fields, "registrable_domain"]
        )
        writer.writeheader()
        writer.writerows(enriched_rows)
    with UNRESOLVED_CSV.open("w", encoding="utf-8", newline="") as stream:
        columns = (
            "record_id",
            "source",
            "hostname",
            "prepared_csv_row",
            "reason",
        )
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(unresolved_rows)

    trainable_rows = [
        row for row in enriched_rows if row["registrable_domain"]
    ]
    unknown_labels = sorted({row["label"] for row in trainable_rows} - set(LABELS))
    if unknown_labels:
        raise ValueError(f"Unexpected labels in dataset: {unknown_labels}")
    if not trainable_rows:
        raise ValueError("No rows have a registrable domain; refusing to train.")

    urls = np.asarray([row["normalized_url"] for row in trainable_rows], dtype=object)
    labels = np.asarray([row["label"] for row in trainable_rows], dtype=object)
    groups = np.asarray(
        [row["registrable_domain"] for row in trainable_rows], dtype=object
    )
    if set(labels) != set(LABELS):
        raise ValueError("Both phishing and legitimate rows are required.")

    splitter = GroupShuffleSplit(
        n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE
    )
    train_indices, test_indices = next(splitter.split(urls, labels, groups))
    train_groups = set(groups[train_indices])
    test_groups = set(groups[test_indices])
    if train_groups & test_groups:
        raise RuntimeError("Domain leakage detected between train and test splits.")
    if set(labels[train_indices]) != set(LABELS) or set(labels[test_indices]) != set(
        LABELS
    ):
        raise RuntimeError(
            "Grouped split does not contain both classes in train and test."
        )

    model = Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    analyzer="char",
                    ngram_range=(3, 5),
                    dtype=np.float32,
                    min_df=2,
                    max_features=500_000,
                    sublinear_tf=True,
                ),
            ),
            (
                "classifier",
                LogisticRegression(
                    solver="saga",
                    max_iter=1000,
                    tol=1e-3,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    model.fit(urls[train_indices], labels[train_indices])
    predictions = model.predict(urls[test_indices])

    class_report = classification_report(
        labels[test_indices],
        predictions,
        labels=LABELS,
        output_dict=True,
        zero_division=0,
    )
    metrics = {
        "accuracy": accuracy_score(labels[test_indices], predictions),
        "precision_phishing": precision_score(
            labels[test_indices], predictions, pos_label="phishing", zero_division=0
        ),
        "recall_phishing": recall_score(
            labels[test_indices], predictions, pos_label="phishing", zero_division=0
        ),
        "f1_phishing": f1_score(
            labels[test_indices], predictions, pos_label="phishing", zero_division=0
        ),
        "confusion_matrix_labels": LABELS,
        "confusion_matrix": confusion_matrix(
            labels[test_indices], predictions, labels=LABELS
        ).tolist(),
        "classification_report": class_report,
    }

    joblib.dump(model, MODEL_PATH, compress=3)
    report = {
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input_dataset": str(INPUT_CSV.relative_to(MODEL_DIRECTORY.parents[0])),
        "domain_dataset": str(DOMAIN_CSV.relative_to(MODEL_DIRECTORY.parents[0])),
        "registrable_domain_method": {
            "library": "tldextract",
            "version": "5.3.0",
            "psl": "bundled snapshot",
            "remote_fetching": False,
            "private_suffixes_included": True,
            "grouping_key": "registrable_domain",
        },
        "dataset": {
            "cleaned_rows": len(rows),
            "rows_with_registrable_domain": len(trainable_rows),
            "rows_without_registrable_domain": len(unresolved_rows),
            "unresolved_report": str(
                UNRESOLVED_CSV.relative_to(MODEL_DIRECTORY.parents[0])
            ),
            "label_counts_in_trainable_data": dict(Counter(labels.tolist())),
        },
        "split": {
            "method": "GroupShuffleSplit",
            "test_size_requested": TEST_SIZE,
            "random_state": RANDOM_STATE,
            "train_rows": len(train_indices),
            "test_rows": len(test_indices),
            "train_fraction": len(train_indices) / len(trainable_rows),
            "test_fraction": len(test_indices) / len(trainable_rows),
            "train_domains": len(train_groups),
            "test_domains": len(test_groups),
            "overlap_domains": len(train_groups & test_groups),
            "train_label_counts": dict(Counter(labels[train_indices].tolist())),
            "test_label_counts": dict(Counter(labels[test_indices].tolist())),
        },
        "model": {
            "input": "normalized_url",
            "vectorizer": {
                "class": "TfidfVectorizer",
                "analyzer": "char",
                "ngram_range": [3, 5],
                "min_df": 2,
                "max_features": 500_000,
                "sublinear_tf": True,
                "dtype": "float32",
            },
            "classifier": {
                "class": "LogisticRegression",
                "solver": "saga",
                "max_iter": 1000,
                "tol": 1e-3,
                "random_state": RANDOM_STATE,
            },
            "scikit_learn_version": sklearn.__version__,
        },
        "metrics": metrics,
        "artifacts": {
            "model": str(MODEL_PATH.relative_to(MODEL_DIRECTORY.parents[0])),
            "evaluation_json": str(
                REPORT_JSON.relative_to(MODEL_DIRECTORY.parents[0])
            ),
            "evaluation_report": str(
                REPORT_MARKDOWN.relative_to(MODEL_DIRECTORY.parents[0])
            ),
        },
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MARKDOWN.write_text(_render_report(report), encoding="utf-8")
    print(json.dumps(report, indent=2))


def _render_report(report: dict[str, object]) -> str:
    dataset = report["dataset"]
    split = report["split"]
    metrics = report["metrics"]
    model = report["model"]
    assert isinstance(dataset, dict)
    assert isinstance(split, dict)
    assert isinstance(metrics, dict)
    assert isinstance(model, dict)
    confusion = metrics["confusion_matrix"]
    class_report = metrics["classification_report"]
    lines = [
        "# URL Phishing Baseline Evaluation",
        "",
        f"- Trained at: `{report['trained_at']}`",
        f"- Cleaned records: {dataset['cleaned_rows']:,}",
        f"- Rows with registrable domains: {dataset['rows_with_registrable_domain']:,}",
        f"- Rows without registrable domains: {dataset['rows_without_registrable_domain']:,}",
        f"- Train/test split: {split['train_rows']:,} / {split['test_rows']:,}",
        f"- Actual test fraction: {split['test_fraction']:.4f}",
        f"- Domain groups, train/test: {split['train_domains']:,} / {split['test_domains']:,}",
        f"- Domain overlap: {split['overlap_domains']}",
        f"- Split strategy: `{split['method']}` grouped by registrable domain",
        "- PSL: `tldextract==5.3.0` bundled snapshot, offline, private suffixes included",
        "",
        "## Model",
        "",
        f"- Features: character TF-IDF n-grams {model['vectorizer']['ngram_range']}",
        f"- Logistic Regression: solver `{model['classifier']['solver']}`, max_iter `{model['classifier']['max_iter']}`",
        "",
        "## Held-out test metrics",
        "",
        f"- Accuracy: {metrics['accuracy']:.4f}",
        f"- Precision (phishing): {metrics['precision_phishing']:.4f}",
        f"- Recall (phishing): {metrics['recall_phishing']:.4f}",
        f"- F1 (phishing): {metrics['f1_phishing']:.4f}",
        "",
        "### Confusion matrix",
        "",
        "Rows are true labels; columns are predicted labels. Order: `legitimate`, `phishing`.",
        "",
        f"| | Predicted legitimate | Predicted phishing |",
        f"|---|---:|---:|",
        f"| True legitimate | {confusion[0][0]:,} | {confusion[0][1]:,} |",
        f"| True phishing | {confusion[1][0]:,} | {confusion[1][1]:,} |",
        "",
        "### Per-class classification report",
        "",
        "| Class | Precision | Recall | F1 | Support |",
        "|---|---:|---:|---:|---:|",
    ]
    for label in LABELS:
        row = class_report[label]
        lines.append(
            f"| {label} | {row['precision']:.4f} | {row['recall']:.4f} | "
            f"{row['f1-score']:.4f} | {row['support']:,} |"
        )
    lines.extend(
        [
            "",
            "## Registrable-domain extraction",
            "",
            f"Records without a registrable domain are listed by record ID and hostname in "
            f"`{dataset['unresolved_report']}`. They were excluded from the split and training set.",
            "",
            "This is a baseline trained on publisher-provided labels; it is not evidence that the underlying URL labels were independently verified.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
