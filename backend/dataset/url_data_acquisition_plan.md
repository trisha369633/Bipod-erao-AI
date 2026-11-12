# URL Phishing Data Acquisition Plan

**Prepared:** 2026-11-11  
**Project:** Bipod-Erao AI  
**Scope:** Source evaluation and acquisition recommendations only. No source data was downloaded, imported, or merged; no existing dataset or model was changed; no model was trained.

## Executive recommendation

`Phishing URLs.csv` supplies 54,807 records labeled Phishing, but none labeled benign. Keep it as a candidate positive source, not ground truth, until provenance, usage rights, and the duplicate/malformed records have been reviewed. Do not turn links from message datasets into URL labels.

For an initial competition MVP:

1. Establish licensing/permission and provenance first.
2. Verify and deduplicate the existing phishing candidates; supplement with a second, independent phishing source only where usage terms allow.
3. Build a separate, manually or authoritatively verified benign set. Tranco can suggest domains to review, but a high rank is not a benign verdict.
4. Aim for **5,000–10,000 verified unique phishing URLs and 5,000–10,000 verified unique benign URLs** after review and deduplication. Favor distinct domains/campaigns and recent, documented evidence over raw volume. If this volume cannot be verified in time, use a smaller labeled set and report the limitation; do not relax the label standard.
5. Keep unresolved, stale, conflicting, or otherwise unverified examples as `unknown`, outside binary training and evaluation.

The source checks below were made against the linked official documentation on 2026-11-11. Availability and terms change; re-check the linked terms before acquisition and again before publication or product use.

## Source assessment

| Source | Appropriate use | Availability, format, update | Usage / licensing considerations |
|---|---|---|---|
| [PhishTank developer information](https://phishtank.org/developer_info.php) and [API information](https://phishtank.org/api_info.php) | **Primary phishing candidate source** because it is specifically for reported phishing URLs and has a community verification workflow. A positive should retain the source's record/status and collection time. | The source documents an API and downloadable data feeds. However, the official PhishTank pages returned HTTP 403 to this research environment. I could not verify current feed fields, authentication/key requirements, refresh interval, or current formats from the official pages in this check. Confirm these directly before acquisition; do not rely on an undocumented endpoint or an old feed copy. | Current terms, permitted research/training use, redistribution/model-output conditions, and any rate limits could not be verified here. Treat it as **pending permission/terms review**, not automatically open data. |
| [OpenPhish phishing feeds](https://openphish.com/phishing_feeds.html) and [Terms of Use](https://openphish.com/terms.html) | **Secondary phishing candidate source.** Phishing-specific and has a community feed. Use to corroborate positives or obtain recent candidates, not as sole proof. | Official feed page lists the Community feed as a free plain-text URL list updated every 12 hours. Premium is listed as updated every 5 minutes with CSV/JSON and richer metadata; pricing/access require contacting OpenPhish. | Important: the current Community terms restrict service/data to personal use and academic, independent, or personal research that does not support an organization's business operations. They prohibit organizational commercial/product-development/security-operation uses without prior written consent. Since Bipod-Erao AI is a project/product, obtain written permission or use a properly licensed tier/source before using this feed to develop or distribute the model. Terms also restrict redistribution/derivative works absent written permission. |
| [Tranco](https://tranco-list.eu/), [API documentation](https://tranco-list.eu/api_documentation) | **Benign candidate discovery only.** A stable, research-oriented popularity ranking can seed a review queue; it is not a labeled-safe URL feed. The list is domain-ranked, not a collection of verified complete URLs or page paths. | Standard list is one million domains averaged from source rankings over the preceding 30 days; the site says a new list is available daily by 00:00 UTC. Download is a ZIP containing CSV in rank/domain format; a public API provides list metadata and domain rank history. | The list combines provider data with different terms. Tranco identifies CC BY 3.0 and CC BY-SA 4.0 sources, and also a CC BY-NC 4.0 source (Cloudflare Radar). Review the exact list configuration and component licenses for this project's use; preserve attribution and do not assume commercial/redistribution rights for the combined list. A domain's rank is not a safety assertion. |
| **Official-domain sources and manual verification** (organization-controlled official sites, government registries/directories where applicable) | **Best path for a small, high-confidence benign seed set**, after review of the actual URL and page, not just the domain. Use first-party links published by the organization or an authoritative registry as evidence of ownership/association. | There is no single universal official-domain download/API or common update schedule. Formats and access are source-specific; preserve the source URL/document, retrieval date, and reviewer. | License/terms vary by source. Verify the source's reuse terms before storing or redistributing it. A legitimate organization can host compromised pages or user-generated content, so a verified organization/domain alone does not establish that every URL on it is benign. |
| [URLhaus API](https://urlhaus.abuse.ch/api/), [feeds](https://urlhaus.abuse.ch/feeds/), [FAQ](https://urlhaus.abuse.ch/faq/) | **Do not use as a PhishTank/OpenPhish substitute for phishing labels.** It is an optional additional source for URLs distributing malware, which can be maintained as a separate threat class or used for out-of-scope testing if permitted. | API/downloads require a free abuse.ch Auth-Key. Documentation describes CSV and JSON dumps generated every 5 minutes and instructs consumers not to fetch more frequently than every 5 minutes. | URLhaus explicitly says its submission scope is malware distribution; phishing sites/kits are not accepted as phishing submissions and it directs phishing reports to other services. The pages reviewed point vendors to Terms of Service; they do not establish an unrestricted license for this project's training/redistribution. Review the current ToS and obtain any required permission. Never relabel its malware URLs as phishing without independent phishing evidence. |
| [Google Safe Browsing v4 overview](https://developers.google.com/safe-browsing/v4) / [Google Web Risk overview](https://docs.cloud.google.com/web-risk/docs/overview) | **Optional online corroboration at verification time, not a training-label dump.** A match is evidence of being listed on a particular threat list at a time; no match means only “not found on queried lists,” not proven benign. | Safe Browsing v4 is marked deprecated by Google. Google directs commercial use to Web Risk. Web Risk provides Lookup and Update APIs; Lookup sends the actual URL, while Update uses locally stored hashed lists and requires implementation of Google's URL canonicalization procedure. | Safe Browsing v4 is documented for non-commercial use only. Web Risk says its returned information must not be redistributed; Lookup discloses queried URLs to Google. Check current product/API terms, privacy implications, quota, and pricing before use. Do not turn a no-match into a verified benign label. |

### Source choice for this project

- **Phishing:** Start by reviewing `Phishing URLs.csv` source/provenance and status meaning. Ask PhishTank for current access/terms documentation, then evaluate its verified feed. OpenPhish Community is not a safe default for Bipod-Erao AI product/model development under the currently published terms; seek written consent or an appropriate paid/license arrangement.
- **Benign:** Create an explicit, reviewed allowlist of organization-controlled official domains/URLs with a documented evidence trail. Tranco may help find candidates but cannot label them. Use exact URL/page review and dated corroboration; keep uncertain URLs `unknown`.
- **Other malware:** URLhaus is useful threat intelligence but its scope is malware distribution rather than phishing. Keep such labels separate if ever acquired.
- **Live reputation:** Safe Browsing/Web Risk results can help a reviewer make a time-bounded decision, subject to terms. They do not provide a reusable, redistributable benign dataset.

## Benign URL verification policy

Do not define “benign” as any of the following: a URL's domain appears in Tranco; the host is a famous brand; the URL uses HTTPS; it uses WhatsApp, a shortener, a redirector, or a large hosting provider; a URL is absent from one blocklist; or the containing message is labeled `normal`/`HAM`.

For a `benign` label, require all of the following:

1. **Provenance:** Record where the exact URL came from (prefer first-party official navigation, organization-published link, or controlled collection from a verified official site).
2. **Ownership/association:** Confirm the registrable domain or tenant is controlled by or formally used by the named organization using authoritative evidence; record the evidence reference.
3. **Destination review:** Safely inspect the exact URL's destination and relevant page/content, including redirect chain, at the verification time. Use an isolated review process; do not submit user-private URLs to third-party services without consent.
4. **Threat corroboration:** Check reputable threat sources where use is permitted. A positive hit is evidence to investigate; no hit is not a clean bill of health.
5. **Time-bounded decision:** Store `verified_at`, reviewer/method, and relevant evidence. A URL may later be compromised, repurposed, expire, redirect elsewhere, or change content. Re-verify before treating stale positives as current.
6. **Abstain when uncertain:** If ownership, redirect destination, content, status, or labels conflict or cannot be checked, set `label=unknown`. Do not force it into benign or phishing for class balance.

Manual verification can be a defensible MVP method when it is reproducible and recorded. Use at least two-person review for ambiguous/high-impact examples where feasible, and periodically audit a random sample. Do not browse malicious links from an ordinary workstation; use an isolated, no-credential analysis environment with appropriate safety controls.

## Unified dataset schema

Store one row per **original submitted URL observation**. Keep the original value immutable. If two sources report the same canonical URL, preserve both observations or store a separate provenance/evidence table rather than discarding source history.

| Field | Type | Requirement and meaning |
|---|---|---|
| `original_url` | string | Exact URL as received from the source/message/corpus, before normalization. Do not overwrite it. |
| `normalized_url` | string or null | Canonicalized URL used for exact deduplication/model input. Null if parsing fails; store the normalization version separately. Keep query/path information unless a documented, task-appropriate rule justifies removing it. |
| `label` | enum | `phishing`, `benign`, or `unknown`. `unknown` is a first-class abstention/unverified state and must not enter binary supervised targets. |
| `source` | string/object | Source name and record/feed identifier, e.g. source product, record ID, or organization-published page. Preserve source-specific status, not just source brand. |
| `evidence` | object or JSON | Evidence for the label: status/report ID, first-party ownership reference, observed redirect chain/page-review result, reviewer/method, corroborating source hits, and reason for `unknown`. Do not store credentials or private URL data unnecessarily. |
| `collected_at` | timestamp | UTC time the record was acquired from the source. |
| `verified_at` | timestamp or null | UTC time the URL label/destination was last verified. Null when unverified. |

Recommended additional fields: `record_id`, `normalization_version`, `source_license_or_terms_ref`, `source_observed_at`, `expires_at`/`recheck_after`, `registrable_domain`, `hostname`, `campaign_group_id`, `reviewer_or_method`, `confidence_or_status`, `split`, and `notes`. Store timestamps in ISO 8601 UTC. Treat source-specific status and `verified_at` as distinct from the label.

Illustrative row shape (not a label or actual sample):

```json
{
  "original_url": "<exact URL from source>",
  "normalized_url": "<canonical URL or null>",
  "label": "unknown",
  "source": {
    "name": "<source name>",
    "record_id": "<source record identifier>",
    "terms_ref": "<applicable source terms>"
  },
  "evidence": {
    "source_status": "<source status>",
    "review_method": "<method>",
    "references": [],
    "reason": "<why the label is unknown or verified>"
  },
  "collected_at": "2026-11-11T00:00:00Z",
  "verified_at": null,
  "normalization_version": "<version>"
}
```

The illustrative value is deliberately `unknown`; it does not assert that the placeholder URL is safe or malicious.

## Deduplication and leakage controls

1. Preserve every raw observation and source before deduplicating.
2. Parse URLs with a versioned normalizer: trim only surrounding message punctuation, lowercase scheme/hostname, IDNA-normalize hostnames, normalize default ports, and normalize an empty path to `/`. Preserve path, query, and fragment by default. Do not reorder/remove query parameters, strip tracking parameters, or resolve redirects without a documented rule; those changes can merge distinct destinations or lose malicious evidence.
3. Make normalized exact URL identity the first duplicate key. Keep all source observations/evidence for that key. Flag conflicting labels for manual review; never resolve conflict by arbitrary precedence or majority vote.
4. Add separate, conservative grouping keys for registrable domain (using a pinned Public Suffix List version), hostname/tenant, redirect destination, and campaign/kit where evidence supports it. A redirect URL and final destination are related observations, not automatically interchangeable URLs.
5. Split by group **before** model fitting or feature selection. Keep the same normalized URL, domain/tenant, and known campaign cluster within one partition. Prefer a domain/campaign holdout for validation/test and a later-time holdout for measuring freshness.
6. Shared hosting needs special handling: grouping every customer under one hosting provider's registrable domain can collapse the dataset into one giant group. Group tenant hostnames/subdomains and campaign artifacts; additionally report a stricter provider-held-out result if enough data exists. Never allow the same tenant/campaign to leak across partitions.
7. Freeze a final test set before experiments, and record its source/time cutoff. Report source-specific performance and avoid near-duplicate/template examples crossing partitions.

## MVP sizing and acceptance criteria

**Initial target:** 5,000–10,000 verified, normalized-unique phishing URLs plus 5,000–10,000 verified, normalized-unique benign URLs. Aim for at least hundreds of distinct registrable domains/tenants per class and multiple independent campaigns/sources where available; do not let one domain or feed dominate. Treat these numbers as a practical first benchmark, not a guarantee of statistical representativeness.

Before calling the set model-ready:

- Every binary-labeled row has evidence, source, collection time, and verification time or a documented source-status equivalent.
- Unknown and conflicting records are excluded from binary training and score calculation.
- Duplicate and campaign/domain group assignments are checked across partitions.
- Test has enough independent phishing and benign domains for meaningful per-class precision/recall; if not, report the limitation instead of claiming generalization.
- Licensing permits the intended use, storage, training, and any distribution. Keep source attribution and provenance.
- Establish recheck/retirement policy for stale URLs and preserve the label's “verified as of” time.

A smaller MVP is preferable to a larger set created by assuming that Tranco domains, benign-looking pages, or message labels are verified negatives. The existing 54,807 phishing-only records do not remove the need for verified benign examples.

## Acquisition sequence (no acquisition performed)

1. Contact/consult PhishTank documentation directly because the pages were inaccessible during this review; confirm API key/feed use, update cadence, label status meaning, terms, and redistribution restrictions.
2. Review the provenance and data-use terms for `Phishing URLs.csv`; audit duplicates and invalid records using the existing inspection report before reuse.
3. Contact OpenPhish for written permission or a suitable license if its intelligence is desired for project/model development. Do not treat the free community feed as cleared for product use.
4. Create a benign candidate queue from official organization sources; optionally use a dated Tranco ranking for discovery, with its underlying license constraints documented. Manually verify exact destinations and keep uncertain entries unknown.
5. Implement the schema and review workflow in a separate future data-preparation task. Record source versions and timestamps. Do not merge until label policy, rights, and leakage groups are approved.
6. Assemble a small pilot, review disagreements and source/domain balance, then freeze group-aware splits and train only after a separate approval.

## Official references

- [PhishTank developer information](https://phishtank.org/developer_info.php) and [API information](https://phishtank.org/api_info.php) — official pages returned HTTP 403 in this review; verify directly.
- [OpenPhish feed comparison](https://openphish.com/phishing_feeds.html)
- [OpenPhish Terms of Use](https://openphish.com/terms.html)
- [Tranco homepage and download details](https://tranco-list.eu/)
- [Tranco API documentation](https://tranco-list.eu/api_documentation)
- [URLhaus API/dataset documentation](https://urlhaus.abuse.ch/api/)
- [URLhaus feed limits](https://urlhaus.abuse.ch/feeds/)
- [URLhaus FAQ and scope](https://urlhaus.abuse.ch/faq/)
- [Google Safe Browsing v4 overview/deprecation notice](https://developers.google.com/safe-browsing/v4)
- [Google Web Risk overview](https://docs.cloud.google.com/web-risk/docs/overview)

This is a source-selection plan, not legal advice. Obtain confirmation from each source owner when a term is unclear, especially before competition submission, public release, or product integration.
