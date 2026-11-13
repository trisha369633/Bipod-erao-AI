# Message held-out pilot evaluation

- Pilot examples selected: 100
- Gemini usable predictions: 22
- Gemini requests attempted: 100
- Gemini API errors: 78
- Gemini skipped/not attempted: 0
- Gemini model configured: `gemini-2.5-flash`
- Saved ML artifact SHA-256: `41a176b272f6fd8c0a96e7e51d31a0547a43a9d1b5f356d9f170a5420153426e`
- Pre-run estimate for the complete 200-request pilot: 25k-40k input tokens and 6k-15k output tokens; roughly $0.06-$0.12 at published paid standard rates.
- Actual token usage and cost were not captured by the existing Gemini response wrapper.
- Gemini was sent only the selected message or normalized URL; ground-truth labels were excluded from prompts.
- Metrics are pilot-only and must not be interpreted as full-test-set estimates.

## Overall metrics

| System / subset | Accuracy | Macro precision | Macro recall | Macro F1 | N |
|---|---:|---:|---:|---:|---:|
| ML, all pilot examples | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 100 |
| ML, paired successful-Gemini examples | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 22 |
| Gemini, successful responses only | 0.9091 | 0.9167 | 0.8778 | 0.8929 | 22 |

**Pilot result:** The saved ML model had the higher macro F1 on the usable paired examples; this is not a conclusive ranking because the Gemini pilot was incomplete.

## ML, all pilot examples: per-class metrics

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| normal | 1.0000 | 1.0000 | 1.0000 | 36 |
| promo | 1.0000 | 1.0000 | 1.0000 | 24 |
| smish | 1.0000 | 1.0000 | 1.0000 | 40 |

Confusion matrix (rows actual, columns predicted; order `normal, promo, smish`):

```json
[[36, 0, 0], [0, 24, 0], [0, 0, 40]]
```

## ML, paired examples: per-class metrics

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| normal | 1.0000 | 1.0000 | 1.0000 | 11 |
| promo | 1.0000 | 1.0000 | 1.0000 | 6 |
| smish | 1.0000 | 1.0000 | 1.0000 | 5 |

Confusion matrix (rows actual, columns predicted; order `normal, promo, smish`):

```json
[[11, 0, 0], [0, 6, 0], [0, 0, 5]]
```

## Gemini, successful responses: per-class metrics

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| normal | 0.9167 | 1.0000 | 0.9565 | 11 |
| promo | 0.8333 | 0.8333 | 0.8333 | 6 |
| smish | 1.0000 | 0.8000 | 0.8889 | 5 |

Confusion matrix (rows actual, columns predicted; order `normal, promo, smish`):

```json
[[11, 0, 0], [1, 5, 0], [0, 1, 4]]
```

## Confidence calibration

- Temperature scaling fit on the existing message validation set only (N=735); temperature: `0.391981`.
- Validation log loss before/after scaling: `0.144323` / `0.062409`.
- Pilot raw ML probabilities: multiclass Brier `0.048471`, top-label ECE `0.125034`.
- Pilot temperature-scaled ML probabilities: multiclass Brier `0.008154`, top-label ECE `0.021858`.
- Gemini self-reported confidence is not treated as a calibrated probability; no Gemini Brier/ECE is reported.
- ECE uses 10 equal-width bins and top-label confidence. Pilot sample size makes both calibration estimates noisy.

## Gemini errors and skipped examples

| Count | Error type | Error |
|---:|---|---|
| 78 | `ClientError` | 429 RESOURCE_EXHAUSTED: Gemini account quota exceeded. |

## Limitations

- This is a 100-example stratified pilot drawn only from the held-out test split; it is not the full-test evaluation.
- Failed or invalid Gemini responses are excluded from Gemini metrics; paired ML metrics use only the same examples Gemini successfully classified.
- The successful Gemini subset is non-random because quota exhaustion caused most later requests to fail; its paired result is not a reliable overall ranking.
- Message confidence calibration reuses the validation split previously used to select the saved model configuration; test examples were not used to fit the temperature.
- URL labels are publisher-provided and were not independently verified in the dataset provenance.
- URL calibration could not be fit because no URL validation set exists; raw-probability metrics are descriptive only.
- Model/version, quota, and API availability can change; self-reported Gemini confidence is not calibrated.
