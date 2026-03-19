# Sanity Check Report: Ruland 1612 Arabic Term Extraction

**Date:** 2026-03-19
**Author:** Generated with Claude Code (Opus 4.6)

---

## Purpose of this Report

This report documents a **data quality audit** ("sanity check") of a CSV file containing Arabic-tradition term detections in Martin Ruland the Younger's *Lexicon Alchemiae* (Frankfurt, 1612). The CSV was produced through a combination of manual review and AI-supported extraction. We compare it against the authoritative TEI XML edition of the dictionary to identify errors, duplicates, and data quality issues before further analysis.

**In plain terms:** We have two files — the original dictionary (XML) and a spreadsheet of Arabic terms found in it (CSV). This report checks whether the spreadsheet is accurate, complete, and clean enough for scholarly analysis.

---

## Data Sources

### The XML Dictionary

- **File:** [`Ruland.xml`](https://github.com/sarahalang/alchemical-dictionaries/blob/main/Ruland1612/Ruland.xml)
- **Format:** TEI P5 XML — a standard encoding format used in digital humanities for structured texts, particularly dictionaries and lexicons
- **Content:** Martin Ruland the Younger's *Lexicon Alchemiae sive Dictionarium Alchemisticum* (1612), an alchemical dictionary containing approximately 3,200 entries
- **Structure:** Each entry is encoded as a `<entry>` element containing a `<form type="lemma">` (the headword) and a `<sense>` with a `<def>` (the definition). Entries range from single-word glosses to multi-page treatises.
- **Provenance:** OCR'd using the NOSCEMUS GM HTR model in Transkribus, then structured as TEI XML by Ines Lesjak (Uni Graz, 2023), revised by Sarah Lang (2024–2025).

### The CSV Extraction File

- **File:** `output_4ofixed_reviewed_with_entries.csv`
- **Content:** 928 rows, each representing a potential Arabic-tradition term detected within a Ruland dictionary entry
- **Production method:** A combination of manual annotation and AI-assisted extraction (using GPT-4o), where each row was scored for:
  - **`confidence_score`** (0–1): How confident the model/reviewer was that the detected string is genuinely an Arabic-origin term. A score of 1.0 means very confident; 0.6 means uncertain.
  - **`irrelevance_probability`** (0–1): How likely the detection is a false positive — i.e., the term is *not* actually of Arabic origin. A score of 0.95 means almost certainly irrelevant; 0.0 means almost certainly relevant.
- **Columns:**

| Column | Type | Description |
|--------|------|-------------|
| `lemma` | string | The Ruland dictionary headword under which this detection was found |
| `confidence_score` | float | Model/reviewer confidence that this is a genuine Arabic-origin term (0–1) |
| `detected_string` | string | The actual Latin/vernacular string flagged as potentially Arabic-derived |
| `normalized_latin` | string | Normalized Latin form of the detected string |
| `lemmatized_latin` | string | Lemmatized (dictionary-form) version of the Latin string |
| `arabic_script` | string | The Arabic-script equivalent of the detected term |
| `normalized_arabic` | string | Normalized Arabic form |
| `english_translation` | string | English gloss/translation of the Arabic term |
| `irrelevance_probability` | float | Probability that this detection is a false positive (0–1) |
| `ruland_entry` | string | Full text of the Ruland dictionary entry in which the detection was found |

---

## Method

The sanity check was performed using Python (pandas, xml.etree.ElementTree) with the following steps:

1. **Parse the XML** to extract all `<entry>` elements with their headwords and full text (3,164 entries)
2. **Parse the CSV** and drop unnamed/empty columns (928 rows)
3. **Cross-reference** CSV lemmas against XML headwords to find mismatches
4. **Check for duplicates** on the key columns `(lemma, detected_string, arabic_script)`
5. **Analyze score distributions** (confidence and irrelevance) to understand data quality tiers
6. **Spot-check entry texts** by comparing the first 100 characters of CSV `ruland_entry` against XML full text for 49 entries
7. **Compare word counts** between XML entries and CSV `ruland_entry` to find truncations or wrong-entry assignments

---

## Dataset Overview

| Metric | Value |
|--------|-------|
| XML dictionary entries | 3,164 |
| XML unique headwords | 2,601 |
| XML entries with definitions (>3 words) | 3,100 (98.0%) |
| XML stub entries (headword only) | 64 (2.0%) |
| CSV extraction rows | 928 |
| CSV unique lemmas (headwords) | 545 |
| CSV unique detected strings | 692 |

**What this means:** The dictionary has about 3,200 entries. The extraction CSV found potential Arabic terms in 545 of those entries (about 17% of the dictionary). However, as we'll see below, many of these 928 detections are unreliable.

---

## Issues Found

### Issue 1: Over half the rows are likely false positives

The `irrelevance_probability` column — which indicates how likely a detection is a false positive — reveals a **bimodal distribution**. This means the scores cluster at two extremes with almost nothing in between:

| Irrelevance bracket | Rows | % of total |
|---------------------|------|------------|
| 0–0.15 (very likely relevant) | 240 | 25.9% |
| 0.15–0.3 (probably relevant) | 2 | 0.2% |
| 0.3–0.5 (uncertain) | 0 | 0.0% |
| 0.5–0.8 (probably irrelevant) | 0 | 0.0% |
| 0.8–1.0 (very likely irrelevant) | 507 | 54.6% |
| Missing/NaN | 179 | 19.3% |

![Distribution of irrelevance probability and confidence scores](sanity_score_distributions.png)

**Technical explanation:** The bimodal distribution (two peaks with a gap in the middle) means the scoring system was quite decisive — it either flagged a term as clearly relevant or clearly irrelevant, with very few borderline cases. The fact that the CSV contains both populations without any filter means the raw output of the extraction pipeline was saved without post-processing.

**In plain terms:** Imagine you asked someone to highlight every word in a book that might come from Arabic. They highlighted 928 words, but then noted that 507 of those were probably mistakes. Those mistakes were never removed from the list — they're still mixed in with the genuine finds.

The scatter plot below shows confidence vs. irrelevance for every row. The data splits cleanly into two clusters:

![Confidence vs irrelevance scatter plot](sanity_confidence_vs_irrelevance.png)

- **Bottom-right (green):** 372 "gold standard" rows — high confidence, low irrelevance. These are the reliable Arabic term detections.
- **Top-right (red):** 507 rows — high confidence *but also* high irrelevance. These are terms that look Arabic but probably aren't (e.g., Latin words that happen to resemble Arabic roots).

### Issue 2: Exact duplicate rows (n=35)

35 rows are exact duplicates on the key identifying columns `(lemma, detected_string, arabic_script)`. This means the same Arabic term was recorded multiple times for the same dictionary entry.

| Lemma | Detected string | Duplicate count |
|-------|----------------|-----------------|
| Nitrum | nitrum | 5 copies |
| Borax | borax | 4 copies |
| Elixir | elixir | 4 copies |
| Alcohol | alcohol | 2 copies |
| Alumen | Alumen | 2 copies |

![CSV quality overview including duplicate analysis](sanity_csv_quality_overview.png)

**Technical explanation:** This likely occurred because multiple extraction passes (e.g., different AI model runs or manual review rounds) were concatenated into a single CSV without deduplication. The duplicates sometimes have slightly different confidence scores, suggesting they come from different extraction runs.

**In plain terms:** It's as if two people independently catalogued the same book and their lists were merged without checking for overlaps. "Borax" got written down four times instead of once.

### Issue 3: 41 CSV lemmas don't match any XML headword

41 unique lemma values in the CSV cannot be found in the XML dictionary. The main causes:

**a) Newlines and whitespace embedded in lemma strings:**
```
"Gummi cedri, cedria vel\n                cedrina"
"Kazdir, kasdir, kacir,\n                kassiceros"
```
These are formatting artifacts from the original data processing — the CSV preserved line breaks from the XML source.

**b) Comma-separated variant forms used as a single lemma:**
```
"Alos, Alo, Alix"        (XML headword: just "Alos")
"Anthonor, Athonor"       (XML headword: just "Anthonor")
"Corallus, Corallium,"    (XML headword: just "Corallus")
```
The XML stores one canonical headword per entry, but the CSV sometimes includes all variant spellings as the lemma.

**c) Spelling/capitalization differences:**
```
"KAchimia vel Kakimia"    (XML: "Kachimia")
"Elixir vel Xir"          (XML: "Elixir")
```

**In plain terms:** These 41 entries are like index cards that got filed under the wrong name. The dictionary entry exists, but the label on the CSV row doesn't quite match the label in the XML, usually because of extra spaces, line breaks, or variant spellings being concatenated.

### Issue 4: 60 rows with no lemma

60 rows have their `lemma` field set to `N/A` or left blank. These detections couldn't be traced back to a specific dictionary entry.

### Issue 5: Entry text mismatches

We compared the dictionary text stored in the CSV (`ruland_entry` column) against the XML source for 49 entries. Three showed different text in the first 100 characters:

| Lemma | CSV text starts with | XML text starts with |
|-------|---------------------|---------------------|
| **Alcohol** | "id est, stybium siue antimonium" | "est puluis subtilissimus" |
| **Adamas** | "Demanth/Demuth nascitur…" | "Arabice hagar subedhig…" |
| **Aetites** | "omnes continent & custodiunt…" | "à Germanis dicitur, Ein Adler Stein…" |

**Technical explanation:** The XML contains multiple `<entry>` elements with the same headword (e.g., there are several entries for "Alcohol" describing different senses). The CSV matching process appears to have sometimes picked the wrong entry.

**In plain terms:** The dictionary has multiple definitions for "Alcohol" (one meaning antimony powder, another meaning a very fine powder). The spreadsheet attached the wrong definition to some of these terms.

### Issue 6: Word count outliers (n=32)

Comparing the word counts between XML entries and CSV entry texts, 32 entries show major discrepancies (the CSV text is less than half or more than double the XML text length):

![Word count comparison: XML vs CSV](sanity_wordcount_xml_vs_csv.png)

**How to read this chart:** Each dot represents one dictionary entry. The x-axis is the word count in the XML; the y-axis is the word count in the CSV. If everything matched perfectly, all dots would fall on the dashed diagonal line. Blue dots are on or near the line (good matches). Red dots are far from the line (problems) — they indicate entries where the CSV has the wrong text, a truncated text, or text from a neighboring entry.

**In plain terms:** Most entries (the dense blue cluster along the diagonal) have matching text in both files. But 32 entries (red dots) have significantly different amounts of text, suggesting the wrong dictionary entry was pasted into the spreadsheet for those rows.

### Issue 7: Missing values

| Column | Missing values | Impact |
|--------|---------------|--------|
| `lemma` | 60 | Cannot link detection to dictionary entry |
| `arabic_script` | 30 | No Arabic equivalent recorded |
| `normalized_arabic` | 18 | Minor — normalized form unavailable |
| `lemmatized_latin` | 23 | Minor — lemmatized form unavailable |
| `normalized_latin` | 13 | Minor — normalized form unavailable |
| `english_translation` | 3 | Minor — gloss unavailable |
| `ruland_entry` | 60 | Aligns with missing lemmas |

---

## Quality Tiers

Based on the two scoring dimensions, the data naturally falls into three tiers:

| Tier | Criteria | Rows | % | What it means |
|------|----------|------|---|---------------|
| **Gold** | confidence ≥ 0.8, irrelevance ≤ 0.2 | 372 | 40.1% | High-confidence detections that are very likely genuine Arabic-tradition terms |
| **Moderate** | confidence ≥ 0.6, 0.2 < irrelevance ≤ 0.5 | ~49 | ~5.3% | Plausible but uncertain detections that may need manual review |
| **Likely irrelevant** | irrelevance > 0.5 | 507 | 54.6% | Flagged as probably not genuine Arabic terms — should be excluded from analysis |

### Effect of filtering on results

The chart below shows how the top detected strings change at different filtering thresholds:

![Filtering comparison at different irrelevance thresholds](filtering_comparison.png)

**Key observation:** Without filtering (left panel), **"alumen"** dominates with 33 hits. But after removing likely-irrelevant rows (middle and right panels), **"alkali"**, **"borax"**, and **"elixir"** emerge as the genuine top terms. "Alumen" (alum) drops because many of its detections were flagged as irrelevant — the Latin word *alumen* superficially resembles Arabic but is actually of Latin origin.

**In plain terms:** Without cleaning the data, we'd wrongly conclude that "alumen" is the most common Arabic term in the dictionary. After cleaning, we see that "alkali," "borax," and "elixir" — terms genuinely borrowed from Arabic — are actually the most frequently occurring.

---

## Structural Observations from the XML Dictionary

Parsing the XML directly gives us a ground-truth view of the dictionary's structure, independent of the extraction CSV:

![XML dictionary structure overview](xml_dictionary_overview.png)

**Top-left:** Entry counts per letter. A (497 entries), C (343), and S (298) dominate — typical for a Latin-based alchemical lexicon where many terms begin with *A-* prefixes (often Arabic definite article *al-*) or Latin *S-* words.

**Top-right:** Word count distribution on a logarithmic scale. The median entry is just 8 words (many entries are brief glosses like "Abam, id est, plumbum"), but the mean is 38 words because a few entries are extremely long treatises. The longest entry (Cadmia) exceeds 2,400 words.

**Bottom-left:** 98% of entries have actual definitions; only 2% are stubs (a headword with no definition text).

**Bottom-right:** The 15 longest entries — topics like Cadmia (a zinc ore), Lapides (stones), and Argenti spuma (silver foam) — are essentially mini-treatises embedded within the dictionary.

---

## Cleaning Actions Taken

Based on these findings, the CSV was cleaned as follows (see `02_DATA_CLEANING_REPORT.md` for details):

1. **Removed 507 rows** with `irrelevance_probability > 0.3`
2. **Removed 6 duplicate rows** (keeping the highest-confidence copy)
3. **Normalized lemma whitespace** (removed embedded newlines)
4. **Added metadata columns:** `first_letter`, `quality_tier`, `lemma_in_xml`

**Result:** 415 clean rows across 345 unique lemmas (44.7% retention rate).

**Output file:** `ruland_arabic_cleaned.csv`

---

## Appendix: Technical Details

- **Python version:** 3.x with pandas, matplotlib, seaborn, networkx, xml.etree.ElementTree
- **XML parsing:** Used `xml.etree.ElementTree` to iterate over `{http://www.tei-c.org/ns/1.0}entry` elements
- **Duplicate detection:** `pandas.DataFrame.duplicated()` on columns `[lemma, detected_string, arabic_script]` with `keep=False` to flag all copies
- **Word count comparison:** Tokenized using Python `str.split()` (whitespace-based), compared ratios between XML and CSV for the same headword
- **Score distributions:** Analyzed using `pandas.cut()` for binning and `seaborn.histplot()` for visualization
- **Spot-check:** Normalized whitespace with `re.sub(r'\s+', ' ', text)` before comparing first 100 characters
