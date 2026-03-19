#!/usr/bin/env python3
"""
Ruland 1612 Alchemical Dictionary – Arabic Tradition Exploration
================================================================
Sanity checks (XML vs CSV) + new visualizations.
"""

import os
import re
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import networkx as nx
from collections import Counter, defaultdict
from textwrap import fill

# ── paths ───────────────────────────────────────────────────────────
XML_PATH = "/tmp/Ruland.xml"
CSV_PATH = "/Users/slang/Downloads/schreibProjekte-slides/narrowingdown/output_4ofixed_reviewed_with_entries.csv"
HEADWORD_CSV = "/Users/slang/Downloads/lemma_visualizations_jan28_rev/03_dictionary_structure/headword_letter_coverage.csv"
ENTRY_LEN_CSV = "/Users/slang/Downloads/lemma_visualizations_jan28_rev/03_dictionary_structure/entry_length_summary.csv"
ARABIC_STRINGS_CSV = "/Users/slang/Downloads/lemma_visualizations_jan28_rev/02_coverage_and_counts/top_arabic_strings.csv"
LATIN_COOC_CSV = "/Users/slang/Downloads/lemma_visualizations_jan28_rev/04_relationships_and_cooccurrence/latin_cooccurrence_pairs.csv"
ARABIC_COOC_CSV = "/Users/slang/Downloads/lemma_visualizations_jan28_rev/04_relationships_and_cooccurrence/arabic_cooccurrence_pairs.csv"
SINGLETON_CSV = "/Users/slang/Downloads/lemma_visualizations_jan28_rev/08_arabic_singletons/singleton_profiles.csv"

OUTDIR = "/Users/slang/claude/ruland_exploration"
os.makedirs(OUTDIR, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.1)
BLUE = "#4C78A8"
ORANGE = "#F58518"
TEAL = "#72B7B2"
RED = "#E45756"
GREEN = "#54A24B"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. PARSE XML
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("Parsing XML …")
ns = {"tei": "http://www.tei-c.org/ns/1.0"}
tree = ET.parse(XML_PATH)
root = tree.getroot()

xml_entries = []
for entry in root.iter("{http://www.tei-c.org/ns/1.0}entry"):
    etype = entry.attrib.get("type", "")
    eid = entry.attrib.get("n", "")
    # get headword
    form_el = entry.find(".//{http://www.tei-c.org/ns/1.0}form[@type='lemma']")
    headword = form_el.text.strip() if form_el is not None and form_el.text else ""
    # get full text
    full_text = "".join(entry.itertext()).strip()
    word_count = len(full_text.split())
    xml_entries.append({
        "entry_id": eid,
        "entry_type": etype,
        "headword": headword,
        "full_text": full_text,
        "word_count": word_count,
        "first_letter": headword[0].upper() if headword else "",
    })

xml_df = pd.DataFrame(xml_entries)
print(f"  XML entries parsed: {len(xml_df)}")
print(f"  Unique headwords:   {xml_df['headword'].nunique()}")
print(f"  Letters covered:    {sorted(xml_df['first_letter'].unique())}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. PARSE CSV
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nParsing CSV …")
csv_df = pd.read_csv(CSV_PATH)
# drop unnamed empty columns
csv_df = csv_df.loc[:, ~csv_df.columns.str.startswith("Unnamed")]
print(f"  CSV rows:           {len(csv_df)}")
print(f"  Columns:            {list(csv_df.columns)}")
print(f"  Unique lemmas:      {csv_df['lemma'].nunique()}")
print(f"  Unique detected_string: {csv_df['detected_string'].nunique()}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. SANITY CHECKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "="*70)
print("SANITY CHECKS")
print("="*70)

# 3a. Do all CSV lemmas appear in XML headwords?
xml_headwords = set(xml_df["headword"].str.strip())
csv_lemmas = set(csv_df["lemma"].dropna().str.strip())

missing_from_xml = csv_lemmas - xml_headwords
present_in_xml = csv_lemmas & xml_headwords
print(f"\n3a. CSV lemmas vs XML headwords:")
print(f"    CSV lemmas found in XML: {len(present_in_xml)} / {len(csv_lemmas)}")
print(f"    CSV lemmas NOT in XML:   {len(missing_from_xml)}")
if missing_from_xml:
    print(f"    Missing: {sorted(missing_from_xml)[:30]}{'…' if len(missing_from_xml)>30 else ''}")

# 3b. Check for duplicate rows in CSV
dupes = csv_df.duplicated(subset=["lemma", "detected_string", "arabic_script"], keep=False)
dupe_count = dupes.sum()
print(f"\n3b. Exact duplicate rows (lemma+detected_string+arabic_script): {dupe_count}")
if dupe_count > 0:
    dupe_examples = csv_df[dupes].sort_values(["lemma","detected_string"]).head(10)
    print("    Examples:")
    for _, r in dupe_examples.iterrows():
        print(f"      {r['lemma']:30s} | {str(r['detected_string']):20s} | conf={r['confidence_score']}")

# 3c. Check for rows with very high irrelevance
high_irr = csv_df[csv_df["irrelevance_probability"] >= 0.8]
print(f"\n3c. Rows with irrelevance_probability >= 0.8: {len(high_irr)} / {len(csv_df)} ({100*len(high_irr)/len(csv_df):.1f}%)")
print(f"    Rows with irrelevance_probability >= 0.9: {len(csv_df[csv_df['irrelevance_probability'] >= 0.9])}")

# 3d. Check confidence distribution
print(f"\n3d. Confidence score distribution:")
print(csv_df["confidence_score"].describe().to_string())

# 3e. Check for missing values
print(f"\n3e. Missing values per column:")
for col in csv_df.columns:
    n_miss = csv_df[col].isna().sum()
    if n_miss > 0:
        print(f"    {col}: {n_miss}")

# 3f. Check ruland_entry text matches XML
print(f"\n3f. Spot-checking CSV ruland_entry against XML full_text:")
mismatches = 0
checked = 0
mismatch_examples = []
for lemma in csv_df["lemma"].dropna().unique()[:50]:
    csv_entry_text = csv_df[csv_df["lemma"]==lemma]["ruland_entry"].iloc[0] if "ruland_entry" in csv_df.columns else None
    if csv_entry_text is None or pd.isna(csv_entry_text):
        continue
    xml_match = xml_df[xml_df["headword"].str.strip()==lemma.strip()]
    if len(xml_match) == 0:
        continue
    checked += 1
    xml_text = xml_match.iloc[0]["full_text"]
    # normalize whitespace for comparison
    csv_norm = re.sub(r'\s+', ' ', str(csv_entry_text).strip())[:200]
    xml_norm = re.sub(r'\s+', ' ', xml_text.strip())[:200]
    if csv_norm[:100] != xml_norm[:100]:
        mismatches += 1
        if len(mismatch_examples) < 3:
            mismatch_examples.append((lemma, csv_norm[:80], xml_norm[:80]))

print(f"    Checked {checked} entries, found {mismatches} with text differences in first 100 chars")
for lem, csv_t, xml_t in mismatch_examples:
    print(f"    [{lem}]")
    print(f"      CSV: {csv_t}")
    print(f"      XML: {xml_t}")

# 3g. Entries with N/A lemma
na_rows = csv_df[csv_df["lemma"].isna() | (csv_df["lemma"] == "N/A")]
print(f"\n3g. Rows with lemma = N/A or NaN: {len(na_rows)}")

# 3h. Check for low-confidence + low-irrelevance (potentially interesting)
gold = csv_df[(csv_df["confidence_score"] >= 0.8) & (csv_df["irrelevance_probability"] <= 0.2)]
print(f"\n3h. 'Gold standard' rows (conf>=0.8, irr<=0.2): {len(gold)} / {len(csv_df)} ({100*len(gold)/len(csv_df):.1f}%)")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. VISUALIZATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\n" + "="*70)
print("GENERATING VISUALIZATIONS")
print("="*70)

# ── 4a. Sanity: CSV lemma coverage vs XML ────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(16, 6))

# Left: XML entry count per letter vs CSV unique lemmas per letter
xml_letter_counts = xml_df["first_letter"].value_counts().sort_index()
csv_first_letters = csv_df["lemma"].dropna().str.strip().str[0].str.upper()
csv_letter_counts = csv_first_letters.value_counts().sort_index()

all_letters = sorted(set(xml_letter_counts.index) | set(csv_letter_counts.index))
x = np.arange(len(all_letters))
w = 0.35

ax = axes[0]
ax.bar(x - w/2, [xml_letter_counts.get(l, 0) for l in all_letters], w, label="XML entries", color=BLUE)
ax.bar(x + w/2, [csv_letter_counts.get(l, 0) for l in all_letters], w, label="CSV rows", color=ORANGE)
ax.set_xticks(x)
ax.set_xticklabels(all_letters, fontsize=9)
ax.set_title("XML Entries vs CSV Extraction Rows by Letter")
ax.set_xlabel("initial letter")
ax.set_ylabel("count")
ax.legend()

# Right: ratio of CSV rows to XML entries
ax = axes[1]
ratios = []
for l in all_letters:
    xml_c = xml_letter_counts.get(l, 0)
    csv_c = csv_letter_counts.get(l, 0)
    ratios.append(csv_c / xml_c * 100 if xml_c > 0 else 0)
colors = [RED if r == 0 else (ORANGE if r > 30 else TEAL) for r in ratios]
ax.bar(x, ratios, color=colors)
ax.set_xticks(x)
ax.set_xticklabels(all_letters, fontsize=9)
ax.set_title("Arabic Detection Rate: CSV Rows / XML Entries (%)")
ax.set_xlabel("initial letter")
ax.set_ylabel("% of XML entries with ≥1 detection")
ax.axhline(y=np.mean(ratios), color="gray", linestyle="--", alpha=0.7, label=f"mean = {np.mean(ratios):.1f}%")
ax.legend()

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "sanity_xml_vs_csv_by_letter.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  ✓ sanity_xml_vs_csv_by_letter.png")

# ── 4b. Sanity: confidence vs irrelevance scatter ────────────────
fig, ax = plt.subplots(figsize=(8, 7))
scatter = ax.scatter(
    csv_df["confidence_score"],
    csv_df["irrelevance_probability"],
    alpha=0.35, s=20, c=BLUE, edgecolors="none"
)
ax.set_xlabel("Confidence Score")
ax.set_ylabel("Irrelevance Probability")
ax.set_title("Confidence vs Irrelevance (all CSV rows)")
ax.axhline(0.5, color="gray", linestyle="--", alpha=0.5)
ax.axvline(0.5, color="gray", linestyle="--", alpha=0.5)

# annotate quadrants
ax.text(0.85, 0.05, f"HIGH conf\nLOW irr\nn={len(gold)}", ha="center", va="bottom",
        fontsize=9, color=GREEN, fontweight="bold", transform=ax.transAxes)
q_hh = len(csv_df[(csv_df["confidence_score"]>=0.5) & (csv_df["irrelevance_probability"]>=0.5)])
ax.text(0.85, 0.95, f"HIGH conf\nHIGH irr\nn={q_hh}", ha="center", va="top",
        fontsize=9, color=RED, fontweight="bold", transform=ax.transAxes)
q_ll = len(csv_df[(csv_df["confidence_score"]<0.5) & (csv_df["irrelevance_probability"]<0.5)])
ax.text(0.15, 0.05, f"LOW conf\nLOW irr\nn={q_ll}", ha="center", va="bottom",
        fontsize=9, color=ORANGE, fontweight="bold", transform=ax.transAxes)
q_lh = len(csv_df[(csv_df["confidence_score"]<0.5) & (csv_df["irrelevance_probability"]>=0.5)])
ax.text(0.15, 0.95, f"LOW conf\nHIGH irr\nn={q_lh}", ha="center", va="top",
        fontsize=9, color="gray", fontweight="bold", transform=ax.transAxes)

fig.savefig(os.path.join(OUTDIR, "sanity_confidence_vs_irrelevance.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  ✓ sanity_confidence_vs_irrelevance.png")

# ── 4c. Sanity: distribution of irrelevance scores ──────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

ax = axes[0]
sns.histplot(csv_df["irrelevance_probability"], bins=20, color=RED, ax=ax, edgecolor="white")
ax.set_title("Distribution of Irrelevance Probability")
ax.set_xlabel("irrelevance probability")
ax.axvline(0.5, color="black", linestyle="--", alpha=0.5)

ax = axes[1]
sns.histplot(csv_df["confidence_score"], bins=20, color=GREEN, ax=ax, edgecolor="white")
ax.set_title("Distribution of Confidence Score")
ax.set_xlabel("confidence score")
ax.axvline(0.5, color="black", linestyle="--", alpha=0.5)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "sanity_score_distributions.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  ✓ sanity_score_distributions.png")

# ── 4d. Sanity: entry word-count comparison XML vs CSV ───────────
# For each CSV lemma, compare XML word count
fig, ax = plt.subplots(figsize=(8, 7))
merge_data = []
for lemma in csv_df["lemma"].dropna().unique():
    if lemma == "N/A":
        continue
    xml_match = xml_df[xml_df["headword"].str.strip() == lemma.strip()]
    if len(xml_match) == 0:
        continue
    xml_wc = xml_match.iloc[0]["word_count"]
    csv_entry = csv_df[csv_df["lemma"]==lemma]["ruland_entry"].iloc[0] if "ruland_entry" in csv_df.columns else None
    if csv_entry is None or pd.isna(csv_entry):
        continue
    csv_wc = len(str(csv_entry).split())
    merge_data.append({"lemma": lemma, "xml_wc": xml_wc, "csv_wc": csv_wc})

merge_df = pd.DataFrame(merge_data)
if len(merge_df) > 0:
    ax.scatter(merge_df["xml_wc"], merge_df["csv_wc"], alpha=0.5, s=25, color=BLUE)
    max_val = max(merge_df["xml_wc"].max(), merge_df["csv_wc"].max())
    ax.plot([0, max_val], [0, max_val], "k--", alpha=0.3, label="perfect match")
    ax.set_xlabel("XML word count")
    ax.set_ylabel("CSV ruland_entry word count")
    ax.set_title("Entry Word Count: XML vs CSV (per lemma)")
    ax.legend()
    # flag outliers
    merge_df["ratio"] = merge_df["csv_wc"] / merge_df["xml_wc"].replace(0, np.nan)
    outliers = merge_df[(merge_df["ratio"] < 0.5) | (merge_df["ratio"] > 2.0)]
    if len(outliers) > 0:
        ax.scatter(outliers["xml_wc"], outliers["csv_wc"], color=RED, s=40, zorder=5, label=f"outliers (n={len(outliers)})")
        ax.legend()

fig.savefig(os.path.join(OUTDIR, "sanity_wordcount_xml_vs_csv.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  ✓ sanity_wordcount_xml_vs_csv.png")

# ── 4e. Semantic categories of Arabic terms ──────────────────────
# Categorize English translations into semantic groups
CATEGORY_KEYWORDS = {
    "Minerals/Substances": ["salt", "alum", "vitriol", "sulfur", "sulphur", "arsenic", "borax",
                            "antimony", "mercury", "lead", "copper", "iron", "gold", "silver",
                            "ore", "mineral", "stone", "crystal", "gem", "powder", "calcium",
                            "alkali", "potash", "soda", "natron", "talc", "marcasite", "cinnabar",
                            "asphalt", "bitumen", "tar", "pitch", "camphor", "amber", "ammoniac",
                            "hematite", "vermilion", "orpiment", "realgar", "turpeth", "bezoar",
                            "tutty", "calamine", "magnesia", "sal ammoniac"],
    "Processes/Techniques": ["distill", "calcin", "sublim", "dissolv", "coagul", "filter",
                             "extract", "purif", "refin", "smelt", "roast", "burn", "heat",
                             "cool", "wash", "leaven", "ferment"],
    "Instruments/Vessels": ["alembic", "furnace", "vessel", "flask", "crucible", "retort",
                            "mortar", "bath", "aludel", "athanor", "drum"],
    "Natural Products": ["oil", "resin", "gum", "wax", "saffron", "turmeric", "mummy",
                         "balsam", "aloe", "nutmeg", "sugar", "petroleum", "naphtha",
                         "wood", "dye", "plant", "herb", "flower", "water"],
    "People/Authorities": ["avicenna", "jabir", "rhazes", "geber", "hayyan", "serapio"],
    "Medical/Pharmacological": ["medicine", "cure", "heal", "poison", "drug", "therapeutic",
                                 "remedy", "elixir"],
    "Colors": ["red", "white", "blue", "black", "yellow", "green"],
}

def categorize(english_translation):
    if pd.isna(english_translation):
        return "Uncategorized"
    t = str(english_translation).lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in t:
                return cat
    return "Other"

csv_df["semantic_category"] = csv_df["english_translation"].apply(categorize)

# Filter to reliable rows
reliable = csv_df[csv_df["irrelevance_probability"] <= 0.5]

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# All rows
cat_counts_all = csv_df["semantic_category"].value_counts()
ax = axes[0]
colors_map = {
    "Minerals/Substances": BLUE, "Processes/Techniques": ORANGE,
    "Instruments/Vessels": TEAL, "Natural Products": GREEN,
    "People/Authorities": RED, "Medical/Pharmacological": "#B279A2",
    "Colors": "#FF9DA6", "Other": "#BAB0AC", "Uncategorized": "#D3D3D3"
}
bar_colors = [colors_map.get(c, "#BAB0AC") for c in cat_counts_all.index]
sns.barplot(x=cat_counts_all.values, y=cat_counts_all.index, palette=bar_colors, ax=ax)
ax.set_title(f"Semantic Categories – All CSV Rows (n={len(csv_df)})")
ax.set_xlabel("count")
for i, v in enumerate(cat_counts_all.values):
    ax.text(v + 2, i, str(v), va="center", fontsize=9)

# Reliable only
cat_counts_rel = reliable["semantic_category"].value_counts()
ax = axes[1]
bar_colors_rel = [colors_map.get(c, "#BAB0AC") for c in cat_counts_rel.index]
sns.barplot(x=cat_counts_rel.values, y=cat_counts_rel.index, palette=bar_colors_rel, ax=ax)
ax.set_title(f"Semantic Categories – Reliable Only (irr≤0.5, n={len(reliable)})")
ax.set_xlabel("count")
for i, v in enumerate(cat_counts_rel.values):
    ax.text(v + 1, i, str(v), va="center", fontsize=9)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "semantic_categories.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  ✓ semantic_categories.png")

# ── 4f. Arabic term density across dictionary (by position) ─────
# Use XML entry order (alphabetical position) to show density
xml_df_sorted = xml_df.reset_index(drop=True)
xml_df_sorted["position"] = xml_df_sorted.index

# Mark which XML entries have CSV hits
csv_lemmas_set = set(csv_df["lemma"].dropna().str.strip().unique())
xml_df_sorted["has_arabic"] = xml_df_sorted["headword"].str.strip().isin(csv_lemmas_set)

# Reliable hits
reliable_lemmas = set(reliable["lemma"].dropna().str.strip().unique())
xml_df_sorted["has_reliable_arabic"] = xml_df_sorted["headword"].str.strip().isin(reliable_lemmas)

# Sliding window density
window = 50
positions = xml_df_sorted["position"].values
has_arabic = xml_df_sorted["has_arabic"].astype(int).values
has_reliable = xml_df_sorted["has_reliable_arabic"].astype(int).values

density_all = np.convolve(has_arabic, np.ones(window)/window, mode="valid")
density_rel = np.convolve(has_reliable, np.ones(window)/window, mode="valid")
density_x = np.arange(len(density_all)) + window//2

# Get letter boundaries for annotation
letter_boundaries = {}
for letter in sorted(xml_df_sorted["first_letter"].unique()):
    subset = xml_df_sorted[xml_df_sorted["first_letter"]==letter]
    if len(subset) > 0:
        letter_boundaries[letter] = subset["position"].iloc[0]

fig, ax = plt.subplots(figsize=(16, 5))
ax.fill_between(density_x, density_all, alpha=0.3, color=BLUE, label="all CSV hits")
ax.plot(density_x, density_all, color=BLUE, linewidth=1)
ax.fill_between(density_x, density_rel, alpha=0.3, color=GREEN, label="reliable hits (irr≤0.5)")
ax.plot(density_x, density_rel, color=GREEN, linewidth=1)

for letter, pos in letter_boundaries.items():
    ax.axvline(pos, color="gray", alpha=0.2, linewidth=0.5)
    ax.text(pos, ax.get_ylim()[1]*0.95, letter, fontsize=8, ha="center", va="top", color="gray")

ax.set_title(f"Arabic Term Density Across the Dictionary (sliding window = {window} entries)")
ax.set_xlabel("entry position (alphabetical order)")
ax.set_ylabel("fraction of entries with Arabic hits")
ax.legend()
fig.savefig(os.path.join(OUTDIR, "arabic_density_by_position.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  ✓ arabic_density_by_position.png")

# ── 4g. Co-occurrence network ────────────────────────────────────
latin_cooc = pd.read_csv(LATIN_COOC_CSV)

# Filter to pairs with count >= 1, and take unique terms with >= 2 connections
G = nx.Graph()
for _, row in latin_cooc.iterrows():
    if row["cooccurrence_count"] >= 1:
        G.add_edge(row["term_a"], row["term_b"], weight=row["cooccurrence_count"])

# Keep only nodes with degree >= 2 for readability
nodes_to_keep = [n for n in G.nodes() if G.degree(n) >= 2]
G_sub = G.subgraph(nodes_to_keep).copy()

if len(G_sub.nodes()) > 0:
    fig, ax = plt.subplots(figsize=(14, 14))
    pos = nx.spring_layout(G_sub, k=2.5, iterations=80, seed=42)

    degrees = dict(G_sub.degree())
    node_sizes = [max(100, degrees[n] * 40) for n in G_sub.nodes()]

    edges = G_sub.edges(data=True)
    edge_weights = [e[2].get("weight", 1) for e in edges]

    nx.draw_networkx_edges(G_sub, pos, ax=ax, alpha=0.3,
                           width=[w*0.5 for w in edge_weights], edge_color="gray")
    nx.draw_networkx_nodes(G_sub, pos, ax=ax, node_size=node_sizes,
                           node_color=ORANGE, alpha=0.7, edgecolors="white", linewidths=0.5)
    nx.draw_networkx_labels(G_sub, pos, ax=ax, font_size=7)

    ax.set_title("Latin Arabic Term Co-occurrence Network (nodes with ≥2 connections)")
    ax.axis("off")
    fig.savefig(os.path.join(OUTDIR, "cooccurrence_network_latin.png"), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  ✓ cooccurrence_network_latin.png")

# ── 4h. Arabic proportion by entry length (percentage view) ─────
entry_len_df = pd.read_csv(ENTRY_LEN_CSV)
fig, ax = plt.subplots(figsize=(10, 6))
buckets = entry_len_df["length_bucket"].astype(str)
pcts = entry_len_df["arabic_share_pct"]
bars = ax.bar(buckets, pcts, color=ORANGE, edgecolor="white")
for bar, pct, total, arabic in zip(bars, pcts, entry_len_df["total_entries"], entry_len_df["entries_with_arabic"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
            f"{pct:.1f}%\n({int(arabic)}/{int(total)})", ha="center", va="bottom", fontsize=9)
ax.set_title("Percentage of Entries with Arabic Terms by Entry Length")
ax.set_xlabel("entry length bucket (words)")
ax.set_ylabel("% of entries with Arabic terms")
ax.set_ylim(0, max(pcts) * 1.3)
fig.savefig(os.path.join(OUTDIR, "arabic_share_by_entry_length.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  ✓ arabic_share_by_entry_length.png")

# ── 4i. Top Arabic strings by confidence tier ───────────────────
# Show top 25 detected strings, colored by mean confidence
top_strings = csv_df.groupby("detected_string").agg(
    count=("detected_string", "size"),
    mean_conf=("confidence_score", "mean"),
    mean_irr=("irrelevance_probability", "mean")
).sort_values("count", ascending=True).tail(30)

fig, ax = plt.subplots(figsize=(10, 9))
colors = []
for _, row in top_strings.iterrows():
    if row["mean_irr"] >= 0.5:
        colors.append(RED)
    elif row["mean_conf"] >= 0.8:
        colors.append(GREEN)
    else:
        colors.append(ORANGE)

ax.barh(range(len(top_strings)), top_strings["count"], color=colors)
ax.set_yticks(range(len(top_strings)))
ax.set_yticklabels(top_strings.index)
for i, (term, row) in enumerate(top_strings.iterrows()):
    ax.text(row["count"] + 0.2, i,
            f"conf={row['mean_conf']:.2f}  irr={row['mean_irr']:.2f}",
            va="center", fontsize=8)
ax.set_title("Top 30 Detected Strings – Colored by Quality")
ax.set_xlabel("count")

# legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=GREEN, label="High quality (conf≥0.8, irr<0.5)"),
    Patch(facecolor=ORANGE, label="Moderate (conf<0.8, irr<0.5)"),
    Patch(facecolor=RED, label="Likely irrelevant (irr≥0.5)"),
]
ax.legend(handles=legend_elements, loc="lower right")

fig.savefig(os.path.join(OUTDIR, "top_strings_quality_coded.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  ✓ top_strings_quality_coded.png")

# ── 4j. XML dictionary structure overview ────────────────────────
fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Top-left: entry count per letter from XML
ax = axes[0, 0]
letter_cts = xml_df["first_letter"].value_counts().sort_index()
ax.bar(letter_cts.index, letter_cts.values, color=BLUE)
ax.set_title(f"XML Dictionary: Entries per Letter (total={len(xml_df)})")
ax.set_xlabel("letter")
ax.set_ylabel("entries")
for i, (l, v) in enumerate(letter_cts.items()):
    ax.text(i, v + 5, str(v), ha="center", fontsize=7)

# Top-right: word count distribution (log scale)
ax = axes[0, 1]
ax.hist(xml_df["word_count"], bins=80, color=TEAL, edgecolor="white")
ax.set_title("XML Entry Word Count Distribution")
ax.set_xlabel("words")
ax.set_ylabel("entries")
ax.set_yscale("log")
ax.axvline(xml_df["word_count"].median(), color=RED, linestyle="--",
           label=f"median={xml_df['word_count'].median():.0f}")
ax.axvline(xml_df["word_count"].mean(), color=ORANGE, linestyle="--",
           label=f"mean={xml_df['word_count'].mean():.0f}")
ax.legend()

# Bottom-left: empty vs non-empty entries
ax = axes[1, 0]
xml_df["has_definition"] = xml_df["word_count"] > 3  # just headword = ~1-2 words
has_def = xml_df["has_definition"].value_counts()
ax.pie(has_def.values, labels=["Has definition", "Stub/empty"],
       colors=[BLUE, "#D3D3D3"], autopct="%1.1f%%", startangle=90)
ax.set_title(f"XML Entries: Stub vs Defined")

# Bottom-right: top 15 longest entries
ax = axes[1, 1]
longest = xml_df.nlargest(15, "word_count")[["headword", "word_count"]].sort_values("word_count")
ax.barh(longest["headword"], longest["word_count"], color=BLUE)
ax.set_title("15 Longest XML Entries (by word count)")
ax.set_xlabel("words")

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "xml_dictionary_overview.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  ✓ xml_dictionary_overview.png")

# ── 4k. Arabic authority references ──────────────────────────────
authority_terms = {
    "Avicenna": ["avicenna", "auicenna", "avic", "ابن سينا"],
    "Geber/Jabir": ["geber", "jabir", "جابر"],
    "Serapio": ["serapio"],
    "Rhazes": ["rhazes", "rasis", "الرازي", "razis"],
    "Dioscorides": ["dioscorid", "dioscor", "diosc"],
    "Pliny": ["plin", "plinius"],
    "Galen": ["galen", "galeni", "galenus"],
}

# Count authorities in XML entries
auth_counts = defaultdict(int)
auth_entries = defaultdict(set)
for _, row in xml_df.iterrows():
    text_lower = row["full_text"].lower()
    for auth, patterns in authority_terms.items():
        for pat in patterns:
            if pat.lower() in text_lower:
                auth_counts[auth] += 1
                auth_entries[auth].add(row["headword"])
                break

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left: total mentions
ax = axes[0]
auth_series = pd.Series(auth_counts).sort_values()
ax.barh(auth_series.index, auth_series.values, color=BLUE)
ax.set_title("Authority Mentions in XML Entries")
ax.set_xlabel("entries mentioning authority")
for i, v in enumerate(auth_series.values):
    ax.text(v + 2, i, str(v), va="center", fontsize=9)

# Right: Arabic vs non-Arabic authority mentions
ax = axes[1]
auth_in_arabic = {}
for auth in authority_terms:
    arabic_entries = auth_entries[auth] & csv_lemmas_set
    auth_in_arabic[auth] = len(arabic_entries)

auth_df = pd.DataFrame({
    "total_entries": {a: len(auth_entries[a]) for a in authority_terms},
    "in_arabic_entries": auth_in_arabic,
}).sort_values("total_entries")

x_pos = np.arange(len(auth_df))
ax.barh(x_pos - 0.15, auth_df["total_entries"], 0.3, label="all entries", color=BLUE)
ax.barh(x_pos + 0.15, auth_df["in_arabic_entries"], 0.3, label="entries with Arabic terms", color=ORANGE)
ax.set_yticks(x_pos)
ax.set_yticklabels(auth_df.index)
ax.set_title("Authorities: All Entries vs Arabic-Bearing Entries")
ax.set_xlabel("count")
ax.legend()

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "authority_references.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  ✓ authority_references.png")

# ── 4l. Sanity: CSV rows that might need cleaning ───────────────
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Top-left: rows by irrelevance quartile
ax = axes[0, 0]
irr_bins = pd.cut(csv_df["irrelevance_probability"], bins=[0, 0.15, 0.3, 0.5, 0.8, 1.0],
                  labels=["0–0.15", "0.15–0.3", "0.3–0.5", "0.5–0.8", "0.8–1.0"])
irr_dist = irr_bins.value_counts().sort_index()
bar_colors_irr = [GREEN, GREEN, ORANGE, RED, RED]
ax.bar(irr_dist.index, irr_dist.values, color=bar_colors_irr)
ax.set_title("CSV Rows by Irrelevance Bracket")
ax.set_xlabel("irrelevance probability")
ax.set_ylabel("rows")
for i, v in enumerate(irr_dist.values):
    ax.text(i, v + 3, str(v), ha="center", fontsize=9)

# Top-right: confidence by irrelevance bracket (box plot)
ax = axes[0, 1]
csv_df["irr_bracket"] = irr_bins
csv_df.boxplot(column="confidence_score", by="irr_bracket", ax=ax)
ax.set_title("Confidence by Irrelevance Bracket")
ax.set_xlabel("irrelevance bracket")
ax.set_ylabel("confidence score")
plt.sca(ax)
plt.title("Confidence by Irrelevance Bracket")
ax.get_figure().suptitle("")

# Bottom-left: how many unique arabic_script per lemma
ax = axes[1, 0]
scripts_per_lemma = csv_df.groupby("lemma")["arabic_script"].nunique()
scripts_dist = scripts_per_lemma.value_counts().sort_index()
ax.bar(scripts_dist.index[:15], scripts_dist.values[:15], color=TEAL)
ax.set_title("Unique Arabic Scripts per Lemma")
ax.set_xlabel("number of distinct arabic_script values")
ax.set_ylabel("number of lemmas")

# Bottom-right: duplicate detected_string per lemma
ax = axes[1, 1]
dupes_per_lemma = csv_df.groupby(["lemma", "detected_string"]).size().reset_index(name="n")
multi = dupes_per_lemma[dupes_per_lemma["n"] > 1]
if len(multi) > 0:
    ax.barh(range(min(15, len(multi))),
            multi.nlargest(15, "n")["n"].values,
            color=RED)
    labels = [f"{r['lemma'][:20]}→{r['detected_string'][:15]}"
              for _, r in multi.nlargest(15, "n").iterrows()]
    ax.set_yticks(range(min(15, len(multi))))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_title("Duplicate (lemma, detected_string) Pairs")
    ax.set_xlabel("occurrences")
else:
    ax.text(0.5, 0.5, "No duplicates found", ha="center", va="center", transform=ax.transAxes)
    ax.set_title("Duplicate Check: Clean")

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "sanity_csv_quality_overview.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  ✓ sanity_csv_quality_overview.png")

# ── 4m. Filtered vs unfiltered comparison ────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# How results change when filtering
thresholds = [0.0, 0.3, 0.5]
for idx, max_irr in enumerate(thresholds):
    ax = axes[idx]
    if max_irr == 0.0:
        subset = csv_df
        title = f"All rows (n={len(subset)})"
    else:
        subset = csv_df[csv_df["irrelevance_probability"] <= max_irr]
        title = f"irr ≤ {max_irr} (n={len(subset)})"

    top = subset["detected_string"].value_counts().head(15)
    ax.barh(range(len(top)), top.values, color=ORANGE if max_irr > 0 else BLUE)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top.index)
    ax.set_title(title)
    ax.set_xlabel("count")
    ax.invert_yaxis()

plt.suptitle("Top Detected Strings at Different Irrelevance Thresholds", fontsize=14, y=1.02)
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "filtering_comparison.png"), dpi=150, bbox_inches="tight")
plt.close(fig)
print("  ✓ filtering_comparison.png")

# ── Summary report ───────────────────────────────────────────────
print("\n" + "="*70)
print("SUMMARY REPORT")
print("="*70)
print(f"XML dictionary entries:     {len(xml_df)}")
print(f"  with definition (>3 words): {xml_df['has_definition'].sum()}")
print(f"  stubs:                      {(~xml_df['has_definition']).sum()}")
print(f"CSV extraction rows:        {len(csv_df)}")
print(f"  unique lemmas:              {csv_df['lemma'].nunique()}")
print(f"  unique detected strings:    {csv_df['detected_string'].nunique()}")
print(f"  'gold standard' rows:       {len(gold)} ({100*len(gold)/len(csv_df):.1f}%)")
print(f"  likely irrelevant (≥0.5):   {len(csv_df[csv_df['irrelevance_probability']>=0.5])} ({100*len(csv_df[csv_df['irrelevance_probability']>=0.5])/len(csv_df):.1f}%)")
print(f"  N/A lemmas:                 {len(na_rows)}")
print(f"  exact duplicates:           {dupe_count}")
print(f"  lemmas missing from XML:    {len(missing_from_xml)}")
print(f"\nAll visualizations saved to: {OUTDIR}")
print("Files created:")
for f in sorted(os.listdir(OUTDIR)):
    if f.endswith(".png"):
        print(f"  {f}")
