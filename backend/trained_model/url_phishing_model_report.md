# URL Phishing Baseline Evaluation

- Trained at: `2026-11-11T10:13:11+00:00`
- Cleaned records: 502,591
- Rows with registrable domains: 493,350
- Rows without registrable domains: 9,241
- Train/test split: 391,181 / 102,169
- Actual test fraction: 0.2071
- Domain groups, train/test: 127,037 / 31,760
- Domain overlap: 0
- Split strategy: `GroupShuffleSplit` grouped by registrable domain
- PSL: `tldextract==5.3.0` bundled snapshot, offline, private suffixes included

## Model

- Features: character TF-IDF n-grams [3, 5]
- Logistic Regression: solver `saga`, max_iter `1000`

## Held-out test metrics

- Accuracy: 0.9958
- Precision (phishing): 0.9971
- Recall (phishing): 0.9873
- F1 (phishing): 0.9922

### Confusion matrix

Rows are true labels; columns are predicted labels. Order: `legitimate`, `phishing`.

| | Predicted legitimate | Predicted phishing |
|---|---:|---:|
| True legitimate | 74,662 | 78 |
| True phishing | 349 | 27,080 |

### Per-class classification report

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| legitimate | 0.9953 | 0.9990 | 0.9971 | 74,740.0 |
| phishing | 0.9971 | 0.9873 | 0.9922 | 27,429.0 |

## Registrable-domain extraction

Records without a registrable domain are listed by record ID and hostname in `dataset/url/prepared_mendeley/unresolved_registrable_domains.csv`. They were excluded from the split and training set.

This is a baseline trained on publisher-provided labels; it is not evidence that the underlying URL labels were independently verified.
