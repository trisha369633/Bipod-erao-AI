# Prepared Dataset Validator Results

The existing `validate_dataset.py` validator was run on the byte-identical uncompressed CSV content before lossless gzip compression to `prepared_urls.csv.gz`. This compact report aggregates findings and omits per-row listings and all URL values.

- Rows checked: 502,591
- Validator result: ERRORS REPORTED (CLI exit status 1)
- Required columns missing: none
- Invalid label rows: 345,697
- Required `verified_at` missing for validator-supported binary labels: 156,894
- Malformed original URLs: 0
- Normalization mismatches: 0
- Exact duplicate original-URL extra rows: 0
- Normalized duplicate groups / extra rows: 0 / 0
- Conflicting normalized-label groups: 0
- Blank values: `verified_at` 502,591; `registrable_domain` 502,591

## Interpretation

The file intentionally uses `phishing` and `legitimate`, as requested. The existing validator accepts only `phishing`, `benign`, and `unknown`, so it flags all `legitimate` rows as invalid rather than validating the requested label vocabulary. It also requires `verified_at` for labels it recognizes as binary; source files contain no per-URL verification timestamps, so those values remain blank. No timestamps or label conversions were fabricated to obtain a passing result.

The validator found no malformed URLs in the prepared file, no normalization mismatches, no duplicate normalized URLs, and no label conflicts. The validator's nonzero result reflects the schema/metadata incompatibilities above. This output is a staging dataset, not training approval.
