# URL Dataset Inspection Report

**Inspection date:** 2026-11-11  
**Scope:** Existing data files under `backend/`, including the generated message splits.  
**Changes made:** No datasets, models, or application code were modified. No URL model was trained.

## Executive summary

- There is **one dedicated URL-labeled dataset**: `backend/Phishing URLs.csv`. It has 54,807 records, and every record is labeled `Phishing` (100%). It contains **no labeled benign URLs**, so it cannot train or evaluate a phishing-versus-benign classifier by itself.
- `Phishing URLs.csv` has no source or observation-time columns. Its labels cannot be independently verified from the file alone.
- The SMS/message datasets contain URL-like strings, but their labels describe the **message**, not each URL. `normal`, `promo`, `smish`, `HAM`, and `SPAM` must not be copied as URL labels.
- There are repeated URL records: 2 extra exact-duplicate rows and 1,198 extra rows in 1,197 groups after conservative URL normalization. These should be grouped/deduplicated before any train/test split.
- URL candidates extracted from the existing processed SMS splits overlap across splits: 112 between train/validation, 106 between train/test, and 52 between validation/test. This creates a URL-level leakage risk if the candidates are reused for URL model evaluation.
- **Do not combine the current files as-is.** First obtain independently verified URL-level benign examples and confirm the positive labels and provenance.

## Dataset inventory

`backend/dataset/` does not contain a raw URL dataset. The dedicated URL file is in the `backend/` directory. The `processed/` directory contains message datasets and splits.

| File | Rows / columns | Columns and labels | URL-related finding |
|---|---:|---|---|
| `backend/Phishing URLs.csv` | 54,807 × 2 | `url`, `Type`; `Type=Phishing`: 54,807 (100%) | The only dedicated URL-level dataset. No benign class, source, or timestamp column. |
| `backend/bipod_erao_dataset.csv` | 4,903 × 3 | `label`, `text`, `source`; `smish` 1,966, `normal` 1,742, `promo` 1,195 | Message labels only. A URL-candidate scan found 1,596 messages with candidates and 1,603 candidate occurrences. |
| `backend/BTTC.csv` | 10,283 × 5 | `Text`, `Text_Clean`, `Label`, `Source`, `Annotation_Process`; `HAM` 3,904, `PROMO` 3,695, `SPAM` 2,684 | Message labels only. A URL-candidate scan found 3,004 messages with candidates and 3,411 candidate occurrences in each of `Text` and `Text_Clean`. |
| `backend/dataset/processed/messages_clean.csv` | 4,899 × 3 | `label`, `text`, `source`; `smish` 1,963, `normal` 1,742, `promo` 1,194 | Message labels only. A URL-candidate scan found 1,594 messages and 1,601 candidate occurrences. |
| `backend/dataset/processed/train.csv` | 3,430 × 3 | `label`, `text`, `source`; `smish` 1,374, `normal` 1,220, `promo` 836 | Message labels only. A URL-candidate scan found 1,128 messages and 1,134 candidate occurrences. |
| `backend/dataset/processed/validation.csv` | 735 × 3 | `label`, `text`, `source`; `smish` 295, `normal` 261, `promo` 179 | Message labels only. A URL-candidate scan found 233 messages and 234 candidate occurrences. |
| `backend/dataset/processed/test.csv` | 734 × 3 | `label`, `text`, `source`; `smish` 294, `normal` 261, `promo` 179 | Message labels only. A URL-candidate scan found 233 messages and 233 candidate occurrences. |
| `backend/train-00000-of-00001.parquet` | 4,903 × 3 | `label`, `text`, `source` | Message dataset; an earlier full inspection recorded it as an exact copy of `bipod_erao_dataset.csv`. Not an independent URL source. |
| `backend/train-00000-of-00001 (1).parquet` | 5,574 × 2 | `sms`, integer `label` (`0`: 4,827; `1`: 747) | English SMS dataset, not URL-labeled. The meaning of the integer labels requires authoritative source documentation; they cannot be mapped to URL labels. |

The other CSV files were inspected for URL/link/domain/host columns and URL-like strings in their message fields. The Parquet schemas and summary above are from the existing `backend/dataset_inspection_report.md`, which records a full `read_parquet` inspection on 2026-11-10. In the current inspection environment, `pandas.read_parquet` could not run because neither `pyarrow` nor `fastparquet` is installed; therefore, the Parquet files were not re-read or rescanned for embedded URL occurrences during this run.

The message-text counts above are **candidate extraction counts**, not verified URL records. The scan recognizes common scheme-based, `www`, and bare-domain patterns; it does not establish that a candidate resolves, is safe, or is malicious.

## `Phishing URLs.csv` quality checks

| Check | Result |
|---|---:|
| Rows / columns | 54,807 / `url`, `Type` |
| Missing values | 0 in both columns |
| Label distribution | `Phishing`: 54,807 (100%); no other class |
| Exact duplicate full rows | 2 extra rows; 54,805 distinct raw URL strings |
| Repeated URLs after conservative normalization | 1,197 groups / 1,198 extra valid rows |
| Structurally valid under local checks | 54,786 |
| Structurally invalid under local checks | 21 |
| Distinct hostnames among parsed records | 32,936 |

The local structural check accepts HTTP(S), parses the authority and port, accepts IP literals and IDN/punycode hostnames, and checks host-label and control-character syntax. It does **not** make DNS requests, visit pages, inspect redirect destinations, or check a reputation service. The 21 structurally invalid records comprise 18 invalid hostname-label cases (including underscores), one literal backslash in a URL, and two records with control characters. They should be quarantined for review, not silently repaired or treated as a different label.

Normalization for the duplicate scan trims surrounding punctuation, lowercases the scheme and hostname, converts hostnames to IDNA form, and supplies `/` for an empty path while preserving the URL path, query, and fragment. The 1,197 groups are duplicate candidates under this rule; review them before deduplicating because normalization choices can affect URL identity.

Some records use common hosting or redirect platforms: 4,026 parsed records have a host ending in `google.com`, and 1,284 use the checked set of well-known shortening hosts. This does **not** prove those records are mislabeled: phishing content can be hosted on legitimate platforms or use redirectors. Conversely, the `Phishing` label alone is not independent proof that every submitted record is malicious. Review provenance and the actual URL/context before changing labels.

## Labels, combining, and leakage

### Labels are not interchangeable

- `Phishing` in the URL file is the only explicit URL-level class.
- `normal`/`HAM`, `promo`/`PROMO`, and `smish`/`SPAM` are message-level classes. A message may contain a legitimate link, and a message labeled normal does not independently verify every URL it contains.
- The numeric labels in the SMS Parquet are also message labels, and their mapping must be verified before use even for message analysis.
- Therefore, extracting links from any message dataset does not create trustworthy benign or phishing URL examples. Those extracted links remain **unlabeled** unless independently verified.

### Duplicate and split leakage

- The URL dataset has exact and normalized repeats. Randomly splitting rows before deduplication can put the same URL in both training and evaluation and inflate scores.
- Candidate URLs from the existing message splits repeat across partitions: train/validation share 112 case-folded candidates, train/test share 106, and validation/test share 52. This scan compares extracted strings; it may miss variants that resolve to the same URL.
- These overlaps are not proof that the message-classification model has leakage: its task and labels are message-level. They do mean the existing SMS partitions should **not** be treated as independent URL-level evaluation sets without URL-aware grouping.
- No shared URL was found between the phishing URL file and the extracted candidates from the processed SMS splits under the scan's URL normalization. This does not make the SMS candidates benign.

### Is a safe combination possible now?

**No supervised binary URL dataset can be built safely from the current files.** The dedicated URL dataset is single-class, and the message datasets have a different prediction target. Combining them by assigning message labels to their links would invent URL labels. Combining `Phishing URLs.csv` with an unlabeled or unverified link set as negatives would also violate the required label standard.

The message datasets may be retained as a separate source of *unlabeled URL candidates* for later review. The custom CSV and its Parquet copy must not both be counted as independent samples. Any later URL dataset merge should preserve provenance and timestamps, normalize/deduplicate before splitting, and resolve conflicting labels through review rather than silently selecting one.

## What data is needed before URL-model training

Collect a URL-level dataset with both:

1. **Confirmed phishing/malicious URLs**, supported by a documented, independently verifiable source or review process.
2. **Confirmed benign URLs**, verified at the URL or destination level using documented trusted provenance (for example, controlled/manual validation or a curated set of official domains and pages).

For both classes, store the original URL, normalized URL, label, label source/evidence, observation or verification time, and source/provenance. Keep links that cannot be verified in an **unlabeled/unknown** pool; do not make them benign by default. Include diverse domains, URL structures, languages/regions and time periods. Avoid using only trusted hostnames as negatives: shared hosting and legitimate redirect services can carry malicious destinations.

## Recommended approach

1. **Start with a data gate, not training.** Review the 21 structurally invalid rows, inspect duplicate groups and source provenance, and manually/independently verify positive labels, especially records on shared hosting and redirect services.
2. **Acquire verified examples of both URL classes.** Keep phishing, benign, and unknown records distinct; retain verification dates because URL status can change.
3. **Build a URL-level baseline.** Begin with character n-gram TF-IDF features and a regularized Logistic Regression or linear SVM, optionally combined with carefully tested lexical features (length, host/path structure, IP literal, unusual port, and redirect markers). Do not use HTTPS or a known service alone as a phishing label.
4. **Prevent leakage during evaluation.** Deduplicate on a documented normalized URL first. Split by registrable domain (and, where available, campaign/source) so related URLs do not cross partitions; consider a later time-based holdout to test freshness. Do not randomly split individual URLs alone.
5. **Evaluate for the product's risk.** Report per-class precision/recall, PR-AUC and a confusion matrix, with particular attention to false positives on benign services and false negatives. Calibrate confidence on a separate validation set and preserve an abstain/Unknown outcome for unverified or low-confidence URLs.
6. **Keep URL and message models separate.** URL verdicts should use URL-level labels and an independently versioned pipeline. Message labels and the existing working message model remain unchanged.

## Recommended next steps

1. Locate and document the source, collection date, and labeling method for `Phishing URLs.csv`.
2. Review exact and normalized duplicate groups and the 21 malformed entries; do not delete or relabel them without review.
3. Source a verified benign URL dataset and, if needed, a separately verified malicious feed with dates and provenance.
4. Define URL label policy (`phishing`, `benign`, `unknown`) and normalization/deduplication rules before merging.
5. Create domain-aware and time-aware URL train/validation/test partitions from the verified URL dataset, separately from the message partitions.
6. Only after these checks, approve a baseline URL-model training plan. **No model was trained as part of this inspection.**
