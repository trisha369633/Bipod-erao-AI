# Bilingual Message Baseline Model Report

## Model architecture

- Word-level TF-IDF: unigrams and bigrams, Unicode-aware token pattern, lowercasing, and sublinear term frequency.
- Character-level TF-IDF: character n-grams from 2 to 5 characters, with sublinear term frequency.
- The word and character feature matrices are combined with `FeatureUnion`.
- Multiclass Logistic Regression predicts exactly `normal`, `promo`, or `smish`.
- The saved scikit-learn pipeline contains both vectorizers and the classifier.

The Unicode-aware word vectorizer retains Bengali word characters. Character n-grams provide complementary features for Bengali, English, Banglish, and CodeMix. No translation or stop-word removal is performed.

## Training details

- Training rows: 3430
- Training labels: {"normal": 1220, "promo": 836, "smish": 1374}
- Training sources: {"Banglish": 886, "Bengali": 893, "CodeMix": 813, "English": 838}
- Random seed: `42`
- Training used only `train.csv`.
- Candidate classifier C values were selected using validation macro F1; validation and test examples were not used to fit the model.
- Selected C: `2.0`
- Test metrics were computed once after selecting the configuration.

| Candidate C | Validation macro F1 |
|---:|---:|
| 0.5 | 0.9757 |
| 1.0 | 0.9759 |
| 2.0 | 0.9770 |

## Validation metrics

- Accuracy: 0.9769
- Macro precision: 0.9783
- Macro recall: 0.9758
- Macro F1: 0.9770

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| normal | 0.973 | 0.985 | 0.979 | 261 |
| promo | 0.989 | 0.966 | 0.977 | 179 |
| smish | 0.973 | 0.976 | 0.975 | 295 |

### Validation performance by source

| Source | Rows | Accuracy | Macro Precision | Macro Recall | Macro F1 |
|---|---:|---:|---:|---:|---:|
| Banglish | 202 | 0.975 | 0.978 | 0.974 | 0.976 |
| Bengali | 190 | 0.984 | 0.981 | 0.984 | 0.982 |
| CodeMix | 182 | 0.973 | 0.974 | 0.974 | 0.974 |
| English | 161 | 0.975 | 0.978 | 0.973 | 0.975 |

### Validation confusion matrix

Rows are actual labels; columns are predicted labels.

| Actual \ Predicted | normal | promo | smish |
|---|---:|---:|---:|
| normal | 257 | 1 | 3 |
| promo | 1 | 173 | 5 |
| smish | 6 | 1 | 288 |

The largest off-diagonal count is 6 actual `smish` messages predicted as `normal`. Off-diagonal cells are errors; diagonal cells are correct predictions.

## Final test metrics

- Accuracy: 0.9837
- Macro precision: 0.9858
- Macro recall: 0.9813
- Macro F1: 0.9834

| Label | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| normal | 0.996 | 0.981 | 0.988 | 261 |
| promo | 0.994 | 0.966 | 0.980 | 179 |
| smish | 0.967 | 0.997 | 0.982 | 294 |

### Test performance by source

| Source | Rows | Accuracy | Macro Precision | Macro Recall | Macro F1 |
|---|---:|---:|---:|---:|---:|
| Banglish | 171 | 0.971 | 0.974 | 0.967 | 0.970 |
| Bengali | 169 | 0.982 | 0.983 | 0.981 | 0.982 |
| CodeMix | 180 | 0.989 | 0.991 | 0.990 | 0.990 |
| English | 214 | 0.991 | 0.992 | 0.988 | 0.990 |

### Test confusion matrix

Rows are actual labels; columns are predicted labels.

| Actual \ Predicted | normal | promo | smish |
|---|---:|---:|---:|
| normal | 256 | 0 | 5 |
| promo | 1 | 173 | 5 |
| smish | 0 | 1 | 293 |

The largest off-diagonal count is 5 actual `promo` messages predicted as `smish`. Off-diagonal cells are errors; diagonal cells are correct predictions.

The image `message_confusion_matrix.png` visualizes the held-out test confusion matrix.

## Limitations

- These results measure this specific dataset split and are not a guarantee of real-world scam detection.
- Source/language results use the dataset's existing `source` categories; they are not independently language-detected, and category counts differ.
- CodeMix and Banglish examples may overlap conceptually, and source labels may contain annotation noise.
- TF-IDF is based on token/character patterns; it does not understand context, intent, or newly emerging scam strategies.
- No external validation data or URL-classification task was used.
- The model has no calibrated or validated risk-percentage output; class predictions should not be presented as a probability of fraud.
