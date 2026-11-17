# URL Dataset Preparation Report

**Prepared at:** `2026-11-11T10:07:52Z`  
**Attribution:** Mendeley Data, *Phishing URL dataset*, DOI
[10.17632/vfszbj9b36.1](https://doi.org/10.17632/vfszbj9b36.1), CC BY 4.0.

## Input and row counts

| Metric | Count |
|---|---:|
| Total original rows | 504,983 |
| Valid and normalizable input rows | 502,754 |
| Invalid/unnormalizable rows quarantined | 2,229 |
| Valid normalized duplicate extra rows removed | 163 |
| Conflicting normalized URL groups | 0 |
| Observations placed in conflict quarantine | 0 |
| Agreeing-label duplicate groups collapsed | 162 |
| Agreeing-label duplicate extra rows collapsed | 163 |
| Cross-source normalized URL groups retained once | 48 |
| Final prepared records | 502,591 |

## Per-source counts

| Original source file | Input rows | Valid rows | Invalid rows | Exact duplicate groups / extra rows | Normalized duplicate groups / extra rows | Final unique records carrying source |
|---|---:|---:|---:|---:|---:|
| `URL dataset.csv` | 450,176 | 447,974 | 2,202 | 0 / 0 | 74 / 74 | 447,900 |
| `Phishing URLs.csv` | 54,807 | 54,780 | 27 | 1 / 2 | 40 / 41 | 54,739 |

Source-wise final record counts can overlap: a deduplicated record shared by
both source files is counted under both sources because both attributions are
preserved.

### Normalizer rejection reasons

| Source file | Reason | Rows |
|---|---|---:|
| `URL dataset.csv` | Hostname cannot be converted to IDNA. | 4 |
| `URL dataset.csv` | Hostname syntax is malformed. | 39 |
| `URL dataset.csv` | Only HTTP and HTTPS URLs are supported. | 43 |
| `URL dataset.csv` | URL authority or port is malformed. | 1 |
| `URL dataset.csv` | URL contains control characters. | 2 |
| `URL dataset.csv` | URL contains whitespace or a backslash. | 2,111 |
| `URL dataset.csv` | URL must include a hostname. | 2 |
| `Phishing URLs.csv` | Hostname syntax is malformed. | 18 |
| `Phishing URLs.csv` | URL contains control characters. | 2 |
| `Phishing URLs.csv` | URL contains whitespace or a backslash. | 6 |
| `Phishing URLs.csv` | URL has leading or trailing whitespace. | 1 |

## Final label distribution

| Standardized label | Records |
|---|---:|
| `phishing` | 156,894 |
| `legitimate` | 345,697 |

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
task requires `phishing` and `legitimate`; it also requires a `verified_at`
timestamp for binary labels, which neither source provides. The output
preserves the requested labels and does not invent verification timestamps, so findings on those
requirements must be interpreted as schema/provenance incompatibilities, not
as reasons to alter the labels or fabricate dates. See `validation_summary.md`.

No model was trained. Review the validator compatibility issue and the
publisher-supplied label provenance before treating this staging data as
training-ready.
