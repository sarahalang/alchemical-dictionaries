#!/usr/bin/env python3
"""
Ruland 1612 – Humanities-focused exploration
=============================================
Arabic tradition patterns across the dictionary: etymology, letter sections,
semantic domains, accepted vs rejected terms, and structural trends.
"""

import os, re, textwrap
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from collections import Counter, defaultdict

# ── paths ───────────────────────────────────────────────────────────
XML_PATH = "/tmp/Ruland.xml"
CSV_RAW = "/Users/slang/Downloads/schreibProjekte-slides/narrowingdown/output_4ofixed_reviewed_with_entries.csv"
CSV_CLEAN = "/Users/slang/claude/ruland_exploration/ruland_arabic_cleaned.csv"
OUTDIR = "/Users/slang/claude/ruland_exploration/04_humanities"
os.makedirs(OUTDIR, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.05)
PAL = {
    "blue": "#4C78A8", "orange": "#F58518", "teal": "#72B7B2",
    "red": "#E45756", "green": "#54A24B", "purple": "#B279A2",
    "pink": "#FF9DA6", "brown": "#9D7660", "gray": "#BAB0AC",
    "gold": "#EECA3B", "darkblue": "#2D4A7A",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOAD DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("Loading data…")

# XML
tree = ET.parse(XML_PATH)
root = tree.getroot()
xml_entries = []
for entry in root.iter("{http://www.tei-c.org/ns/1.0}entry"):
    form_el = entry.find(".//{http://www.tei-c.org/ns/1.0}form[@type='lemma']")
    hw = form_el.text.strip() if form_el is not None and form_el.text else ""
    full_text = "".join(entry.itertext()).strip()
    xml_entries.append({
        "headword": hw, "full_text": full_text,
        "word_count": len(full_text.split()),
        "first_letter": hw[0].upper() if hw else "",
    })
xml_df = pd.DataFrame(xml_entries)
xml_df = xml_df[xml_df["first_letter"] != ""]  # drop empty headwords

# CSV (both raw and clean)
raw_df = pd.read_csv(CSV_RAW)
raw_df = raw_df.loc[:, ~raw_df.columns.str.startswith("Unnamed")]
clean_df = pd.read_csv(CSV_CLEAN)

# Add first_letter to raw if needed
raw_df["first_letter"] = raw_df["lemma"].dropna().str.strip().str[0].str.upper()

print(f"  XML: {len(xml_df)} entries")
print(f"  Raw CSV: {len(raw_df)} rows")
print(f"  Clean CSV: {len(clean_df)} rows")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 1: LETTER SECTION PROFILES
# What does each letter section look like in terms of size, entry
# length, and Arabic density?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 1: Letter section profiles…")

letters_order = sorted(xml_df["first_letter"].unique())

# Per-letter stats from XML
xml_letter = xml_df.groupby("first_letter").agg(
    n_entries=("headword", "count"),
    median_wc=("word_count", "median"),
    mean_wc=("word_count", "mean"),
    max_wc=("word_count", "max"),
).reindex(letters_order)

# Arabic detections per letter (clean)
arabic_per_letter = clean_df.groupby("first_letter").agg(
    n_detections=("detected_string", "count"),
    n_unique_lemmas=("lemma", "nunique"),
    n_unique_terms=("detected_string", "nunique"),
).reindex(letters_order).fillna(0)

# Merge
profile = xml_letter.join(arabic_per_letter)
profile["arabic_lemma_pct"] = 100 * profile["n_unique_lemmas"] / profile["n_entries"]
profile["detections_per_100"] = 100 * profile["n_detections"] / profile["n_entries"]

fig, axes = plt.subplots(3, 1, figsize=(16, 14), sharex=True)

# Panel 1: entries per letter + arabic lemmas
ax = axes[0]
x = np.arange(len(letters_order))
w = 0.35
ax.bar(x - w/2, profile["n_entries"], w, label="total XML entries", color=PAL["blue"])
ax.bar(x + w/2, profile["n_unique_lemmas"], w, label="entries with Arabic terms", color=PAL["orange"])
ax.set_ylabel("number of entries")
ax.set_title("Dictionary Size and Arabic Presence by Letter Section")
ax.legend()
for i, (ne, na) in enumerate(zip(profile["n_entries"], profile["n_unique_lemmas"])):
    if na > 0:
        ax.text(i + w/2, na + 3, f"{int(na)}", ha="center", fontsize=7, color=PAL["orange"])

# Panel 2: % of entries with Arabic + detections per 100 entries
ax = axes[1]
ax.bar(x - w/2, profile["arabic_lemma_pct"], w,
       label="% of entries with Arabic terms", color=PAL["teal"])
ax.bar(x + w/2, profile["detections_per_100"], w,
       label="Arabic detections per 100 entries", color=PAL["red"])
ax.set_ylabel("percentage / rate")
ax.set_title("Arabic Penetration Rate by Letter Section")
ax.legend()
ax.axhline(profile["arabic_lemma_pct"].mean(), ls="--", color=PAL["teal"], alpha=0.5)

# Panel 3: median entry length
ax = axes[2]
ax.bar(x, profile["median_wc"], color=PAL["purple"], alpha=0.7)
ax.set_ylabel("median word count")
ax.set_title("Median Entry Length by Letter Section")
ax.set_xticks(x)
ax.set_xticklabels(letters_order)
ax.set_xlabel("letter section")
for i, v in enumerate(profile["median_wc"]):
    ax.text(i, v + 0.3, f"{v:.0f}", ha="center", fontsize=7)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "letter_section_profiles.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ letter_section_profiles.png")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 2: ACCEPTED vs REJECTED ARABIC DETECTIONS
# What distinguishes a term that was accepted as Arabic from one
# that was rejected?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 2: Accepted vs rejected…")

raw_df["verdict"] = raw_df["irrelevance_probability"].apply(
    lambda x: "accepted" if pd.notna(x) and x <= 0.3 else
              ("rejected" if pd.notna(x) and x > 0.3 else "unknown"))

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Panel 1: accepted vs rejected by letter
ax = axes[0, 0]
verdict_letter = raw_df.groupby(["first_letter", "verdict"]).size().unstack(fill_value=0)
if "unknown" in verdict_letter.columns:
    verdict_letter = verdict_letter.drop(columns="unknown")
verdict_letter = verdict_letter.reindex(letters_order).fillna(0)
verdict_letter.plot(kind="bar", stacked=True, ax=ax,
                    color=[PAL["green"], PAL["red"]], width=0.7)
ax.set_title("Accepted vs Rejected Arabic Detections by Letter Section")
ax.set_xlabel("letter section")
ax.set_ylabel("number of detections")
ax.legend(["accepted (irr ≤ 0.3)", "rejected (irr > 0.3)"])

# Panel 2: top 20 ACCEPTED terms
ax = axes[0, 1]
accepted = raw_df[raw_df["verdict"] == "accepted"]
top_acc = accepted["detected_string"].value_counts().head(20)
ax.barh(range(len(top_acc)), top_acc.values, color=PAL["green"])
ax.set_yticks(range(len(top_acc)))
ax.set_yticklabels(top_acc.index)
ax.invert_yaxis()
ax.set_title("Top 20 Accepted Arabic Terms")
ax.set_xlabel("count")

# Panel 3: top 20 REJECTED terms
ax = axes[1, 0]
rejected = raw_df[raw_df["verdict"] == "rejected"]
top_rej = rejected["detected_string"].value_counts().head(20)
ax.barh(range(len(top_rej)), top_rej.values, color=PAL["red"])
ax.set_yticks(range(len(top_rej)))
ax.set_yticklabels(top_rej.index)
ax.invert_yaxis()
ax.set_title("Top 20 Rejected Detections (False Positives)")
ax.set_xlabel("count")

# Panel 4: what makes a term accepted vs rejected — word-level features
ax = axes[1, 1]
# Analyze morphological patterns
def morpho_features(s):
    if pd.isna(s):
        return {}
    s = str(s).lower()
    return {
        "starts_with_al": s.startswith("al"),
        "length_short": len(s) <= 4,
        "length_long": len(s) >= 8,
        "contains_k": "k" in s,
        "contains_z": "z" in s,
        "contains_q": "q" in s,
        "uppercase_start": str(s)[0].isupper() if s else False,
    }

feat_data = []
for verdict in ["accepted", "rejected"]:
    subset = raw_df[raw_df["verdict"] == verdict]
    for _, row in subset.iterrows():
        feats = morpho_features(row["detected_string"])
        feats["verdict"] = verdict
        feat_data.append(feats)

feat_df = pd.DataFrame(feat_data)
feat_summary = feat_df.groupby("verdict").mean().T * 100  # percentages
feat_summary = feat_summary[["accepted", "rejected"]]
feat_summary["diff"] = feat_summary["accepted"] - feat_summary["rejected"]
feat_summary = feat_summary.sort_values("diff", ascending=True)

y_pos = np.arange(len(feat_summary))
ax.barh(y_pos - 0.15, feat_summary["accepted"], 0.3, label="accepted", color=PAL["green"])
ax.barh(y_pos + 0.15, feat_summary["rejected"], 0.3, label="rejected", color=PAL["red"])
ax.set_yticks(y_pos)
ax.set_yticklabels([
    "starts with al-", "≤4 characters", "≥8 characters",
    "contains k", "contains z", "contains q", "starts uppercase"
])
ax.set_xlabel("% of terms with feature")
ax.set_title("Morphological Features: Accepted vs Rejected")
ax.legend()

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "accepted_vs_rejected.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ accepted_vs_rejected.png")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 3: ETYMOLOGICAL PATTERNS — AL- PREFIX AND MORPHOLOGY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 3: Etymological patterns…")

def classify_etymology(row):
    """Classify how an Arabic term entered Latin based on its form."""
    ds = str(row.get("detected_string", "")).lower()
    lemma = str(row.get("lemma", "")).lower()
    arabic = str(row.get("arabic_script", ""))

    # al- prefix preserved
    if ds.startswith("al") and len(ds) > 3:
        return "al- prefix preserved"
    # Latin adaptation (headword ≠ detected string, no al-)
    if ds.startswith("at") or ds.startswith("az") or ds.startswith("as"):
        return "al- assimilated (at-, az-, as-)"
    # Personal names
    eng = str(row.get("english_translation", "")).lower()
    if any(n in eng for n in ["avicenna", "jabir", "rhazes", "geber", "serapio"]):
        return "personal name"
    # Direct transliteration (Arabic → Latin with minimal change)
    if ds in ["borax", "elixir", "naphtha", "mumia", "camphor", "saffran",
              "realgar", "talcum", "bezar", "zarnich", "natron", "tutia"]:
        return "direct transliteration"
    # Compound forms
    if " " in ds:
        return "compound / phrase"
    return "other adaptation"

clean_df["etymology_type"] = clean_df.apply(classify_etymology, axis=1)

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Left: overall distribution
ax = axes[0]
etym_counts = clean_df["etymology_type"].value_counts()
colors_etym = [PAL["blue"], PAL["orange"], PAL["teal"], PAL["green"],
               PAL["purple"], PAL["red"]][:len(etym_counts)]
ax.barh(range(len(etym_counts)), etym_counts.values, color=colors_etym)
ax.set_yticks(range(len(etym_counts)))
ax.set_yticklabels(etym_counts.index)
ax.set_xlabel("number of detections")
ax.set_title("How Arabic Terms Entered Latin: Etymology Patterns")
for i, v in enumerate(etym_counts.values):
    ax.text(v + 1, i, str(v), va="center", fontsize=9)

# Right: examples for each type
ax = axes[1]
ax.axis("off")
examples_text = []
for etype in etym_counts.index:
    subset = clean_df[clean_df["etymology_type"] == etype]
    examples = subset["detected_string"].value_counts().head(5).index.tolist()
    examples_text.append(f"▸ {etype}:\n  {', '.join(examples)}")

ax.text(0.05, 0.95, "\n\n".join(examples_text),
        transform=ax.transAxes, fontsize=11, va="top", ha="left",
        fontfamily="monospace", linespacing=1.5)
ax.set_title("Examples for Each Etymology Type")

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "etymology_patterns.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ etymology_patterns.png")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 4: MOST FREQUENT ARABIC TERMS IN CONTEXT
# Show the top terms with their Arabic script, English meaning,
# and which letter sections they appear in
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 4: Most frequent terms in context…")

# Aggregate per detected_string
term_agg = clean_df.groupby("detected_string").agg(
    count=("lemma", "size"),
    n_entries=("lemma", "nunique"),
    arabic=("arabic_script", "first"),
    english=("english_translation", "first"),
    mean_conf=("confidence_score", "mean"),
    letters=("first_letter", lambda x: ",".join(sorted(x.unique()))),
).sort_values("count", ascending=False)

top25 = term_agg.head(25).copy()

fig, ax = plt.subplots(figsize=(14, 10))
y_pos = np.arange(len(top25))
bars = ax.barh(y_pos, top25["count"], color=PAL["orange"], edgecolor="white")
ax.set_yticks(y_pos)
# Show: detected_string (arabic_script) = "english"
labels = []
for term, row in top25.iterrows():
    arabic = str(row["arabic"]) if pd.notna(row["arabic"]) else ""
    english = str(row["english"]) if pd.notna(row["english"]) else ""
    labels.append(f'{term}  ({arabic})')
ax.set_yticklabels(labels, fontsize=9)
ax.invert_yaxis()

# Annotate with english and letter sections
for i, (term, row) in enumerate(top25.iterrows()):
    eng = str(row["english"])[:30] if pd.notna(row["english"]) else ""
    lets = row["letters"]
    ax.text(row["count"] + 0.2, i,
            f'"{eng}"  [{lets}]',
            va="center", fontsize=8, color=PAL["darkblue"])

ax.set_xlabel("number of occurrences in dictionary")
ax.set_title("Top 25 Arabic Terms in Ruland's Lexicon Alchemiae\n(with Arabic script, English meaning, and letter sections)")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "top_terms_in_context.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ top_terms_in_context.png")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 5: SEMANTIC DOMAINS BY LETTER SECTION
# What kinds of Arabic terms appear in which parts of the dictionary?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 5: Semantic domains by letter section…")

DOMAINS = {
    "Minerals & Salts": ["salt", "alum", "vitriol", "sulfur", "sulphur", "borax",
        "antimony", "mercury", "lead", "copper", "iron", "ore", "mineral",
        "alkali", "potash", "soda", "natron", "marcasite", "cinnabar", "talc",
        "arsenic", "orpiment", "realgar", "hematite", "vermilion", "calcium",
        "powder", "calamine", "magnesia"],
    "Organic & Natural": ["oil", "resin", "gum", "wax", "saffron", "turmeric",
        "mummy", "balsam", "aloe", "nutmeg", "sugar", "petroleum", "naphtha",
        "camphor", "amber", "wood", "dye", "plant", "herb", "flower", "tar",
        "pitch", "asphalt", "bitumen", "juniper", "water"],
    "Apparatus & Process": ["alembic", "furnace", "vessel", "flask", "crucible",
        "aludel", "athanor", "drum", "bath", "distill", "calcin", "sublim",
        "filter", "extract", "purif", "leaven", "ferment"],
    "Scholars & Texts": ["avicenna", "jabir", "rhazes", "geber", "hayyan",
        "serapio", "arabic", "draftsman"],
    "Medical & Alchemical": ["elixir", "medicine", "cure", "heal", "poison",
        "bezoar", "remedy", "stone"],
}

def assign_domain(eng):
    if pd.isna(eng):
        return "Unclassified"
    t = str(eng).lower()
    for dom, kws in DOMAINS.items():
        for kw in kws:
            if kw in t:
                return dom
    return "Other"

clean_df["domain"] = clean_df["english_translation"].apply(assign_domain)

# Heatmap: domain × letter section
domain_letter = clean_df.groupby(["first_letter", "domain"]).size().unstack(fill_value=0)
domain_order = list(DOMAINS.keys()) + ["Other", "Unclassified"]
domain_letter = domain_letter.reindex(columns=[d for d in domain_order if d in domain_letter.columns])
domain_letter = domain_letter.reindex(letters_order).fillna(0)

fig, ax = plt.subplots(figsize=(14, 9))
im = ax.imshow(domain_letter.T.values, aspect="auto", cmap="YlOrRd", interpolation="nearest")
ax.set_xticks(range(len(domain_letter.index)))
ax.set_xticklabels(domain_letter.index)
ax.set_yticks(range(len(domain_letter.columns)))
ax.set_yticklabels(domain_letter.columns)
ax.set_xlabel("letter section")
ax.set_ylabel("semantic domain")
ax.set_title("Arabic Term Semantic Domains Across Dictionary Letter Sections")

# Annotate cells
for i in range(len(domain_letter.columns)):
    for j in range(len(domain_letter.index)):
        val = int(domain_letter.T.values[i, j])
        if val > 0:
            ax.text(j, i, str(val), ha="center", va="center",
                    fontsize=8, color="white" if val > 3 else "black")

plt.colorbar(im, ax=ax, label="number of detections", shrink=0.7)
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "semantic_domains_by_letter.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ semantic_domains_by_letter.png")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 6: ARABIC TERMS AND ENTRY LENGTH — DO LONGER ENTRIES ATTRACT
# MORE ARABIC TERMS, AND IS THIS DIFFERENT PER LETTER?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 6: Entry length and Arabic terms per letter…")

# For each XML entry, count Arabic detections
arabic_counts_per_hw = clean_df.groupby("lemma").size().rename("arabic_count")
xml_with_arabic = xml_df.merge(arabic_counts_per_hw, left_on="headword",
                                right_index=True, how="left")
xml_with_arabic["arabic_count"] = xml_with_arabic["arabic_count"].fillna(0)
xml_with_arabic["has_arabic"] = xml_with_arabic["arabic_count"] > 0

# Bin entries
bins = [0, 10, 25, 50, 100, 200, 5000]
labels_bins = ["1–9", "10–24", "25–49", "50–99", "100–199", "200+"]
xml_with_arabic["len_bucket"] = pd.cut(xml_with_arabic["word_count"], bins=bins,
                                        labels=labels_bins, right=False)

# Select most interesting letters
interesting_letters = ["A", "B", "C", "K", "M", "N", "S"]

fig, axes = plt.subplots(2, 4, figsize=(20, 10))
axes = axes.flatten()

# Overall
ax = axes[0]
bucket_stats = xml_with_arabic.groupby("len_bucket").agg(
    total=("headword", "count"),
    with_arabic=("has_arabic", "sum"),
).dropna()
bucket_stats["pct"] = 100 * bucket_stats["with_arabic"] / bucket_stats["total"]
ax.bar(range(len(bucket_stats)), bucket_stats["pct"], color=PAL["orange"])
ax.set_xticks(range(len(bucket_stats)))
ax.set_xticklabels(bucket_stats.index, fontsize=8)
ax.set_title("ALL LETTERS", fontweight="bold")
ax.set_ylabel("% entries with Arabic")
for i, (_, row) in enumerate(bucket_stats.iterrows()):
    ax.text(i, row["pct"] + 0.5, f'{row["pct"]:.0f}%', ha="center", fontsize=7)

for idx, letter in enumerate(interesting_letters):
    ax = axes[idx + 1]
    subset = xml_with_arabic[xml_with_arabic["first_letter"] == letter]
    bs = subset.groupby("len_bucket").agg(
        total=("headword", "count"),
        with_arabic=("has_arabic", "sum"),
    ).dropna()
    bs["pct"] = 100 * bs["with_arabic"] / bs["total"]
    ax.bar(range(len(bs)), bs["pct"], color=PAL["teal"])
    ax.set_xticks(range(len(bs)))
    ax.set_xticklabels(bs.index, fontsize=7)
    ax.set_title(f"Letter {letter} (n={len(subset)})", fontweight="bold")
    if idx == 0:
        ax.set_ylabel("% entries with Arabic")
    for i, (_, row) in enumerate(bs.iterrows()):
        if row["total"] > 0:
            ax.text(i, row["pct"] + 0.5,
                    f'{row["pct"]:.0f}%\n({int(row["with_arabic"])}/{int(row["total"])})',
                    ha="center", fontsize=6)

plt.suptitle("Arabic Term Presence by Entry Length: Overall and Per Letter Section",
             fontsize=14, y=1.02)
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "entry_length_arabic_by_letter.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ entry_length_arabic_by_letter.png")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 7: THE AL- PREFIX — ARABIC DEFINITE ARTICLE IN LATIN ALCHEMY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 7: The al- prefix…")

# Classify headwords by al- prefix
xml_df["has_al_prefix"] = xml_df["headword"].str.lower().str.startswith("al")
al_headwords = xml_df[xml_df["has_al_prefix"]]

# How many al- headwords have Arabic detections?
al_with_arabic = al_headwords["headword"].isin(clean_df["lemma"].unique())

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Panel 1: al- prefix headwords in dictionary
ax = axes[0]
al_counts = xml_df.groupby("first_letter")["has_al_prefix"].sum().reindex(letters_order).fillna(0)
total_counts = xml_df.groupby("first_letter").size().reindex(letters_order).fillna(0)
al_pct = 100 * al_counts / total_counts

ax.bar(letters_order, al_pct, color=PAL["blue"])
ax.set_title("Headwords Starting with 'Al-' (% of section)")
ax.set_xlabel("letter section")
ax.set_ylabel("% of headwords starting with al-")
ax.set_ylim(0, 100)

# Panel 2: al- headwords — Arabic detection rate
ax = axes[1]
al_hw_set = set(al_headwords["headword"])
arabic_lemma_set = set(clean_df["lemma"].unique())
al_with_detection = al_hw_set & arabic_lemma_set
non_al_hw_set = set(xml_df[~xml_df["has_al_prefix"]]["headword"])
non_al_with_detection = non_al_hw_set & arabic_lemma_set

data_al = pd.DataFrame({
    "category": ["al- headwords", "non-al- headwords"],
    "total": [len(al_hw_set), len(non_al_hw_set)],
    "with_arabic": [len(al_with_detection), len(non_al_with_detection)],
})
data_al["pct"] = 100 * data_al["with_arabic"] / data_al["total"]
bars = ax.bar(data_al["category"], data_al["pct"], color=[PAL["orange"], PAL["gray"]])
ax.set_title("Arabic Detection Rate: al- vs non-al- Headwords")
ax.set_ylabel("% of entries with Arabic detections")
for bar, row in zip(bars, data_al.itertuples()):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f'{row.pct:.1f}%\n({row.with_arabic}/{row.total})',
            ha="center", fontsize=9)

# Panel 3: top al- terms and their Arabic origins
ax = axes[2]
ax.axis("off")
al_terms = clean_df[clean_df["detected_string"].str.lower().str.startswith("al")]
al_term_counts = al_terms.groupby("detected_string").agg(
    count=("lemma", "size"),
    arabic=("arabic_script", "first"),
    english=("english_translation", "first"),
).sort_values("count", ascending=False).head(15)

table_text = "  Latin form          Arabic         English\n"
table_text += "  " + "─" * 55 + "\n"
for term, row in al_term_counts.iterrows():
    ar = str(row["arabic"])[:12] if pd.notna(row["arabic"]) else ""
    en = str(row["english"])[:20] if pd.notna(row["english"]) else ""
    table_text += f'  {term:20s} {ar:14s} {en}\n'

ax.text(0.02, 0.95, table_text, transform=ax.transAxes, fontsize=10,
        va="top", fontfamily="monospace")
ax.set_title("Top 15 al- Terms with Arabic Origins")

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "al_prefix_analysis.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ al_prefix_analysis.png")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 8: ARABIC TERM HOTSPOTS — WHICH ENTRIES ARE RICHEST?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 8: Arabic term hotspots…")

hotspots = clean_df.groupby("lemma").agg(
    n_terms=("detected_string", "nunique"),
    n_rows=("detected_string", "count"),
    terms_list=("detected_string", lambda x: ", ".join(sorted(x.unique()))),
    domain_list=("domain", lambda x: ", ".join(sorted(x.unique()))),
).sort_values("n_terms", ascending=False)

top_hotspots = hotspots.head(25)

# Get entry word counts from XML
hw_wc = xml_df.set_index("headword")["word_count"].to_dict()
top_hotspots["word_count"] = top_hotspots.index.map(lambda x: hw_wc.get(x, 0))

fig, axes = plt.subplots(1, 2, figsize=(18, 10))

# Left: top 25 entries by number of distinct Arabic terms
ax = axes[0]
y = np.arange(len(top_hotspots))
ax.barh(y, top_hotspots["n_terms"], color=PAL["orange"])
ax.set_yticks(y)
ax.set_yticklabels(top_hotspots.index, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel("distinct Arabic terms detected")
ax.set_title("Dictionary Entries Richest in Arabic Terminology")
for i, (lem, row) in enumerate(top_hotspots.iterrows()):
    ax.text(row["n_terms"] + 0.1, i,
            f'{int(row["word_count"])} words',
            va="center", fontsize=7, color=PAL["gray"])

# Right: terms found in each hotspot
ax = axes[1]
ax.axis("off")
text_lines = []
for lem, row in top_hotspots.head(15).iterrows():
    terms = row["terms_list"]
    if len(terms) > 70:
        terms = terms[:67] + "…"
    text_lines.append(f"▸ {lem}:")
    text_lines.append(f"  {terms}")
    text_lines.append("")

ax.text(0.02, 0.98, "\n".join(text_lines), transform=ax.transAxes,
        fontsize=9, va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title("Arabic Terms Found in Top 15 Hotspot Entries")

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "arabic_hotspot_entries.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ arabic_hotspot_entries.png")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 9: ARABIC TERMS ACROSS LETTER SECTIONS — WHICH TERMS SPAN
# MULTIPLE SECTIONS vs WHICH ARE CONFINED TO ONE?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 9: Term spread across sections…")

term_spread = clean_df.groupby("detected_string").agg(
    n_sections=("first_letter", "nunique"),
    sections=("first_letter", lambda x: "".join(sorted(x.unique()))),
    count=("lemma", "size"),
    english=("english_translation", "first"),
).sort_values("n_sections", ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# Left: distribution of section spread
ax = axes[0]
spread_dist = term_spread["n_sections"].value_counts().sort_index()
ax.bar(spread_dist.index, spread_dist.values, color=PAL["teal"])
ax.set_xlabel("number of letter sections where term appears")
ax.set_ylabel("number of distinct Arabic terms")
ax.set_title("How Widely Are Arabic Terms Distributed?")
for i, (x_val, y_val) in enumerate(zip(spread_dist.index, spread_dist.values)):
    ax.text(x_val, y_val + 2, str(y_val), ha="center", fontsize=9)

# Right: terms appearing in 3+ sections
ax = axes[1]
wide_terms = term_spread[term_spread["n_sections"] >= 3].sort_values("n_sections", ascending=True)
y = np.arange(len(wide_terms))
ax.barh(y, wide_terms["n_sections"], color=PAL["orange"])
ax.set_yticks(y)
labels_wide = []
for term, row in wide_terms.iterrows():
    eng = str(row["english"])[:25] if pd.notna(row["english"]) else ""
    labels_wide.append(f'{term} ("{eng}")')
ax.set_yticklabels(labels_wide, fontsize=8)
ax.set_xlabel("number of letter sections")
ax.set_title("Arabic Terms Appearing Across 3+ Letter Sections")
for i, (term, row) in enumerate(wide_terms.iterrows()):
    ax.text(row["n_sections"] + 0.05, i, f'[{row["sections"]}]',
            va="center", fontsize=7, color=PAL["darkblue"])

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "term_spread_across_sections.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ term_spread_across_sections.png")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 10: DICTIONARY SECTIONS AS "WINDOWS" INTO ARABIC INFLUENCE
# Combine entry length, entry count, and arabic density into one
# comprehensive letter-section view
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 10: Comprehensive letter section view…")

fig, ax = plt.subplots(figsize=(14, 9))

# Bubble chart: x = total entries, y = % with arabic, size = median word count
for letter in letters_order:
    row_p = profile.loc[letter]
    if row_p["n_entries"] == 0:
        continue
    ax.scatter(
        row_p["n_entries"], row_p["arabic_lemma_pct"],
        s=row_p["median_wc"] * 20,  # scale size
        alpha=0.6, color=PAL["blue"], edgecolors=PAL["darkblue"], linewidths=1.5
    )
    ax.annotate(letter, (row_p["n_entries"], row_p["arabic_lemma_pct"]),
                fontsize=12, fontweight="bold", ha="center", va="center")

ax.set_xlabel("total entries in letter section")
ax.set_ylabel("% of entries containing Arabic terms")
ax.set_title("Letter Sections: Size, Arabic Density, and Entry Length\n(bubble size = median entry length in words)")

# Add legend for bubble sizes
for size_val, label in [(5, "5 words"), (10, "10 words"), (20, "20 words")]:
    ax.scatter([], [], s=size_val * 20, c=PAL["blue"], alpha=0.5, label=label)
ax.legend(title="median entry length", loc="upper right", scatterpoints=1)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "letter_section_bubble.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ letter_section_bubble.png")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 11: ARABIC HEADWORDS vs ARABIC REFERENCES
# Entries where the headword itself is Arabic vs entries that merely
# mention Arabic terms in their body text
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 11: Headword Arabic vs body-text Arabic…")

# Identify entries where the headword IS the detected string
clean_df["hw_is_arabic"] = clean_df.apply(
    lambda r: str(r["detected_string"]).lower().strip() == str(r["lemma"]).lower().strip()
              or str(r["detected_string"]).lower() in str(r["lemma"]).lower(),
    axis=1
)

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Left: proportion
ax = axes[0]
hw_arabic_count = clean_df["hw_is_arabic"].value_counts()
labels_hw = ["Headword mentions\nArabic term in body", "Headword itself\nis Arabic-derived"]
if True in hw_arabic_count.index:
    vals = [hw_arabic_count.get(False, 0), hw_arabic_count.get(True, 0)]
else:
    vals = [len(clean_df), 0]
ax.pie(vals, labels=labels_hw, colors=[PAL["blue"], PAL["orange"]],
       autopct="%1.1f%%", startangle=90, textprops={"fontsize": 11})
ax.set_title("Arabic as Headword vs Arabic in Body Text")

# Right: examples of headwords that ARE Arabic
ax = axes[1]
hw_arabic = clean_df[clean_df["hw_is_arabic"]].drop_duplicates("lemma")
hw_examples = hw_arabic.nlargest(20, "confidence_score")[
    ["lemma", "arabic_script", "english_translation"]
]
ax.axis("off")
text = "  Headword              Arabic         Meaning\n"
text += "  " + "─" * 55 + "\n"
for _, row in hw_examples.iterrows():
    lem = str(row["lemma"])[:22]
    ar = str(row["arabic_script"])[:14] if pd.notna(row["arabic_script"]) else ""
    en = str(row["english_translation"])[:20] if pd.notna(row["english_translation"]) else ""
    text += f"  {lem:22s} {ar:14s} {en}\n"
ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=10,
        va="top", fontfamily="monospace")
ax.set_title("Examples: Dictionary Headwords That Are Themselves Arabic")

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "headword_vs_body_arabic.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ headword_vs_body_arabic.png")

print(f"\nAll done. {len(os.listdir(OUTDIR))} files in {OUTDIR}")
for f in sorted(os.listdir(OUTDIR)):
    print(f"  {f}")
