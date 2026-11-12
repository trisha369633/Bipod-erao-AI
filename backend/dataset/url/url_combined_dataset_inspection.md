# Combined URL Dataset Inspection

**Inspection date:** 2026-11-11  
**Scope:** Read-only inspection of the two source CSVs and the existing offline URL normalizer. No dataset, model, or application code was changed, and no model was trained.

## Files and attribution

| Dataset | Exact project path | Rows | Columns |
|---|---|---:|---|
| Mendeley URL dataset | `backend/URL dataset.csv` | 450,176 | `url`, `type` |
| Phishing URLs dataset | `backend/Phishing URLs.csv` | 54,807 | `url`, `Type` |

Source attribution for the Mendeley publication: **Mendeley Data, “Phishing URL dataset,” version 1, DOI [10.17632/vfszbj9b36.1](https://doi.org/10.17632/vfszbj9b36.1), CC BY 4.0**. The Mendeley record states it was published on 2 April 2024.

The Mendeley record describes the 450,176-row URL dataset as containing `phishing` and `legitimate` categories, with 104,438 phishing and 345,738 legitimate URLs. It separately describes a 54,807-URL phishing-only dataset. Those published counts and descriptions match the observed row counts and label distributions in the two local files. This is source-level attribution and label documentation, not independent verification of every URL's current or historical status.

## Schema, labels, and missing values

| File | Label field and values found | Missing `url` | Missing label |
|---|---|---:|---:|
| `backend/URL dataset.csv` | `type`: `phishing` 104,438; `legitimate` 345,738 | 0 | 0 |
| `backend/Phishing URLs.csv` | `Type`: `Phishing` 54,807 | 0 | 0 |

The CSV contents establish the literal labels. The Mendeley record identifies `phishing` as the malicious class and `legitimate` as the non-malicious/benign class. Accordingly, `legitimate` maps to the benign class for this dataset, while retaining the original label spelling in any source-preserving copy. This mapping reflects the publisher's documented meaning; it does not independently establish that each row is correctly labeled.

## Normalization and URL quality

Each non-empty `url` field was passed through `backend/dataset/url/normalize_url.py`'s `normalize_url()` function. The utility is offline: it requires an explicit HTTP(S) scheme, validates supported URL syntax, normalizes scheme/hostname/default ports, preserves path/query/fragment, and does not fetch or follow URLs. No URL strings or query values are included here.

| File | Rows not normalizable by the existing utility | Exact duplicate URL groups / excess rows | Exact duplicate full-row groups / excess rows | Normalized duplicate URL groups / excess rows |
|---|---:|---:|---:|---:|
| `backend/URL dataset.csv` | 2,202 | 0 / 0 | 0 / 0 | 74 / 74 |
| `backend/Phishing URLs.csv` | 27 | 1 / 2 | 1 / 2 | 40 / 41 |

“Excess rows” counts additional occurrences after retaining one copy of each unique value. An unnormalizable row is not necessarily malicious or unusable under every URL standard; it failed this project's explicit HTTP(S) normalizer and should be reviewed or quarantined rather than silently repaired.

The normalizer failure categories were:

| Failure category | Mendeley URL dataset | Phishing URLs |
|---|---:|---:|
| Whitespace or backslash rejected | 2,111 | 6 |
| Unsupported scheme | 43 | 0 |
| Hostname syntax malformed | 39 | 18 |
| Control character present | 2 | 2 |
| Missing hostname | 2 | 0 |
| IDNA conversion failure | 4 | 0 |
| Malformed authority or port | 1 | 0 |
| Leading/trailing whitespace | 0 | 1 |

## Cross-dataset overlap

Comparisons below use exact raw URL strings for the exact match, and the existing normalizer's output for normalized matches. Label comparison is case-insensitive (`Phishing` and `phishing` treated as the same label).

| Check | Result |
|---|---:|
| Exact URL values present in both files | 48 |
| Normalized URL values present in both files | 48 |
| Shared URLs with conflicting labels | 0 |
| Shared URLs labeled phishing in both files | 48 |
| `Phishing URLs.csv` exact unique URL set contained in Mendeley file | No; 54,757 exact unique URLs are absent |
| Normalizable unique URL set from `Phishing URLs.csv` contained in Mendeley file | No; 54,691 normalized URLs are absent |

Thus, all observed cross-file duplicates are exact as well as normalized matches; there were no additional matches caused only by normalization. The 48 shared records agree on the phishing label. The phishing-only file is **not** a subset of the larger file.

Considering only rows that normalize successfully and deduplicating by normalized URL across both files yields **502,591 unique normalized URL keys** (`447,900 + 54,739 - 48`). This is a count for inspection, not a prepared or approved training dataset; the 2,229 unnormalizable rows and repeated observations are excluded from that count.

## Can the files be combined safely?

They must not be concatenated and counted as independent examples: doing so would double-count the 48 shared normalized URLs, retain within-file duplicates, and include rows the existing normalizer cannot process. A future source-preserving staging process could reconcile valid records by normalized URL while keeping both source attributions and original labels, and route duplicates with any label disagreement to manual review. In this inspection, the shared URLs have no label disagreement.

The Mendeley description provides an attribution and class definition for the two matching-size collections, but it does not establish record-by-record verification, collection timestamps, or whether the local phishing-only CSV is an unchanged copy of the Mendeley file. Preserve the provided Mendeley attribution and CC BY 4.0 terms; do not discard source identity when deduplicating. Keep the existing originals unchanged.

## Safest next step

Do not train yet. Create a separate, source-preserving staging copy only after documenting source/license metadata and label provenance. For each URL, retain the original value and source label, normalize with the existing utility, quarantine the normalizer failures, deduplicate by normalized URL, and manually review conflicting labels (none found in this comparison). Keep a record of the 48 cross-file duplicates as multi-source observations rather than treating them as additional independent samples. Before splitting for model work, group related domains/campaigns to reduce train/test leakage and independently review the publisher-supplied labels and benign class assumptions.

## Method and privacy

Inspection used Python's CSV reader and the existing normalizer; comparisons and summaries were computed locally. No URLs were visited, no external feed/API was queried, and no full URL, path, or query value was printed in this report. Source documentation was checked at the Mendeley DOI record.
