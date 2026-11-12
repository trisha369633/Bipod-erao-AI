"""Train and evaluate a TF-IDF/logistic-regression SMS baseline."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

import joblib
import matplotlib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.pipeline import FeatureUnion, Pipeline

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


LABELS = ["normal", "promo", "smish"]
SOURCES = ["Bengali", "English", "Banglish", "CodeMix"]
RANDOM_SEED = 42
CLASSIFIER_C_VALUES = [0.5, 1.0, 2.0]


def build_pipeline(classifier_c: float) -> Pipeline:
    """Create combined word/character TF-IDF features and a classifier."""
    features = FeatureUnion(
        [
            (
                "word_tfidf",
                TfidfVectorizer(
                    analyzer="word",
                    token_pattern=r"(?u)\b\w+\b",
                    ngram_range=(1, 2),
                    lowercase=True,
                    sublinear_tf=True,
                ),
            ),
            (
                "character_tfidf",
                TfidfVectorizer(
                    analyzer="char",
                    ngram_range=(2, 5),
                    lowercase=True,
                    sublinear_tf=True,
                ),
            ),
        ]
    )
    classifier = LogisticRegression(
        C=classifier_c,
        max_iter=1000,
        random_state=RANDOM_SEED,
    )
    return Pipeline([("features", features), ("classifier", classifier)])


def validate_split(data: pd.DataFrame, split_name: str) -> None:
    required = {"label", "text", "source"}
    if not required.issubset(data.columns):
        raise ValueError(f"{split_name} data must include label, text, and source.")
    if data.empty:
        raise ValueError(f"{split_name} data is empty.")
    if data["text"].isna().any() or data["text"].str.strip().eq("").any():
        raise ValueError(f"{split_name} data contains empty messages.")
    labels = set(data["label"])
    if labels != set(LABELS):
        raise ValueError(
            f"{split_name} labels must be exactly {LABELS}; found {sorted(labels)}."
        )
    if data["source"].isna().any() or data["source"].str.strip().eq("").any():
        raise ValueError(f"{split_name} data contains empty source values.")


def calculate_metrics(
    actual: pd.Series, predicted: np.ndarray
) -> dict[str, Any]:
    precision, recall, f1, support = precision_recall_fscore_support(
        actual,
        predicted,
        labels=LABELS,
        zero_division=0,
    )
    per_class = {
        label: {
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
            "support": int(support[index]),
        }
        for index, label in enumerate(LABELS)
    }
    return {
        "accuracy": float(accuracy_score(actual, predicted)),
        "macro_precision": float(
            precision_recall_fscore_support(
                actual, predicted, labels=LABELS, average="macro", zero_division=0
            )[0]
        ),
        "macro_recall": float(
            precision_recall_fscore_support(
                actual, predicted, labels=LABELS, average="macro", zero_division=0
            )[1]
        ),
        "macro_f1": float(f1_score(actual, predicted, labels=LABELS, average="macro")),
        "per_class": per_class,
        "confusion_matrix": confusion_matrix(
            actual, predicted, labels=LABELS
        ).tolist(),
    }


def evaluate_by_source(
    data: pd.DataFrame, predicted: np.ndarray
) -> dict[str, dict[str, Any]]:
    source_results: dict[str, dict[str, Any]] = {}
    source_values = sorted(set(data["source"]) | set(SOURCES))
    for source in source_values:
        positions = np.flatnonzero(data["source"].to_numpy() == source)
        if not len(positions):
            source_results[source] = {"support": 0, "metrics": None}
            continue
        actual = data["label"].iloc[positions]
        source_results[source] = {
            "support": int(len(positions)),
            "metrics": calculate_metrics(actual, predicted[positions]),
        }
    return source_results


def markdown_metric_table(
    metrics: dict[str, Any], include_support: bool = False
) -> str:
    columns = ["Label", "Precision", "Recall", "F1"]
    if include_support:
        columns.append("Support")
    lines = ["| " + " | ".join(columns) + " |", "|" + "|".join("---" for _ in columns) + "|"]
    for label in LABELS:
        result = metrics["per_class"][label]
        cells = [
            label,
            f"{result['precision']:.3f}",
            f"{result['recall']:.3f}",
            f"{result['f1']:.3f}",
        ]
        if include_support:
            cells.append(str(result["support"]))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def markdown_source_table(source_results: dict[str, dict[str, Any]]) -> str:
    lines = [
        "| Source | Rows | Accuracy | Macro Precision | Macro Recall | Macro F1 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for source, result in source_results.items():
        metrics = result["metrics"]
        if metrics is None:
            lines.append(f"| {source} | 0 | — | — | — | — |")
        else:
            lines.append(
                f"| {source} | {result['support']} | "
                f"{metrics['accuracy']:.3f} | {metrics['macro_precision']:.3f} | "
                f"{metrics['macro_recall']:.3f} | {metrics['macro_f1']:.3f} |"
            )
    return "\n".join(lines)


def markdown_confusion_matrix(matrix: list[list[int]]) -> str:
    lines = [
        "| Actual \\ Predicted | " + " | ".join(LABELS) + " |",
        "|---|" + "---:|" * len(LABELS),
    ]
    lines.extend(
        f"| {label} | " + " | ".join(str(value) for value in row) + " |"
        for label, row in zip(LABELS, matrix)
    )
    return "\n".join(lines)


def confusion_interpretation(matrix: list[list[int]]) -> str:
    errors = [
        (matrix[row][column], LABELS[row], LABELS[column])
        for row in range(len(LABELS))
        for column in range(len(LABELS))
        if row != column and matrix[row][column] > 0
    ]
    if not errors:
        return "No misclassifications occurred in this evaluation split."
    count, actual, predicted = max(errors)
    return (
        f"The largest off-diagonal count is {count} actual `{actual}` messages "
        f"predicted as `{predicted}`. Off-diagonal cells are errors; diagonal "
        "cells are correct predictions."
    )


def write_confusion_matrix(
    matrix: list[list[int]], output_path: Path, title: str
) -> None:
    figure, axis = plt.subplots(figsize=(7, 5.5))
    image = axis.imshow(matrix, interpolation="nearest", cmap="Blues")
    figure.colorbar(image, ax=axis, label="Message count")
    axis.set(
        xticks=np.arange(len(LABELS)),
        yticks=np.arange(len(LABELS)),
        xticklabels=LABELS,
        yticklabels=LABELS,
        xlabel="Predicted label",
        ylabel="Actual label",
        title=title,
    )
    threshold = max((max(row) for row in matrix), default=0) / 2
    for row in range(len(LABELS)):
        for column in range(len(LABELS)):
            axis.text(
                column,
                row,
                str(matrix[row][column]),
                ha="center",
                va="center",
                color="white" if matrix[row][column] > threshold else "#17345b",
            )
    figure.tight_layout()
    figure.savefig(output_path, dpi=160)
    plt.close(figure)


def make_report(
    train: pd.DataFrame,
    validation_metrics: dict[str, Any],
    validation_sources: dict[str, dict[str, Any]],
    test_metrics: dict[str, Any],
    test_sources: dict[str, dict[str, Any]],
    selected_c: float,
    tuning_results: list[dict[str, Any]],
) -> str:
    tuning_rows = "\n".join(
        f"| {row['C']} | {row['validation_macro_f1']:.4f} |"
        for row in tuning_results
    )
    return f"""# Bilingual Message Baseline Model Report

## Model architecture

- Word-level TF-IDF: unigrams and bigrams, Unicode-aware token pattern, lowercasing, and sublinear term frequency.
- Character-level TF-IDF: character n-grams from 2 to 5 characters, with sublinear term frequency.
- The word and character feature matrices are combined with `FeatureUnion`.
- Multiclass Logistic Regression predicts exactly `normal`, `promo`, or `smish`.
- The saved scikit-learn pipeline contains both vectorizers and the classifier.

The Unicode-aware word vectorizer retains Bengali word characters. Character n-grams provide complementary features for Bengali, English, Banglish, and CodeMix. No translation or stop-word removal is performed.

## Training details

- Training rows: {len(train)}
- Training labels: {json.dumps(train['label'].value_counts().sort_index().to_dict(), ensure_ascii=False)}
- Training sources: {json.dumps(train['source'].value_counts().sort_index().to_dict(), ensure_ascii=False)}
- Random seed: `{RANDOM_SEED}`
- Training used only `train.csv`.
- Candidate classifier C values were selected using validation macro F1; validation and test examples were not used to fit the model.
- Selected C: `{selected_c}`
- Test metrics were computed once after selecting the configuration.

| Candidate C | Validation macro F1 |
|---:|---:|
{tuning_rows}

## Validation metrics

- Accuracy: {validation_metrics['accuracy']:.4f}
- Macro precision: {validation_metrics['macro_precision']:.4f}
- Macro recall: {validation_metrics['macro_recall']:.4f}
- Macro F1: {validation_metrics['macro_f1']:.4f}

{markdown_metric_table(validation_metrics, include_support=True)}

### Validation performance by source

{markdown_source_table(validation_sources)}

### Validation confusion matrix

Rows are actual labels; columns are predicted labels.

{markdown_confusion_matrix(validation_metrics['confusion_matrix'])}

{confusion_interpretation(validation_metrics['confusion_matrix'])}

## Final test metrics

- Accuracy: {test_metrics['accuracy']:.4f}
- Macro precision: {test_metrics['macro_precision']:.4f}
- Macro recall: {test_metrics['macro_recall']:.4f}
- Macro F1: {test_metrics['macro_f1']:.4f}

{markdown_metric_table(test_metrics, include_support=True)}

### Test performance by source

{markdown_source_table(test_sources)}

### Test confusion matrix

Rows are actual labels; columns are predicted labels.

{markdown_confusion_matrix(test_metrics['confusion_matrix'])}

{confusion_interpretation(test_metrics['confusion_matrix'])}

The image `message_confusion_matrix.png` visualizes the held-out test confusion matrix.

## Limitations

- These results measure this specific dataset split and are not a guarantee of real-world scam detection.
- Source/language results use the dataset's existing `source` categories; they are not independently language-detected, and category counts differ.
- CodeMix and Banglish examples may overlap conceptually, and source labels may contain annotation noise.
- TF-IDF is based on token/character patterns; it does not understand context, intent, or newly emerging scam strategies.
- No external validation data or URL-classification task was used.
- The model has no calibrated or validated risk-percentage output; class predictions should not be presented as a probability of fraud.
"""


def train_and_evaluate() -> dict[str, Any]:
    backend_dir = Path(__file__).resolve().parents[2]
    processed_dir = backend_dir / "dataset" / "processed"
    output_dir = backend_dir / "trained_model"
    train = pd.read_csv(processed_dir / "train.csv", dtype=str, keep_default_na=False)
    validation = pd.read_csv(
        processed_dir / "validation.csv", dtype=str, keep_default_na=False
    )
    validate_split(train, "train")
    validate_split(validation, "validation")

    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    best_model: Pipeline | None = None
    best_validation_metrics: dict[str, Any] | None = None
    best_validation_predictions: np.ndarray | None = None
    selected_c: float | None = None
    tuning_results: list[dict[str, Any]] = []

    for classifier_c in CLASSIFIER_C_VALUES:
        model = build_pipeline(classifier_c)
        model.fit(train["text"], train["label"])
        predictions = model.predict(validation["text"])
        metrics = calculate_metrics(validation["label"], predictions)
        tuning_results.append(
            {
                "C": classifier_c,
                "validation_macro_f1": metrics["macro_f1"],
            }
        )
        if (
            best_validation_metrics is None
            or metrics["macro_f1"] > best_validation_metrics["macro_f1"]
        ):
            best_model = model
            best_validation_metrics = metrics
            best_validation_predictions = predictions
            selected_c = classifier_c

    if (
        best_model is None
        or best_validation_metrics is None
        or best_validation_predictions is None
        or selected_c is None
    ):
        raise RuntimeError("No baseline model configuration was selected.")

    validation_sources = evaluate_by_source(
        validation, best_validation_predictions
    )

    # Read the held-out test split only after selecting the model on validation.
    test = pd.read_csv(processed_dir / "test.csv", dtype=str, keep_default_na=False)
    validate_split(test, "test")
    test_predictions = best_model.predict(test["text"])
    test_metrics = calculate_metrics(test["label"], test_predictions)
    test_sources = evaluate_by_source(test, test_predictions)

    output_dir.mkdir(parents=True, exist_ok=True)
    model_path = output_dir / "message_baseline.joblib"
    evaluation_path = output_dir / "message_evaluation.json"
    matrix_path = output_dir / "message_confusion_matrix.png"
    report_path = output_dir / "message_model_report.md"

    joblib.dump(best_model, model_path)
    evaluation = {
        "labels": LABELS,
        "random_seed": RANDOM_SEED,
        "training_rows": len(train),
        "validation_rows": len(validation),
        "test_rows": len(test),
        "selected_parameters": {"classifier__C": selected_c},
        "validation": {
            "metrics": best_validation_metrics,
            "by_source": validation_sources,
            "tuning": tuning_results,
        },
        "test": {
            "metrics": test_metrics,
            "by_source": test_sources,
        },
    }
    evaluation_path.write_text(
        json.dumps(evaluation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_confusion_matrix(
        test_metrics["confusion_matrix"],
        matrix_path,
        "Message Baseline — Held-out Test Set",
    )
    report_path.write_text(
        make_report(
            train,
            best_validation_metrics,
            validation_sources,
            test_metrics,
            test_sources,
            selected_c,
            tuning_results,
        ),
        encoding="utf-8",
    )
    return {
        "model": model_path,
        "evaluation": evaluation_path,
        "confusion_matrix": matrix_path,
        "report": report_path,
        "selected_c": selected_c,
        "validation_metrics": best_validation_metrics,
        "test_metrics": test_metrics,
        "validation_sources": validation_sources,
        "test_sources": test_sources,
    }


if __name__ == "__main__":
    results = train_and_evaluate()
    print(f"Selected classifier C: {results['selected_c']}")
    print(
        "Validation metrics: "
        + json.dumps(results["validation_metrics"], ensure_ascii=False)
    )
    print("Test metrics: " + json.dumps(results["test_metrics"], ensure_ascii=False))
    print("Performance by source:")
    print(json.dumps(results["test_sources"], ensure_ascii=False, indent=2))
    print("Saved artifacts:")
    for key in ("model", "evaluation", "confusion_matrix", "report"):
        print(f"  {results[key]}")
