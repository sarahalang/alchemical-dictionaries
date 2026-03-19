# Sanity Check Report: Ruland 1612 Arabic Term Extraction CSV

**Date:** 2026-03-19
**Source XML:** `Ruland.xml` from [sarahalang/alchemical-dictionaries](https://github.com/sarahalang/alchemical-dictionaries/blob/main/Ruland1612/Ruland.xml)
**Source CSV:** `output_4ofixed_reviewed_with_entries.csv`
**Visualizations:** `/Users/slang/claude/ruland_exploration/`

---

## 1. Dataset Overview

| Metric | Value |
|--------|-------|
| XML dictionary entries | 3,164 |
| XML unique headwords | 2,601 |
| XML entries with definitions (>3 words) | 3,100 (98.0%) |
| XML stub entries | 64 (2.0%) |
| CSV extraction rows | 928 |
| CSV unique lemmas | 545 |
| CSV unique detected strings | 692 |
| CSV columns | lemma, confidence_score, detected_string, normalized_latin, lemmatized_latin, arabic_script, normalized_arabic, english_translation, irrelevance_probability, ruland_entry |

---

## 2. Issues Found

### 2a. Bimodal irrelevance distribution — majority of rows likely irrelevant

The `irrelevance_probability` column has a stark bimodal distribution with almost no values between 0.3 and 0.7:

| Irrelevance bracket | Rows | % |
|---------------------|------|---|
| 0–0.15 | 240 | 25.9% |
| 0.15–0.3 | 2 | 0.2% |
| 0.3–0.5 | 0 | 0.0% |
| 0.5–0.8 | 0 | 0.0% |
| 0.8–1.0 | 507 | 54.6% |
| *(missing/NaN)* | 179 | 19.3% |

**Impact:** Over half the rows are flagged as irrelevant but were never filtered out. The CSV appears to contain both accepted and rejected detections without distinction.

**Visualization:** `sanity_score_distributions.png`, `sanity_confidence_vs_irrelevance.png`

### 2b. Exact duplicate rows (n=35)

35 rows are exact duplicates on the key columns `(lemma, detected_string, arabic_script)`. Notable examples:

| Lemma | Detected string | Occurrences |
|-------|----------------|-------------|
| Nitrum | nitrum | 5 |
| Borax | borax | 4 |
| Elixir | elixir | 4 |
| Alcohol | alcohol | 2 |
| Alumen | Alumen | 2 |
| Aquila | Salmiax | 2 |
| Talcum | talcum | 2 |

These appear to be rows from different extraction passes that were concatenated without deduplication.

**Visualization:** `sanity_csv_quality_overview.png` (bottom-right panel)

### 2c. CSV lemmas not found in XML (n=41)

41 unique lemma values from the CSV do not match any XML headword. The causes are:

1. **Multi-word lemmas with embedded newlines/whitespace:** e.g. `"Gummi cedri, cedria vel\n                cedrina"`, `"Kazdir, kasdir, kacir,\n                kassiceros"`, `"Anucar\n                     \n                     Ancinar"`
2. **Comma-separated variant forms:** e.g. `"Alos, Alo, Alix"`, `"Botin, butimo,"`, `"Anthonor, Athonor"`, `"Corallus, Corallium,"`
3. **Slight spelling differences:** e.g. `"KAchimia vel Kakimia"` (capitalization), `"Elixir vel Xir"` vs `"Elixir"`

The XML uses single headwords in `<form type="lemma">` tags, while the CSV sometimes includes variant forms or multi-line headwords.

**First 30 missing:** Alcone, Alembic, Aliocab, Alnec Allenec, Alos Alo Alix, Altingat, Alumen alafuri vel alafor, Anthonor Athonor, Anucar Ancinar, Atincar vel Atinkar, Azagor, Azemasor, Balneum roris vel roritum, Barnabus barnaas, Botin butimo, Calcanthos vel calcanthum significat, Calmet cosmec, Cibur vel chybur, Cinis clauellatus, Corallus Corallium, Dragantum dragantium, Elixir vel Xir, Elixir Elei, Guma gumi, Gummi cedri cedria vel cedrina, Hasacium, KAchimia vel Kakimia, Kamar vel Camar, Kazdir kasdir kacir kassiceros, Kybrius kebrick

### 2d. Rows with missing/N/A lemma (n=60)

60 rows have `lemma` set to `N/A` or `NaN`. These have no associated dictionary entry and appear to be detections that couldn't be mapped to a specific headword.

### 2e. Entry text mismatches between CSV and XML

Spot-checking 49 entries for which both CSV `ruland_entry` and XML text exist:

- **3 entries had different text in the first 100 characters**
- Most notable: **Alcohol** — the CSV has `"id est, stybium siue antimonium"` while the XML has `"est puluis subtilissimus"`. This indicates a wrong entry was attached (the XML contains multiple entries starting with "Alcohol" for different senses).
- **Adamas** — different opening text, suggesting a different sub-entry was matched.
- **Aetites** — offset in the text, likely a sub-entry issue.

**Visualization:** `sanity_wordcount_xml_vs_csv.png`

### 2f. Word count outliers (n=32)

Comparing word counts between XML entries and CSV `ruland_entry` text, 32 entries have a ratio < 0.5 or > 2.0 (i.e. the CSV text is less than half or more than double the XML text). This indicates:

- Some CSV rows contain text from the wrong entry
- Some entries may have been truncated in the CSV
- Some may include text from adjacent entries

**Visualization:** `sanity_wordcount_xml_vs_csv.png` (red dots)

### 2g. Missing values

| Column | Missing values |
|--------|---------------|
| lemma | 60 |
| normalized_latin | 13 |
| lemmatized_latin | 23 |
| arabic_script | 30 |
| normalized_arabic | 18 |
| english_translation | 3 |
| ruland_entry | 60 |

---

## 3. Quality Tiers

Based on the confidence and irrelevance scores, the data falls into clear tiers:

| Tier | Criteria | Rows | % | Description |
|------|----------|------|---|-------------|
| Gold standard | conf ≥ 0.8, irr ≤ 0.2 | 372 | 40.1% | High-confidence, low-irrelevance detections |
| Moderate | conf ≥ 0.6, 0.2 < irr ≤ 0.5 | ~49 | ~5.3% | Possibly valid but less certain |
| Likely irrelevant | irr > 0.5 | 507 | 54.6% | Flagged as probably not genuine Arabic terms |

**Visualization:** `sanity_confidence_vs_irrelevance.png`

The filtering comparison (`filtering_comparison.png`) shows that the top detected strings change significantly when irrelevant rows are removed:
- **"alumen"** dominates the unfiltered set (33 hits) but drops substantially after filtering — many of its detections are irrelevant
- **"alkali"**, **"borax"**, and **"elixir"** remain the top terms after filtering, suggesting they are genuinely prominent Arabic-tradition terms

---

## 4. Structural Observations from XML

- The dictionary has **3,164 entries** across letters A–Z (no J or U in this Latin-based scheme)
- Letter **A** has the most entries (497), followed by **C** (343) and **S** (298)
- Entry lengths are heavily right-skewed: median = 8 words, mean = 38 words
- The 15 longest entries exceed 1,000 words each (Cadmia, Lapides, Argenti spuma, etc.)
- 98% of entries have definitions; only 64 are stubs (headword only)

**Visualization:** `xml_dictionary_overview.png`

---

## 5. Recommendations for Cleaning

1. **Filter on irrelevance:** Remove rows with `irrelevance_probability > 0.3` (or at most 0.5)
2. **Deduplicate:** Remove exact duplicates on `(lemma, detected_string, arabic_script)`, keeping the row with the highest confidence score
3. **Fix lemma formatting:** Normalize multi-word lemmas by removing newlines and standardizing comma-separated variants
4. **Remove N/A lemmas** or investigate whether they can be matched to XML entries
5. **Verify entry text:** For the 32 word-count outliers, re-match the `ruland_entry` text against the XML

---

## 6. Visualization Index

| File | Description |
|------|-------------|
| `sanity_xml_vs_csv_by_letter.png` | XML entries vs CSV rows per letter; detection rate by letter |
| `sanity_confidence_vs_irrelevance.png` | Scatter of confidence vs irrelevance with quadrant counts |
| `sanity_score_distributions.png` | Histograms of irrelevance and confidence scores |
| `sanity_wordcount_xml_vs_csv.png` | Entry word count: XML vs CSV with outliers flagged |
| `sanity_csv_quality_overview.png` | 4-panel: irrelevance brackets, confidence boxplots, scripts per lemma, duplicates |
| `filtering_comparison.png` | Top detected strings at different irrelevance thresholds |
| `semantic_categories.png` | Arabic terms grouped by semantic domain (all vs reliable) |
| `arabic_density_by_position.png` | Arabic term density across dictionary position (sliding window) |
| `arabic_share_by_entry_length.png` | % of entries with Arabic terms by entry length bucket |
| `cooccurrence_network_latin.png` | Latin co-occurrence network graph |
| `top_strings_quality_coded.png` | Top 30 detected strings color-coded by quality tier |
| `authority_references.png` | Authority mentions in XML; comparison with Arabic-bearing entries |
| `xml_dictionary_overview.png` | Full XML dictionary structure: entries per letter, word count distribution, longest entries |
