# Bipod Erao AI Dataset Inspection

Inspected on 2026-11-10 with pandas (`read_csv` and `read_parquet`). Original files were not modified. The five input datasets are currently in `backend/`; this report is saved at `backend/dataset_inspection_report.md`.

## Summary

| File | Rows × columns | Columns and dtypes | Missing values | Duplicate full rows | Labels |
|---|---:|---|---:|---:|---|
| `bipod_erao_dataset.csv` | 4,903 × 3 | `label` string, `text` string, `source` string | 0 | 0 | `smish` 1,966 (40.10%); `normal` 1,742 (35.53%); `promo` 1,195 (24.37%) |
| `BTTC.csv` | 10,283 × 5 | `Text` string, `Text_Clean` string, `Label` string, `Source` string, `Annotation_Process` string | 0 | 0 | `HAM` 3,904 (37.97%); `PROMO` 3,695 (35.93%); `SPAM` 2,684 (26.10%) |
| `Phishing URLs.csv` | 54,807 × 2 | `url` string, `Type` string | 0 | 2 | `Phishing` 54,807 (100%) |
| `train-00000-of-00001.parquet` | 4,903 × 3 | `label` string, `text` string, `source` string | 0 | 0 | Same distribution as `bipod_erao_dataset.csv` |
| `train-00000-of-00001 (1).parquet` | 5,574 × 2 | `sms` string, `label` int64 | 0 | 403 | `0` 4,827 (86.60%); `1` 747 (13.40%) |

Missing-value counts are zero in every column of every file. For `Text` and `Text_Clean`, all 10,283 BTTC values are individually unique; they are two versions of the same records, not two independent message sets. They differ in 4,203 rows.

## First five rows

Long values are shortened with `…` for readability; column values are shown in source order.

### `bipod_erao_dataset.csv` (`label`, `text`, `source`)

| # | label | text | source |
|---:|---|---|---|
| 1 | smish | আপনি ৩ vori gold জিতেছেন! Claim করুন: +8801716677889 | CodeMix |
| 2 | normal | Tumi ki kheladhula korcho? | Banglish |
| 3 | promo | Bonus soho 2GB-45Tk-3din. Dial *121*5534# or mygp.li/my | Banglish |
| 4 | smish | Apnar payment-ta prokria korte amader apnar tothyo proyojon. Ekhane click korun: [verifysecure.com/InfoBD] | Banglish |
| 5 | smish | জয়! আপনি Google লটারিতে $৫০০০০ জিতেছেন। claim করতে: winlottery.tk/claim পূরণ করুন। | Bengali |

### `BTTC.csv` (`Text`, `Text_Clean`, `Label`, `Source`, `Annotation_Process`)

| # | Text | Text_Clean | Label | Source | Annotation_Process |
|---:|---|---|---|---|---|
| 1 | ৳২২০: ১৫ জিবি, ৩০   দিন! এখনই ডায়াল করুন *21291*2212# | ৳২২০: ১৫ জিবি, ৩০ দিন! এখনই ডায়াল করুন *21291*2212# | PROMO | SMS | ANNOTATOR-REVIEWED |
| 2 | আজই ২৫টাকায় ৫জিবি (সোশ্যাল প্যাক) ৩দিন নিতে ডায়াল *21291*825# | আজই ২৫টাকায় ৫জিবি (সোশ্যাল প্যাক) ৩দিন নিতে ডায়াল *21291*825# | PROMO | SMS | ANNOTATOR-REVIEWED |
| 3 | আজই ৮জিবি   (Social Pack ) ৩দিন ৫০টাকায় কিনতে ডায়াল *21291*895# | আজই ৮জিবি (Social Pack ) ৩দিন ৫০টাকায় কিনতে ডায়াল *21291*895# | PROMO | SMS | ANNOTATOR-REVIEWED |
| 4 | এয়ারটেলে   সেরা রেট! ৪২টাকা রিচার্জে ৪৫প/মি+ট্যাক্স,মেয়াদ ১৫দিন | এয়ারটেলে সেরা রেট! ৪২টাকা রিচার্জে ৪৫প/মি+ট্যাক্স,মেয়াদ ১৫দিন | PROMO | SMS | ANNOTATOR-REVIEWED |
| 5 | এয়ারটেলে ডায়ালে আজ৬জিবি - ৳৯০ মেয়াদ ৩০দিন *212*690# | এয়ারটেলে ডায়ালে আজ৬জিবি - ৳৯০ মেয়াদ ৩০দিন *212*690# | PROMO | SMS | ANNOTATOR-REVIEWED |

### `Phishing URLs.csv` (`url`, `Type`)

| # | url | Type |
|---:|---|---|
| 1 | `https://docs.google.com/presentation/d/e/2PACX-1vTVj7OXwAUKJDv57jBmVg8eWFIUvTQ3c0-F1gPD_G5CwsQzOf3aelTqo4q42FIlqbHODnIlx2-Lx3Cf/pub?start=false&loop=false&delayms=3000&slide=id.p` | Phishing |
| 2 | `https://btttelecommunniccatiion.weeblysite.com/` | Phishing |
| 3 | `https://kq0hgp.webwave.dev/` | Phishing |
| 4 | `https://brittishtele1bt-69836.getresponsesite.com/` | Phishing |
| 5 | `https://bt-internet-105056.weeblysite.com/` | Phishing |

### `train-00000-of-00001.parquet` (`label`, `text`, `source`)

The first five rows exactly match `bipod_erao_dataset.csv` above; pandas equality comparison confirmed that both tables match across all rows, columns, and row order. `backend/convert.py` also reads this Parquet file and writes that CSV.

### `train-00000-of-00001 (1).parquet` (`sms`, `label`)

| # | sms | label |
|---:|---|---:|
| 1 | Go until jurong point, crazy.. Available only in bugis n great world la e buffet... Cine there got amore wat... | 0 |
| 2 | Ok lar... Joking wif u oni... | 0 |
| 3 | Free entry in 2 a wkly comp to win FA Cup final tkts 21st May 2005... | 1 |
| 4 | U dun say so early hor... U c already then say... | 0 |
| 5 | Nah I don't think he goes to usf, he lives around here though | 0 |

## Text, URL, labels, and language

- **`bipod_erao_dataset.csv` and its identical Parquet copy:** `text` is the message column, `label` is the classification column, and `source` has `Banglish` (1,261), `Bengali` (1,253), `English` (1,214), and `CodeMix` (1,175). A Unicode-script check found Bengali-script characters in 2,396 texts and both Bengali and Latin letters in 1,690. This supports Bengali/English/script-mixed content; the language categories themselves come from the dataset’s `source` values.
- **`BTTC.csv`:** `Text` is the original message and `Text_Clean` is its cleaned counterpart; `Label` is the class. All 10,283 messages contain Bengali-script characters; 7,657 also contain Latin letters. This supports Bengali messages with Latin-script/English code-mixing. The data does not provide a Banglish category, so script counts alone cannot establish Banglish.
- **`Phishing URLs.csv`:** `url` is the URL and `Type` is its class. URLs use Latin characters; message-language classification is not applicable.
- **`train-00000-of-00001.parquet`:** same message, label, and language information as the identical custom CSV.
- **`train-00000-of-00001 (1).parquet`:** `sms` is the message and integer `label` is the class. Sample rows are English/Latin-script SMS; no Bangla-script text was found. There is no language field.

Labels are not interchangeable. `smish` appears to denote smishing, `normal` ordinary messages, and `promo` promotional messages; `BTTC.csv` explicitly separates `HAM`, `PROMO`, and `SPAM`. The integer labels in the SMS Parquet have no accompanying mapping/metadata. The samples suggest `0` may be ordinary and `1` spam, but this should be verified from authoritative dataset documentation before mapping them. `SPAM` must not be assumed to mean phishing, and `PROMO` must not be treated as phishing.

## Duplicates, balance, and compatibility

- The custom CSV and `train-00000-of-00001.parquet` are exact duplicate datasets; using both would duplicate all 4,903 records.
- `train-00000-of-00001 (1).parquet` has 403 repeated full rows (7.23% of rows), leaving 5,171 unique SMS strings. Its class distribution is imbalanced: label `0` is 86.60% and `1` is 13.40%.
- `Phishing URLs.csv` has 2 repeated full rows (54,805 distinct URLs), a negligible duplicate rate, but contains no non-phishing examples.
- `bipod_erao_dataset.csv` and `BTTC.csv` share 12 exact message texts. All are `promo` in the custom dataset; BTTC labels 5 `PROMO` and 7 `HAM`. This is a label/taxonomy disagreement worth reviewing, especially before combining datasets. There are no conflicting labels for repeated normalized texts within either file individually.
- Custom message classes are moderately uneven (`smish` 40.10%, `normal` 35.53%, `promo` 24.37%). BTTC classes are also moderately uneven (`HAM` 37.97%, `PROMO` 35.93%, `SPAM` 26.10%). The URL file is single-class and the integer-label SMS file is notably imbalanced.

## Data quality issues and recommendations

Before preprocessing or using these sources together, remove the duplicate CSV/Parquet copy from the planned input list; review repeated SMS records; inspect the 12 cross-dataset disagreements; establish a documented label mapping without collapsing Spam, Promo, Smishing, Phishing, and Legitimate/Ham; and preserve source/provenance fields. The SMS Parquet’s integer labels need authoritative interpretation. Review samples/annotations for noise and verify whether messages that contain URLs have a separate message label versus URL label. For evaluation, avoid placing identical or near-identical messages across train and test splits.

**A. Message detection:** `bipod_erao_dataset.csv` is the most directly aligned bilingual candidate because it has message text, explicit `smish`/`normal`/`promo` categories, and Bengali/English/Banglish/CodeMix source tags. Its identical Parquet copy adds no data. `BTTC.csv` is a useful separate Bengali message source with `HAM`/`PROMO`/`SPAM` labels, but the overlap disagreements and distinct taxonomy require review before any label alignment. The integer-label SMS Parquet can be an English SMS spam/ham candidate only after its label mapping and provenance are verified. Preserve `PROMO` as its own class unless reviewed evidence supports a different annotation.

**B. URL detection:** `Phishing URLs.csv` is the only direct URL-labeled dataset and can serve as a phishing-positive URL collection after duplicate and provenance review. It is **not sufficient by itself for supervised phishing-vs-legitimate classification** because it contains only phishing labels; verified legitimate URL examples are needed. Do not infer URL legitimacy/phishing labels solely from a message’s Spam, Promo, or Smishing label.
