"""Compare saved ML pipelines with Gemini on the approved held-out pilot."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from scipy.optimize import minimize_scalar
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import GroupShuffleSplit, train_test_split

from app.services.gemini_analysis import GeminiAnalysisError, GeminiAnalysisService

BACKEND = Path(__file__).resolve().parents[2]
EVALUATION_DIR = Path(__file__).resolve().parent
MANIFEST_PATH = EVALUATION_DIR / "pilot_sample_manifest.json"
PREDICTIONS_PATH = EVALUATION_DIR / "pilot_predictions.jsonl"
MESSAGE_LABELS = ["normal", "promo", "smish"]
URL_LABELS = ["legitimate", "phishing"]
PILOT_SEED = 20261112
GEMINI_DELAY_SECONDS = 6.1


def _message_id(text: str) -> str:
    normalized = " ".join(text.split()).casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prepare_samples() -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest["sample_seed"] != PILOT_SEED:
        raise ValueError("Pilot manifest seed does not match the evaluation runner.")

    message_test_path = BACKEND / "dataset/processed/test.csv"
    message_validation_path = BACKEND / "dataset/processed/validation.csv"
    url_data_path = (
        BACKEND
        / "dataset/url/prepared_mendeley/prepared_urls_with_domains.csv"
    )
    if _file_sha256(message_test_path) != manifest["message"]["test_file_sha256"]:
        raise ValueError("Message test data changed after pilot sample selection.")
    if (
        _file_sha256(message_validation_path)
        != manifest["message"]["validation_file_sha256"]
    ):
        raise ValueError("Message validation data changed after pilot sample selection.")
    if _file_sha256(url_data_path) != manifest["url"]["test_source_sha256"]:
        raise ValueError("URL data changed after pilot sample selection.")

    messages = pd.read_csv(message_test_path, dtype=str, keep_default_na=False)
    expected_message_ids = manifest["message"]["sample_ids"]
    if len(messages) != 734 or not set(expected_message_ids).issubset(
        set(messages["text"].map(_message_id))
    ):
        raise ValueError("Message test split no longer matches the pilot manifest.")
    message_by_id = {_message_id(row.text): row for row in messages.itertuples()}
    selected_messages = [message_by_id[sample_id] for sample_id in expected_message_ids]

    urls = pd.read_csv(url_data_path, dtype=str, keep_default_na=False)
    urls = urls.loc[urls["registrable_domain"].ne("")].reset_index(drop=True)
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
    train_indices, test_indices = next(
        splitter.split(
            urls["normalized_url"], urls["label"], urls["registrable_domain"]
        )
    )
    train_domains = set(urls.iloc[train_indices]["registrable_domain"])
    test_urls = urls.iloc[test_indices]
    if (
        len(train_indices) != 391181
        or len(test_indices) != 102169
        or train_domains & set(test_urls["registrable_domain"])
    ):
        raise ValueError("Reproduced URL test split does not match the saved report.")

    expected_url_ids = manifest["url"]["sample_ids"]
    url_by_id = {
        row.record_id: row for row in test_urls.itertuples(index=False)
    }
    if not set(expected_url_ids).issubset(url_by_id):
        raise ValueError("URL test split no longer matches the pilot manifest.")
    selected_urls = [url_by_id[sample_id] for sample_id in expected_url_ids]

    samples = {
        "message": [
            {
                "sample_id": _message_id(row.text),
                "truth": row.label,
                "input": row.text,
            }
            for row in selected_messages
        ],
        "url": [
            {
                "sample_id": row.record_id,
                "truth": row.label,
                "input": row.normalized_url,
            }
            for row in selected_urls
        ],
    }
    return samples, manifest


def _temperature_scaled(probabilities: np.ndarray, temperature: float) -> np.ndarray:
    logits = np.log(np.clip(probabilities, 1e-12, 1.0)) / temperature
    logits -= logits.max(axis=1, keepdims=True)
    scaled = np.exp(logits)
    return scaled / scaled.sum(axis=1, keepdims=True)


def _fit_message_temperature(model: Any) -> tuple[float, dict[str, float]]:
    validation = pd.read_csv(
        BACKEND / "dataset/processed/validation.csv",
        dtype=str,
        keep_default_na=False,
    )
    if len(validation) != 735:
        raise ValueError("Message validation split no longer matches its report.")
    labels = list(model.classes_)
    probabilities = model.predict_proba(validation["text"])
    targets = np.asarray([labels.index(label) for label in validation["label"]])
    log_probabilities = np.log(np.clip(probabilities, 1e-12, 1.0))

    def validation_log_loss(log_temperature: float) -> float:
        scaled = _temperature_scaled(
            np.exp(log_probabilities), float(np.exp(log_temperature))
        )
        return float(-np.log(scaled[np.arange(len(targets)), targets]).mean())

    result = minimize_scalar(
        validation_log_loss,
        bounds=(-3.0, 3.0),
        method="bounded",
    )
    temperature = float(np.exp(result.x))
    return temperature, {
        "validation_log_loss_before": validation_log_loss(0.0),
        "validation_log_loss_after": validation_log_loss(float(result.x)),
    }


def _classification_metrics(
    truth: list[str], predicted: list[str], labels: list[str]
) -> dict[str, Any] | None:
    if not truth:
        return None
    precision, recall, f1, support = precision_recall_fscore_support(
        truth, predicted, labels=labels, zero_division=0
    )
    return {
        "sample_size": len(truth),
        "accuracy": float(np.mean(np.asarray(truth) == np.asarray(predicted))),
        "macro_precision": float(precision.mean()),
        "macro_recall": float(recall.mean()),
        "macro_f1": float(f1.mean()),
        "per_class": {
            label: {
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
                "support": int(support[index]),
            }
            for index, label in enumerate(labels)
        },
        "confusion_matrix": confusion_matrix(
            truth, predicted, labels=labels
        ).tolist(),
        "confusion_matrix_labels": labels,
    }


def _calibration_metrics(
    truth: list[str], probabilities: np.ndarray, labels: list[str]
) -> dict[str, float]:
    label_indices = {label: index for index, label in enumerate(labels)}
    targets = np.asarray([label_indices[label] for label in truth])
    one_hot = np.eye(len(labels))[targets]
    confidence = probabilities.max(axis=1)
    correct = probabilities.argmax(axis=1) == targets
    bin_edges = np.linspace(0.0, 1.0, 11)
    ece = 0.0
    for lower, upper in zip(bin_edges[:-1], bin_edges[1:]):
        in_bin = (confidence >= lower) & (
            confidence <= upper if upper == 1.0 else confidence < upper
        )
        if in_bin.any():
            ece += float(in_bin.mean()) * abs(
                float(correct[in_bin].mean()) - float(confidence[in_bin].mean())
            )
    return {
        "multiclass_brier_score": float(np.mean(np.sum((probabilities - one_hot) ** 2, axis=1))),
        "top_label_ece_10_equal_width_bins": float(ece),
    }


def _load_existing_predictions(model_name: str) -> dict[tuple[str, str], dict[str, Any]]:
    if not PREDICTIONS_PATH.exists():
        return {}
    existing: dict[tuple[str, str], dict[str, Any]] = {}
    with PREDICTIONS_PATH.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            row = json.loads(line)
            if row.get("gemini_model") != model_name:
                raise ValueError(
                    "Existing pilot predictions use a different Gemini model."
                )
            key = (row["task"], row["sample_id"])
            if key in existing:
                raise ValueError(f"Duplicate persisted prediction at line {line_number}.")
            existing[key] = row
    return existing


def _load_gemini(model_name: str) -> GeminiAnalysisService:
    load_dotenv(BACKEND / ".env")
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=1)
        ),
    )
    return GeminiAnalysisService(client, model_name)


def _render_report(
    task: str,
    labels: list[str],
    rows: list[dict[str, Any]],
    calibration: dict[str, Any] | None,
    model_digest: str,
    model_name: str,
) -> str:
    truth = [row["ground_truth"] for row in rows]
    ml_predictions = [row["ml_prediction"] for row in rows]
    valid_gemini = [row for row in rows if row["gemini_status"] == "available"]
    matched_truth = [row["ground_truth"] for row in valid_gemini]
    ml_matched = [row["ml_prediction"] for row in valid_gemini]
    gemini_predictions = [row["gemini_prediction"] for row in valid_gemini]
    errors = [row for row in rows if row["gemini_status"] == "error"]
    skipped = [row for row in rows if row["gemini_status"] == "skipped"]
    ml_metrics = _classification_metrics(truth, ml_predictions, labels)
    paired_ml_metrics = _classification_metrics(matched_truth, ml_matched, labels)
    gemini_metrics = _classification_metrics(
        matched_truth, gemini_predictions, labels
    )

    if not valid_gemini:
        winner = "No comparison possible: Gemini returned no usable predictions."
    elif paired_ml_metrics["macro_f1"] > gemini_metrics["macro_f1"]:
        winner = (
            "The saved ML model had the higher macro F1 on the usable paired "
            "examples; this is not a conclusive ranking because the Gemini pilot "
            "was incomplete."
        )
    elif paired_ml_metrics["macro_f1"] < gemini_metrics["macro_f1"]:
        winner = (
            "Gemini had the higher macro F1 on the usable paired examples; this "
            "is not a conclusive ranking because the Gemini pilot was incomplete."
        )
    else:
        winner = "The systems tied on macro F1 on the paired examples."

    lines = [
        f"# {task.title()} held-out pilot evaluation",
        "",
        f"- Pilot examples selected: {len(rows)}",
        f"- Gemini usable predictions: {len(valid_gemini)}",
        f"- Gemini requests attempted: {len(valid_gemini) + len(errors)}",
        f"- Gemini API errors: {len(errors)}",
        f"- Gemini skipped/not attempted: {len(skipped)}",
        f"- Gemini model configured: `{model_name}`",
        f"- Saved ML artifact SHA-256: `{model_digest}`",
        "- Pre-run estimate for the complete 200-request pilot: 25k-40k input tokens and 6k-15k output tokens; roughly $0.06-$0.12 at published paid standard rates.",
        "- Actual token usage and cost were not captured by the existing Gemini response wrapper.",
        "- Gemini was sent only the selected message or normalized URL; ground-truth labels were excluded from prompts.",
        "- Metrics are pilot-only and must not be interpreted as full-test-set estimates.",
        "",
        "## Overall metrics",
        "",
        "| System / subset | Accuracy | Macro precision | Macro recall | Macro F1 | N |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, metrics in (
        ("ML, all pilot examples", ml_metrics),
        ("ML, paired successful-Gemini examples", paired_ml_metrics),
        ("Gemini, successful responses only", gemini_metrics),
    ):
        if metrics is None:
            lines.append(f"| {name} | — | — | — | — | 0 |")
        else:
            lines.append(
                f"| {name} | {metrics['accuracy']:.4f} | "
                f"{metrics['macro_precision']:.4f} | {metrics['macro_recall']:.4f} | "
                f"{metrics['macro_f1']:.4f} | {metrics['sample_size']} |"
            )
    lines.extend(["", f"**Pilot result:** {winner}", ""])

    for name, metrics in (
        ("ML, all pilot examples", ml_metrics),
        ("ML, paired examples", paired_ml_metrics),
        ("Gemini, successful responses", gemini_metrics),
    ):
        lines.extend([f"## {name}: per-class metrics", ""])
        if metrics is None:
            lines.extend(["No usable predictions.", ""])
            continue
        lines.extend(
            [
                "| Class | Precision | Recall | F1 | Support |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for label, scores in metrics["per_class"].items():
            lines.append(
                f"| {label} | {scores['precision']:.4f} | {scores['recall']:.4f} | "
                f"{scores['f1']:.4f} | {scores['support']} |"
            )
        lines.extend(
            [
                "",
                f"Confusion matrix (rows actual, columns predicted; order `{', '.join(labels)}`):",
                "",
                "```json",
                json.dumps(metrics["confusion_matrix"]),
                "```",
                "",
            ]
        )

    lines.extend(["## Confidence calibration", ""])
    if task == "message" and calibration is not None:
        lines.extend(
            [
                f"- Temperature scaling fit on the existing message validation set only (N={calibration['validation_size']}); temperature: `{calibration['temperature']:.6f}`.",
                f"- Validation log loss before/after scaling: `{calibration['validation_log_loss_before']:.6f}` / `{calibration['validation_log_loss_after']:.6f}`.",
                f"- Pilot raw ML probabilities: multiclass Brier `{calibration['test_raw']['multiclass_brier_score']:.6f}`, top-label ECE `{calibration['test_raw']['top_label_ece_10_equal_width_bins']:.6f}`.",
                f"- Pilot temperature-scaled ML probabilities: multiclass Brier `{calibration['test_scaled']['multiclass_brier_score']:.6f}`, top-label ECE `{calibration['test_scaled']['top_label_ece_10_equal_width_bins']:.6f}`.",
            ]
        )
    elif task == "url":
        lines.extend(
            [
                "- The existing URL pipeline has no validation split. No calibrator was fit.",
                f"- Pilot raw ML probabilities (uncalibrated diagnostic only): multiclass Brier `{calibration['test_raw']['multiclass_brier_score']:.6f}`, top-label ECE `{calibration['test_raw']['top_label_ece_10_equal_width_bins']:.6f}`.",
            ]
        )
    lines.extend(
        [
            "- Gemini self-reported confidence is not treated as a calibrated probability; no Gemini Brier/ECE is reported.",
            "- ECE uses 10 equal-width bins and top-label confidence. Pilot sample size makes both calibration estimates noisy.",
            "",
            "## Gemini errors and skipped examples",
            "",
        ]
    )
    if errors:
        error_groups: dict[tuple[str, str], int] = {}
        for row in errors:
            error = row.get("gemini_error") or {}
            key = (
                str(error.get("type", "unknown")),
                str(error.get("message", "No usable response"))
                .replace("\n", " ")
                .replace("\r", " "),
            )
            error_groups[key] = error_groups.get(key, 0) + 1
        lines.extend(
            [
                "| Count | Error type | Error |",
                "|---:|---|---|",
            ]
        )
        for (error_type, error_message), count in error_groups.items():
            if "RESOURCE_EXHAUSTED" in error_message:
                error_message = "429 RESOURCE_EXHAUSTED: Gemini account quota exceeded."
            lines.append(
                f"| {count} | `{error_type}` | {error_message.replace('|', '\\|')} |"
            )
    else:
        lines.append("No API errors.")
    if skipped:
        lines.extend(
            [
                "",
                f"{len(skipped)} selected examples were not sent after the quota limit was reached. Their IDs are present in the pilot manifest but have no prediction record.",
            ]
        )
    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "- This is a 100-example stratified pilot drawn only from the held-out test split; it is not the full-test evaluation.",
            "- Failed or invalid Gemini responses are excluded from Gemini metrics; paired ML metrics use only the same examples Gemini successfully classified.",
            "- The successful Gemini subset is non-random because quota exhaustion caused most later requests to fail; its paired result is not a reliable overall ranking.",
            "- Message confidence calibration reuses the validation split previously used to select the saved model configuration; test examples were not used to fit the temperature.",
            "- URL labels are publisher-provided and were not independently verified in the dataset provenance.",
            "- URL calibration could not be fit because no URL validation set exists; raw-probability metrics are descriptive only.",
            "- Model/version, quota, and API availability can change; self-reported Gemini confidence is not calibrated.",
            "",
        ]
    )
    return "\n".join(lines)


def run(preflight: bool, run_gemini: bool, report_only: bool) -> None:
    samples, manifest = _prepare_samples()
    model_paths = {
        "message": BACKEND / "trained_model/message_baseline.joblib",
        "url": BACKEND / "trained_model/url_phishing_char_tfidf_logreg.joblib",
    }
    for task, path in model_paths.items():
        if _file_sha256(path) != manifest["model_artifacts_sha256"][task]:
            raise ValueError(f"The saved {task} model changed after pilot selection.")
    models = {task: joblib.load(path) for task, path in model_paths.items()}
    labels_by_task = {"message": MESSAGE_LABELS, "url": URL_LABELS}
    if any(list(models[task].classes_) != labels for task, labels in labels_by_task.items()):
        raise ValueError("Saved model classes differ from the expected evaluation labels.")

    predictions: dict[tuple[str, str], dict[str, Any]] = {}
    calibration: dict[str, Any] = {}
    for task, items in samples.items():
        model = models[task]
        inputs = [item["input"] for item in items]
        probabilities = model.predict_proba(inputs)
        ml_predictions = model.predict(inputs)
        for index, item in enumerate(items):
            item["ml_prediction"] = str(ml_predictions[index])
            item["ml_probabilities"] = {
                label: float(probabilities[index, class_index])
                for class_index, label in enumerate(model.classes_)
            }
            predictions[(task, item["sample_id"])] = item

        calibration[task] = {}
        if task == "message":
            temperature, validation_metrics = _fit_message_temperature(model)
            scaled = _temperature_scaled(probabilities, temperature)
            calibration[task] = {
                "temperature": temperature,
                "validation_size": 735,
                **validation_metrics,
                "test_raw": _calibration_metrics(
                    [item["truth"] for item in items],
                    probabilities,
                    list(model.classes_),
                ),
                "test_scaled": _calibration_metrics(
                    [item["truth"] for item in items],
                    scaled,
                    list(model.classes_),
                ),
            }
        else:
            calibration[task] = {
                "test_raw": _calibration_metrics(
                    [item["truth"] for item in items],
                    probabilities,
                    list(model.classes_),
                )
            }

    if preflight:
        print(
            json.dumps(
                {
                    "gemini_calls": 0,
                    "planned_gemini_calls": sum(map(len, samples.values())),
                    "message_class_counts": pd.Series(
                        [item["truth"] for item in samples["message"]]
                    ).value_counts().sort_index().to_dict(),
                    "url_class_counts": pd.Series(
                        [item["truth"] for item in samples["url"]]
                    ).value_counts().sort_index().to_dict(),
                    "message_temperature": calibration["message"]["temperature"],
                    "url_calibration": "not fit; no URL validation split exists",
                    "manifest_source_hashes": {
                        "message": manifest["message"]["test_file_sha256"],
                        "url": manifest["url"]["test_source_sha256"],
                    },
                    "model_artifact_hashes": manifest["model_artifacts_sha256"],
                },
                indent=2,
            )
        )
        return
    load_dotenv(BACKEND / ".env")
    model_name = os.getenv("GEMINI_MODEL", "").strip() or "gemini-3.8-flash"
    saved = _load_existing_predictions(model_name)
    if report_only and not PREDICTIONS_PATH.is_file():
        raise FileNotFoundError("Cannot generate reports without saved predictions.")

    if run_gemini:
        service = _load_gemini(model_name)
        from google.genai.errors import APIError

        pending = [
            (task, item)
            for task, items in samples.items()
            for item in items
            if (task, item["sample_id"]) not in saved
        ]
        mode = "a" if PREDICTIONS_PATH.exists() else "x"
        quota_exhausted = False
        with PREDICTIONS_PATH.open(mode, encoding="utf-8") as output:
            for index, (task, item) in enumerate(pending):
                record = {
                    "task": task,
                    "sample_id": item["sample_id"],
                    "ground_truth": item["truth"],
                    "ml_prediction": item["ml_prediction"],
                    "ml_probabilities": item["ml_probabilities"],
                    "gemini_model": model_name,
                }
                try:
                    result = service.classify(task, item["input"])
                    record.update(
                        {
                            "gemini_status": "available",
                            "gemini_prediction": result["prediction"],
                            "gemini_confidence": result["confidence"],
                            "gemini_evidence": result["evidence"],
                            "gemini_reasons": result["reasons"],
                        }
                    )
                except (GeminiAnalysisError, APIError, TimeoutError, OSError) as exc:
                    message = str(exc)[:300]
                    record.update(
                        {
                            "gemini_status": "error",
                            "gemini_error": {
                                "type": type(exc).__name__,
                                "message": message,
                            },
                        }
                    )
                    quota_exhausted = "429" in message or "RESOURCE_EXHAUSTED" in message
                output.write(json.dumps(record, ensure_ascii=False) + "\n")
                output.flush()
                saved[(task, item["sample_id"])] = record
                print(
                    f"{len(saved)}/{len(samples['message']) + len(samples['url'])}: "
                    f"{task} {item['sample_id']} {record['gemini_status']}",
                    flush=True,
                )
                if quota_exhausted:
                    print("Quota exhausted; stopping further Gemini requests.", flush=True)
                    break
                if index < len(pending) - 1:
                    time.sleep(GEMINI_DELAY_SECONDS)

    all_rows = []
    for task, items in samples.items():
        for item in items:
            row = saved.get((task, item["sample_id"]))
            if row is None:
                row = {
                    "task": task,
                    "sample_id": item["sample_id"],
                    "ground_truth": item["truth"],
                    "ml_prediction": item["ml_prediction"],
                    "ml_probabilities": item["ml_probabilities"],
                    "gemini_model": model_name,
                    "gemini_status": "skipped",
                    "gemini_error": {
                        "type": "not_attempted",
                        "message": "Not sent after the evaluator stopped.",
                    },
                }
            all_rows.append(row)
    if len(all_rows) != 200:
        raise RuntimeError("Pilot result count does not equal the selected sample size.")
    for task in ("message", "url"):
        task_rows = [row for row in all_rows if row["task"] == task]
        output_path = EVALUATION_DIR / f"{task}_pilot_report.md"
        report = _render_report(
            task,
            labels_by_task[task],
            task_rows,
            calibration[task],
            hashlib.sha256(model_paths[task].read_bytes()).hexdigest(),
            model_name,
        )
        output_path.write_text(report, encoding="utf-8")
        print(f"Saved {output_path}")
    print(f"Saved {PREDICTIONS_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--run-gemini", action="store_true")
    mode.add_argument("--report-only", action="store_true")
    args = parser.parse_args()
    run(
        preflight=args.preflight,
        run_gemini=args.run_gemini,
        report_only=args.report_only,
    )


if __name__ == "__main__":
    main()
