# Data Cleaning Report: Ruland Arabic Extraction CSV

**Date:** 2026-03-19
**Author:** Generated with Claude Code (Opus 4.6)
**Prerequisite:** See `01_SANITY_CHECK_REPORT.md` for the sanity check that motivated this cleaning.

---

## Purpose

This report documents the cleaning steps applied to `output_4ofixed_reviewed_with_entries.csv` to produce `ruland_arabic_cleaned.csv` — a filtered, deduplicated, and annotated version of the Arabic term extraction data suitable for scholarly analysis.

**In plain terms:** The original spreadsheet of Arabic terms found in Ruland's dictionary contained duplicates, false positives, and formatting errors. This report explains exactly what was removed, why, and what the cleaned data looks like.

---

## Input and Output

| | Input CSV | Output CSV |
|--|-----------|------------|
| **File** | `output_4ofixed_reviewed_with_entries.csv` | `ruland_arabic_cleaned.csv` |
| **Rows** | 928 | 415 |
| **Unique lemmas** | 545 | 345 |
| **Unique detected strings** | 692 | 368 |
| **Retention rate** | — | 44.7% |

---

## Cleaning Steps

### Step 1: Remove likely-irrelevant rows (−507 rows)

**What was done:** All rows with `irrelevance_probability > 0.3` were removed.

**Why 0.3?** The irrelevance scores are bimodal — they cluster at 0.0–0.15 (relevant) and 0.8–1.0 (irrelevant), with essentially no values between 0.3 and 0.7. Choosing 0.3 as the threshold captures all clearly relevant rows and the tiny number of borderline cases, while excluding the entire irrelevant cluster. Any threshold between 0.3 and 0.7 would produce exactly the same result due to the gap in the distribution.

**What `irrelevance_probability` means:** This score (ranging from 0 to 1) represents the estimated probability that a detected term is *not* actually of Arabic origin — that it's a false positive. A score of 0.0 means "almost certainly a real Arabic term"; a score of 0.95 means "almost certainly not Arabic." It was computed during the extraction pipeline as a second-pass quality assessment.

**Effect:** 507 rows removed. These were terms like Latin *roc*, *rub*, *sal*, and *alumen* that superficially resemble Arabic words but are not genuinely Arabic-derived. Their removal changed the ranking of top detected terms significantly (see `02_EXPLORATION_VISUALIZATIONS.md`, Section 7).

### Step 2: Remove N/A and missing lemmas (−0 rows)

**What was done:** Rows where the `lemma` column was `N/A` or `NaN` (blank) were removed.

**Why:** These rows represent detections that couldn't be traced to any specific dictionary entry. Without a lemma, the detection cannot be contextualized within the dictionary structure.

**Effect:** 0 additional rows removed (all N/A lemma rows had already been removed in Step 1, since they also had high irrelevance scores).

### Step 3: Normalize lemma formatting

**What was done:** Internal newlines (`\n`) and excess whitespace within lemma strings were collapsed to single spaces using the regular expression `\s+ → ' '`.

**Why:** Some lemma values contained embedded line breaks from the original XML source, e.g.:
```
"Gummi cedri, cedria vel\n                cedrina"
→ "Gummi cedri, cedria vel cedrina"
```

**Effect:** No rows removed; lemma strings made consistent for downstream matching.

### Step 4: Deduplicate (−6 rows)

**What was done:** Rows with identical values in `(lemma, detected_string, arabic_script)` were deduplicated. When multiple copies existed, the row with the **highest `confidence_score`** was kept.

**Method:** `pandas.DataFrame.drop_duplicates(subset=[...], keep='first')` after sorting by `confidence_score` descending.

**Why:** Duplicate rows likely arose from merging multiple extraction passes without deduplication (e.g., separate AI model runs that both detected "borax" in the "Borax" entry).

**Effect:** 6 duplicate rows removed. The remaining duplicates from the original 35 had already been removed by the irrelevance filter in Step 1.

### Step 5: Add metadata columns

Three new columns were added for convenience:

| Column | Description | Values |
|--------|-------------|--------|
| `first_letter` | First letter of the lemma, uppercased | A–Z |
| `quality_tier` | Quality classification based on scores | gold, silver, bronze |
| `lemma_in_xml` | Whether the lemma matches an XML headword | True/False |

**Quality tier definitions:**

| Tier | Criteria | Meaning |
|------|----------|---------|
| **Gold** | confidence ≥ 0.8 AND irrelevance ≤ 0.15 | Highly reliable detection — both the extraction and the evaluation agreed this is a genuine Arabic term |
| **Silver** | confidence ≥ 0.7 AND irrelevance ≤ 0.3 | Probably reliable, but either confidence or irrelevance is slightly outside the ideal range |
| **Bronze** | Everything else that survived filtering | Survived the irrelevance filter but has lower confidence — worth including but should be treated with caution |

---

## Result Summary

### Quality tier breakdown

| Tier | Rows | % |
|------|------|---|
| Gold | 366 | 88.2% |
| Silver | 39 | 9.4% |
| Bronze | 10 | 2.4% |

The overwhelming majority (88%) of rows in the cleaned dataset are gold-tier — high-confidence, low-irrelevance detections.

### XML match status

- **379 rows** (91.3%) have a lemma that matches an XML headword exactly
- **36 rows** (8.7%) have lemmas not found in the XML, mostly due to multi-word lemmas with variant forms (e.g., "Elixir vel Xir", "Anthonor, Athonor")

### Top 15 detected strings in cleaned data

| Detected string | Count |
|----------------|-------|
| alkali | 15 |
| borax | 11 |
| alumen | 6 |
| nitrum | 5 |
| elixir | 5 |
| naphtha | 4 |
| mumia | 4 |
| colcotar | 4 |
| alcali | 3 |
| alcool | 3 |
| furnus | 3 |
| gummi | 3 |
| balsamus | 3 |
| chalcanthum | 3 |
| arsenicum | 2 |

### Columns in cleaned CSV

| Column | Description |
|--------|-------------|
| `lemma` | Ruland dictionary headword (whitespace-normalized) |
| `first_letter` | Initial letter of the lemma (A–Z) |
| `detected_string` | The Latin/vernacular string detected as Arabic-derived |
| `normalized_latin` | Standardized Latin form |
| `lemmatized_latin` | Lemmatized (dictionary) form of the Latin string |
| `arabic_script` | Arabic-script equivalent |
| `normalized_arabic` | Normalized Arabic form |
| `english_translation` | English gloss |
| `confidence_score` | Model/reviewer confidence (0–1) |
| `irrelevance_probability` | False positive probability (0–1) |
| `quality_tier` | gold / silver / bronze |
| `lemma_in_xml` | True if lemma matches an XML headword |
| `ruland_entry` | Full text of the dictionary entry |

---

## What Was Lost

It's important to document what the cleaning removed, not just what it kept:

- **507 false-positive detections** — terms flagged as Arabic but determined to be Latin, Greek, or German. Examples: *roc* (a general suffix), *rub* (common Latin/German), *alumen* (Latin for alum, not Arabic), *sal* (Latin for salt).
- **6 duplicate rows** — second/third/fourth copies of the same detection for the same entry.
- **0 N/A lemma rows** — these had already been caught by the irrelevance filter.

**What was NOT removed:**
- Rows with lemmas not found in the XML (36 rows) — these are formatting mismatches, not quality issues. The detections themselves are valid.
- Rows with missing `arabic_script` or `normalized_arabic` — incomplete metadata is not a reason to discard an otherwise valid detection.
- Rows with word-count outliers between XML and CSV — the entry text mismatch is in the `ruland_entry` column and doesn't invalidate the detection itself.

---

## Reproduction

```bash
python3 clean_ruland_csv.py
```

The script reads from:
- `output_4ofixed_reviewed_with_entries.csv` (the extraction CSV)
- `Ruland.xml` (the TEI dictionary, for XML matching)

And writes to:
- `ruland_arabic_cleaned.csv`
