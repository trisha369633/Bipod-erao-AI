# URL Dataset Preparation

This directory is the isolated staging area for future URL-level records. The pipeline here does not retrieve URLs, follow redirects, assign verdicts, or train models.

## Status of existing data

`backend/Phishing URLs.csv` remains `provenance_unverified`. Do **not** copy or use it as approved training data. The existing message datasets also are not URL labels. Add records here only after their URL-level label, evidence, and usage permissions have been reviewed.

Start a future CSV with this exact header:

```csv
record_id,original_url,normalized_url,label,source,evidence,collected_at,verified_at,registrable_domain
```

`label` is exactly one of `phishing`, `benign`, or `unknown`. `unknown` is retained for triage and must be excluded from binary training and binary evaluation. `evidence` should be a concise JSON object encoded in the CSV cell (quote/escape it as CSV requires) or a stable evidence reference. Do not put credentials or unnecessary personal data in it.

### Fields

| Column | Meaning |
|---|---|
| `record_id` | Stable, unique identifier for this source observation. |
| `original_url` | URL exactly as received. Never overwrite this with a normalized value. |
| `normalized_url` | Result of the local normalizer, or blank only when the original cannot be safely normalized. |
| `label` | `phishing`, `benign`, or `unknown`; labels must be supported by URL-level evidence. |
| `source` | Feed/source name plus source record/version where available. |
| `evidence` | Verifiable evidence, source status, review method, and reason for an `unknown` result. |
| `collected_at` | ISO 8601 timestamp in UTC for when this observation was added to this collection. |
| `verified_at` | ISO 8601 UTC timestamp for when the URL verdict was last checked; blank is allowed for `unknown`, but binary `phishing`/`benign` rows require a verification timestamp. |
| `registrable_domain` | Pay-level/registrable domain determined with a pinned Public Suffix List version. Leave blank rather than guessing if the suffix/domain cannot be determined; the validator reports blanks but does not calculate this field. |

### Adding future records safely

1. Confirm the upstream source's label meaning, provenance, usage terms, and permission for the intended use before importing records.
2. Keep the unmodified source record and its source identifier. Record when it was collected and when the verdict was checked.
3. Use `phishing` only for documented URL-level evidence of phishing; use `benign` only after review of that exact URL and its destination. Domain popularity, HTTPS, a message's label, or absence from a blocklist is not enough to establish benignness.
4. Put unresolved, stale, disputed, or malformed observations in `unknown` (or quarantine them for repair). Do not manufacture a binary label to balance classes.
5. Normalize with `normalize_url.py`. It requires an explicit HTTP(S) scheme, performs no network access, and does not follow redirects or determine safety. Preserve the original value alongside the normalized value.
6. Fill `registrable_domain` using a pinned PSL implementation/data version in the future ingestion workflow. The normalizer intentionally does not approximate registrable domains.
7. Preserve every observation and source when deduplicating. Investigate different labels on the same normalized URL; the validator reports them as conflicts rather than resolving them.
8. Split after exact URL deduplication and group related domains/tenants/campaigns together to avoid train/validation/test leakage.
9. Keep `unknown` records in a separate review pool and never include them in binary training/evaluation targets.

The pipeline intentionally does not import `backend/Phishing URLs.csv`, any message dataset, or external sources automatically.

## Validation

Run the unit tests using only synthetic URLs under the reserved `.test` namespace:

```bash
cd backend
python -m unittest discover -s dataset/url -p 'test_*.py' -v
```

Validate a CSV staged in this directory (the default summary is written here and contains no URL paths or query values):

```bash
python dataset/url/validate_dataset.py dataset/url/url_records.csv
```

The validator only accepts input and report paths inside this directory, preventing accidental use of the existing unverified CSV. It does not modify the input file. A validation run exits nonzero when it finds schema, missing-value, malformed-URL, or label-conflict issues.
