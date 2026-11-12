# `Phishing URLs.csv` Provenance Audit

**Audit date:** 2026-11-11  
**File audited:** `backend/Phishing URLs.csv`  
**Provenance status:** **`provenance_unverified`**

## Conclusion

The source dataset, URL collection date, original label authority, verification state, and usage permissions **cannot be established from the available repository evidence**. The file should be kept out of the final URL-model training/evaluation dataset until a human confirms provenance, labeling, and reuse rights.

This conclusion does not assert that the URLs are or are not phishing. It means the CSV's `Phishing` values have not been independently tied to a documented source or verification process in this project.

## Confirmed repository and file facts

- The CSV has 54,807 data rows and two columns: `url` and `Type`.
- Both columns have zero missing values in the parsed CSV.
- Every `Type` value is exactly `Phishing` (54,807, 100%); there are 54,805 distinct raw URL strings and two extra exact duplicate rows.
- The file is approximately 4.20 MB. SHA-256 at audit time: `00762308b0347c899769487dac35ee0ab0664fd6f2259588ff7151faab776041`.
- The first five records have the label `Phishing`. Their hostnames, without URL paths or query values, are `docs.google.com`, `btttelecommunniccatiion.weeblysite.com`, `kq0hgp.webwave.dev`, `brittishtele1bt-69836.getresponsesite.com`, and `bt-internet-105056.weeblysite.com`. This is a structure sample only, not a validation of those labels. A URL on a well-known or shared hosting service is not by itself proof of benignness or phishing.
- The only dataset fields are `url` and `Type`; there are no source, source-record ID, collection/observation timestamp, reporter, verification status, evidence, or license fields.

## Repository search

The project was searched for references to the CSV name, PhishTank/OpenPhish, source/citation/license terms, URL dataset references, README/license/citation/metadata/download documentation, and project scripts.

- No repository documentation, source URL, citation, license notice, metadata file, or download script identifying where this CSV came from was found.
- The existing inspection reports describe its schema and class balance, but do not identify its upstream source or license. They are summaries of the file, not provenance evidence.
- The visible project documentation includes `frontend/README.md`; no project README or license record was found that attributes this CSV.
- No matching URL-data acquisition script or source-specific metadata was found in the repository.

This is a repository-only search. It cannot rule out external notes, the original uploader's records, a source catalog outside the repository, or terms supplied when the file was obtained.

## Git history

Git history shows `backend/Phishing URLs.csv` was added in commit `c0f9a9b` on **2026-11-10**, titled **“First commit: Bipod-Erao AI project structure.”** The available history does not show a prior source repository, import/download command, upstream commit, or acquisition event. The file being present by this commit date establishes only that it had entered this Git repository by then.

**The commit date is not a dataset collection date.** It does not establish when the URLs were observed, when the labels were assigned, or when the file was obtained. No credentials or private data were inspected or included in this report.

## What can and cannot be established

| Question | Finding |
|---|---|
| What is the file's current structure? | Confirmed: `url`, `Type`; 54,807 rows. |
| What labels are present in this copy? | Confirmed: `Phishing` on every row. |
| Who/what supplied the file? | Not established. No source attribution was found. |
| When were the URLs collected or observed? | Not established. The Git commit date is not a collection timestamp. |
| Were the original labels independently verified? | Not established. The `Type` column records a claim, but no source status, evidence, or verification metadata is present. |
| What did the upstream label mean, and what process assigned it? | Not established. No label definition, annotation policy, or original source record is present. |
| Does the file grant permission to use, train on, or redistribute the data? | Not established. No license or terms reference accompanies the file, and no repository citation identifies one. |
| Is this file a safe, verified positive training set? | Not established. Do not treat the class values alone as verified ground truth. |

## Assumptions explicitly not made

- The filename and `Type=Phishing` values were not treated as proof of the source or label validity.
- The URL shapes, apparent brands, hosting providers, and sample hostnames were not used to infer labels.
- No public feed was assumed to be the source based on familiar URL patterns.
- The Git commit date was not interpreted as a collection or verification date.
- No license was inferred from the file format, public availability, or repository inclusion.

## Required human confirmation

Before considering this CSV for the final model dataset, obtain and record:

1. **Upstream source and acquisition chain:** original dataset/feed name, source URL or provider, record/feed version or identifier, who obtained it, and how this exact CSV was produced.
2. **Collection/observation dates:** when records were collected and any source-reported first-seen, last-seen, or verification timestamps. If unavailable, explicitly retain those fields as unknown.
3. **Label definition and validation:** what `Phishing` means in the upstream source, the evidence/review policy, source verification status for each record, and whether the file contains only currently/previously confirmed URLs or unreviewed reports.
4. **Usage rights:** the applicable license/terms and confirmation that they permit the intended competition, model training, storage, and any publication or redistribution of data/model outputs. Obtain written permission if terms are absent or unclear.
5. **Record-level issues:** review the two exact duplicate rows and the invalid/malformed records identified by the URL dataset inspection report; do not silently repair, discard, or relabel them.

Until these confirmations are documented, preserve the original file unchanged and label it **`provenance_unverified`** in project tracking. Keep it out of final training, validation, and test datasets. Do not create benign examples from existing message labels or use unverified absence from a reputation feed as proof of benignness.

## Evidence scope and limitations

This audit inspected repository text references and scripts, the CSV header and aggregate counts, a small sanitized sample, and Git history metadata. It did not download or query external feeds, visit any URL, contact an upstream provider, or inspect credentials. No dataset, model, or application code was changed; no model was trained.
