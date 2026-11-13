# Url held-out pilot evaluation

- Pilot examples selected: 100
- Gemini usable predictions: 0
- Gemini requests attempted: 6
- Gemini API errors: 6
- Gemini skipped/not attempted: 94
- Gemini model configured: `gemini-2.5-flash`
- Saved ML artifact SHA-256: `ffc167a043cb6ef9024f1070855e63b61466a5a0afddfeb12474dbad3d367cd0`
- Pre-run estimate for the complete 200-request pilot: 25k-40k input tokens and 6k-15k output tokens; roughly $0.06-$0.12 at published paid standard rates.
- Actual token usage and cost were not captured by the existing Gemini response wrapper.
- Gemini was sent only the selected message or normalized URL; ground-truth labels were excluded from prompts.
- Metrics are pilot-only and must not be interpreted as full-test-set estimates.

## Overall metrics

| System / subset | Accuracy | Macro precision | Macro recall | Macro F1 | N |
|---|---:|---:|---:|---:|---:|
| ML, all pilot examples | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100 |
| ML, paired successful-Gemini examples | — | — | — | — | 0 |
| Gemini, successful responses only | — | — | — | — | 0 |

**Pilot result:** No comparison possible: Gemini returned no usable predictions.

## ML, all pilot examples: per-class metrics

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| legitimate | 1.0000 | 1.0000 | 1.0000 | 73 |
| phishing | 1.0000 | 1.0000 | 1.0000 | 27 |

Confusion matrix (rows actual, columns predicted; order `legitimate, phishing`):

```json
[[73, 0], [0, 27]]
```

## ML, paired examples: per-class metrics

No usable predictions.

## Gemini, successful responses: per-class metrics

No usable predictions.

## Confidence calibration

- The existing URL pipeline has no validation split. No calibrator was fit.
- Pilot raw ML probabilities (uncalibrated diagnostic only): multiclass Brier `0.000866`, top-label ECE `0.011877`.
- Gemini self-reported confidence is not treated as a calibrated probability; no Gemini Brier/ECE is reported.
- ECE uses 10 equal-width bins and top-label confidence. Pilot sample size makes both calibration estimates noisy.

## Gemini errors and skipped examples

| Count | Error type | Error |
|---:|---|---|
| 6 | `ClientError` | 429 RESOURCE_EXHAUSTED: Gemini account quota exceeded. |

94 selected examples were not sent after the quota limit was reached. Their IDs are present in the pilot manifest but have no prediction record.

## Limitations

- This is a 100-example stratified pilot drawn only from the held-out test split; it is not the full-test evaluation.
- Failed or invalid Gemini responses are excluded from Gemini metrics; paired ML metrics use only the same examples Gemini successfully classified.
- The successful Gemini subset is non-random because quota exhaustion caused most later requests to fail; its paired result is not a reliable overall ranking.
- Message confidence calibration reuses the validation split previously used to select the saved model configuration; test examples were not used to fit the temperature.
- URL labels are publisher-provided and were not independently verified in the dataset provenance.
- URL calibration could not be fit because no URL validation set exists; raw-probability metrics are descriptive only.
- Model/version, quota, and API availability can change; self-reported Gemini confidence is not calibrated.
