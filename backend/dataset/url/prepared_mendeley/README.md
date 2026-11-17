# Prepared Mendeley URL Dataset

This is a source-attributed staging dataset prepared from the two original CSVs
listed below. The originals were read only and were not changed.

## Attribution and license

Mendeley Data, **Phishing URL dataset**, DOI
[10.17632/vfszbj9b36.1](https://doi.org/10.17632/vfszbj9b36.1), version 1.
License: **CC BY 4.0**. Cite the Mendeley Data record and retain this attribution
when reusing or redistributing the prepared data.

Original filenames:

- `URL dataset.csv` — columns `url`, `type`; source labels `phishing` and `legitimate`.
- `Phishing URLs.csv` — columns `url`, `Type`; all source labels `Phishing`.

Both files are attributed to the same Mendeley Data DOI. The `source` field in
the prepared CSV retains the filename(s) contributing each deduplicated record;
the `evidence` field preserves source row references and publisher-provided
labels. Repeated URLs from both files are represented once, with both sources
retained.

## Preparation details

- Labels are standardized to exactly `phishing` and `legitimate`.
- URLs were normalized offline using the project's existing `normalize_url.py`.
  No URL was fetched and no redirect was followed.
- Unnormalizable rows are retained in `quarantine_invalid_urls.csv`.
- Conflicting normalized URL labels would be retained in
  `quarantine_label_conflicts.csv`; no such conflicts were found in this run.
- `collected_at` records the UTC time this staging copy was prepared.
- `verified_at` is blank because the source files do not provide per-URL
  verification timestamps; none were invented.
- `registrable_domain` is blank because this pipeline has no pinned Public
  Suffix List data and does not guess registrable domains.
- The publisher's labels are preserved as source claims; they have not been
  independently verified. This staging output is not model training approval.
- No message dataset or message-level label was used.

## Files

- `prepared_urls.csv.gz` — losslessly compressed normalized, deduplicated records.
- `prepared_urls_with_domains.csv.gz` — losslessly compressed data with the
  registrable-domain groups used by the URL pipeline.
- `quarantine_invalid_urls.csv` — every input row rejected by the normalizer.
- `quarantine_label_conflicts.csv` — all observations in any conflicting-label
  normalized URL group.
- `preparation_report.md` — detailed aggregate preparation counts and output
  paths; it does not print URL values.
- `validation_summary.md` — output of the existing URL dataset validator.
- `prepare_dataset.py` — reproducible local preparation utility.
- `compress_prepared_csvs.py` — streaming, lossless compressor; preserves source
  files unless run with `--replace-originals`.

## Lossless compression

Run `python3 compress_prepared_csvs.py` to create verified `.csv.gz` copies
while retaining the original CSVs. Add `--replace-originals` to remove each
uncompressed CSV only after its compressed copy is verified byte-for-byte and
is below 100 MB. No rows, columns, or cell values are changed.

The existing validator's accepted labels are `phishing`, `benign`, and
`unknown`, and it requires `verified_at` for binary labels. This prepared file
intentionally uses the requested publisher-aligned `legitimate` label and
leaves unavailable verification timestamps blank. Therefore, the existing
validator is expected to flag those schema/verification mismatches; do not
silently rewrite labels or fabricate timestamps to make the check pass.
