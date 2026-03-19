#!/usr/bin/env python3
"""
Clean the Ruland Arabic extraction CSV based on sanity check findings.
"""

import re
import pandas as pd
import xml.etree.ElementTree as ET

CSV_PATH = "/Users/slang/Downloads/schreibProjekte-slides/narrowingdown/output_4ofixed_reviewed_with_entries.csv"
XML_PATH = "/tmp/Ruland.xml"
OUTDIR = "/Users/slang/claude/ruland_exploration"

# ── Load data ────────────────────────────────────────────────────
df = pd.read_csv(CSV_PATH)
df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
n_orig = len(df)
print(f"Original CSV: {n_orig} rows, {df['lemma'].nunique()} unique lemmas")

# ── Parse XML for headword lookup ────────────────────────────────
tree = ET.parse(XML_PATH)
root = tree.getroot()
xml_headwords = set()
xml_entries_by_hw = {}
for entry in root.iter("{http://www.tei-c.org/ns/1.0}entry"):
    form_el = entry.find(".//{http://www.tei-c.org/ns/1.0}form[@type='lemma']")
    hw = form_el.text.strip() if form_el is not None and form_el.text else ""
    if hw:
        xml_headwords.add(hw)
        full_text = "".join(entry.itertext()).strip()
        # store first match only (some headwords appear multiple times)
        if hw not in xml_entries_by_hw:
            xml_entries_by_hw[hw] = full_text

# ── Step 1: Remove rows with high irrelevance ───────────────────
# Keep rows where irrelevance <= 0.3, or where irrelevance is NaN
# (NaN rows are the N/A lemma rows — we'll handle those separately)
mask_irr = (df["irrelevance_probability"] <= 0.3) | df["irrelevance_probability"].isna()
df_clean = df[mask_irr].copy()
n_after_irr = len(df_clean)
print(f"After irrelevance filter (<=0.3): {n_after_irr} rows (removed {n_orig - n_after_irr})")

# ── Step 2: Remove N/A and NaN lemmas ────────────────────────────
mask_na = df_clean["lemma"].isna() | (df_clean["lemma"] == "N/A")
n_na = mask_na.sum()
df_clean = df_clean[~mask_na].copy()
print(f"After removing N/A/NaN lemmas: {len(df_clean)} rows (removed {n_na})")

# ── Step 3: Normalize lemma formatting ───────────────────────────
# Remove internal newlines and extra whitespace
df_clean["lemma_original"] = df_clean["lemma"]
df_clean["lemma"] = df_clean["lemma"].apply(
    lambda x: re.sub(r'\s+', ' ', str(x)).strip() if pd.notna(x) else x
)

# ── Step 4: Deduplicate ─────────────────────────────────────────
# Keep row with highest confidence when (lemma, detected_string, arabic_script) duplicates exist
df_clean = df_clean.sort_values("confidence_score", ascending=False)
n_before_dedup = len(df_clean)
df_clean = df_clean.drop_duplicates(subset=["lemma", "detected_string", "arabic_script"], keep="first")
n_dupes_removed = n_before_dedup - len(df_clean)
print(f"After deduplication: {len(df_clean)} rows (removed {n_dupes_removed} duplicates)")

# ── Step 5: Add XML match flag ───────────────────────────────────
df_clean["lemma_in_xml"] = df_clean["lemma"].apply(lambda x: x in xml_headwords)
n_not_in_xml = (~df_clean["lemma_in_xml"]).sum()
print(f"Lemmas not found in XML: {n_not_in_xml}")

# ── Step 6: Add quality tier ────────────────────────────────────
def quality_tier(row):
    conf = row["confidence_score"]
    irr = row["irrelevance_probability"]
    if pd.isna(irr):
        irr = 0  # if it survived the filter, treat as low-irr
    if conf >= 0.8 and irr <= 0.15:
        return "gold"
    elif conf >= 0.7 and irr <= 0.3:
        return "silver"
    else:
        return "bronze"

df_clean["quality_tier"] = df_clean.apply(quality_tier, axis=1)

# ── Step 7: Add first_letter for convenience ─────────────────────
df_clean["first_letter"] = df_clean["lemma"].str[0].str.upper()

# ── Step 8: Sort ─────────────────────────────────────────────────
df_clean = df_clean.sort_values(["lemma", "detected_string"]).reset_index(drop=True)

# ── Save ─────────────────────────────────────────────────────────
# Select columns in a useful order (drop lemma_original if it matches lemma)
out_cols = [
    "lemma", "first_letter", "detected_string", "normalized_latin", "lemmatized_latin",
    "arabic_script", "normalized_arabic", "english_translation",
    "confidence_score", "irrelevance_probability", "quality_tier",
    "lemma_in_xml", "ruland_entry"
]
out_cols = [c for c in out_cols if c in df_clean.columns]
df_out = df_clean[out_cols]

out_path = f"{OUTDIR}/ruland_arabic_cleaned.csv"
df_out.to_csv(out_path, index=False)
print(f"\nCleaned CSV saved: {out_path}")
print(f"  {len(df_out)} rows, {df_out['lemma'].nunique()} unique lemmas")

# ── Summary stats ────────────────────────────────────────────────
print(f"\nQuality tier breakdown:")
print(df_out["quality_tier"].value_counts().to_string())

print(f"\nTop 15 detected strings in cleaned data:")
print(df_out["detected_string"].value_counts().head(15).to_string())

print(f"\nCleaning summary:")
print(f"  Original rows:            {n_orig}")
print(f"  Removed (high irr):       {n_orig - n_after_irr}")
print(f"  Removed (N/A lemmas):     {n_na}")
print(f"  Removed (duplicates):     {n_dupes_removed}")
print(f"  Final rows:               {len(df_out)}")
print(f"  Retention rate:           {100*len(df_out)/n_orig:.1f}%")
