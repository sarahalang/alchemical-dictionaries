#!/usr/bin/env python3
"""
Ruland 1612 – Etymology deep-dive & Alphabetical Timeline
==========================================================
Part A: How Arabic terms were adapted into Latin — morphology,
        roots, entry texts, and semantic patterns.
Part B: The dictionary's alphabetical order as a "timeline" —
        cumulative discovery, density waves, skyline views.
"""

import os, re, textwrap
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import seaborn as sns
from collections import Counter, defaultdict

# ── paths ───────────────────────────────────────────────────────────
XML_PATH = "/tmp/Ruland.xml"
CSV_CLEAN = "/Users/slang/claude/ruland_exploration/ruland_arabic_cleaned.csv"
CSV_RAW = "/Users/slang/Downloads/schreibProjekte-slides/narrowingdown/output_4ofixed_reviewed_with_entries.csv"
OUTDIR = "/Users/slang/claude/ruland_exploration/05_etymology_timeline"
os.makedirs(OUTDIR, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.05)
PAL = {
    "blue": "#4C78A8", "orange": "#F58518", "teal": "#72B7B2",
    "red": "#E45756", "green": "#54A24B", "purple": "#B279A2",
    "pink": "#FF9DA6", "brown": "#9D7660", "gray": "#BAB0AC",
    "gold": "#EECA3B", "darkblue": "#2D4A7A", "lightblue": "#9ECAE9",
    "darkorange": "#D4780A", "darkgreen": "#2E7D32",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LOAD DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("Loading data…")

# XML — preserve document order (sequential position)
tree = ET.parse(XML_PATH)
root = tree.getroot()
xml_entries = []
for seq_idx, entry in enumerate(root.iter("{http://www.tei-c.org/ns/1.0}entry")):
    form_el = entry.find(".//{http://www.tei-c.org/ns/1.0}form[@type='lemma']")
    hw = form_el.text.strip() if form_el is not None and form_el.text else ""
    full_text = "".join(entry.itertext()).strip()
    xml_entries.append({
        "seq_idx": seq_idx,
        "headword": hw,
        "full_text": full_text,
        "word_count": len(full_text.split()),
        "first_letter": hw[0].upper() if hw else "",
    })
xml_df = pd.DataFrame(xml_entries)
xml_df = xml_df[xml_df["first_letter"] != ""]

clean_df = pd.read_csv(CSV_CLEAN)

print(f"  XML: {len(xml_df)} entries (in document order)")
print(f"  Clean CSV: {len(clean_df)} rows")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SHARED: Etymology classification (expanded)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def classify_etymology(row):
    ds = str(row.get("detected_string", "")).lower().strip()
    eng = str(row.get("english_translation", "")).lower()
    if ds.startswith("al") and len(ds) > 3:
        return "al- prefix preserved"
    if ds.startswith(("at", "az", "as")) and len(ds) > 3:
        return "al- assimilated"
    if ds in ["borax", "elixir", "naphtha", "mumia", "camphor", "saffran",
              "realgar", "talcum", "bezar", "zarnich", "natron", "tutia",
              "colcotar", "marcasita", "sal ammoniac"]:
        return "direct transliteration"
    if any(n in eng for n in ["avicenna", "jabir", "rhazes", "geber", "serapio"]):
        return "personal name"
    if " " in ds:
        return "compound / phrase"
    return "other adaptation"

clean_df["etymology_type"] = clean_df.apply(classify_etymology, axis=1)

# Semantic domain assignment
DOMAINS = {
    "Minerals & Salts": ["salt", "alum", "vitriol", "sulfur", "sulphur", "borax",
        "antimony", "mercury", "lead", "copper", "iron", "ore", "mineral",
        "alkali", "potash", "soda", "natron", "marcasite", "cinnabar", "talc",
        "arsenic", "orpiment", "realgar", "hematite", "vermilion", "calcium",
        "powder", "calamine", "magnesia", "ite", "ite "],
    "Organic & Natural": ["oil", "resin", "gum", "wax", "saffron", "turmeric",
        "mummy", "balsam", "aloe", "nutmeg", "sugar", "petroleum", "naphtha",
        "camphor", "amber", "wood", "dye", "plant", "herb", "flower", "tar",
        "pitch", "asphalt", "bitumen", "juniper", "water"],
    "Apparatus & Process": ["alembic", "furnace", "vessel", "flask", "crucible",
        "aludel", "athanor", "drum", "bath", "distill", "calcin", "sublim",
        "filter", "extract", "purif", "leaven", "ferment", "still", "oven"],
    "Medical & Alchemical": ["elixir", "medicine", "cure", "heal", "poison",
        "bezoar", "remedy", "stone", "tincture", "philos"],
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

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PART A: ETYMOLOGY & ENTRIES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── Fig 1: LATIN MORPHOLOGICAL ADAPTATION ────────────────────────
# How were Arabic words Latinized? What endings were added?
print("\nFig 1: Latin morphological adaptation…")

def detect_latin_ending(s):
    s = str(s).lower().strip()
    if s.endswith("um"):
        return "-um (neuter)"
    if s.endswith("us"):
        return "-us (masculine)"
    if s.endswith("a"):
        return "-a (feminine)"
    if s.endswith("is"):
        return "-is (3rd decl.)"
    if s.endswith("ar") or s.endswith("er"):
        return "-ar/-er"
    if s.endswith("ix") or s.endswith("ax"):
        return "-ix/-ax"
    return "no Latin ending"

clean_df["latin_ending"] = clean_df["detected_string"].apply(detect_latin_ending)

fig, axes = plt.subplots(1, 3, figsize=(20, 7))

# Panel 1: overall ending distribution
ax = axes[0]
ending_counts = clean_df["latin_ending"].value_counts()
colors_end = [PAL["blue"], PAL["orange"], PAL["teal"], PAL["green"],
              PAL["purple"], PAL["red"], PAL["brown"]][:len(ending_counts)]
bars = ax.barh(range(len(ending_counts)), ending_counts.values, color=colors_end)
ax.set_yticks(range(len(ending_counts)))
ax.set_yticklabels(ending_counts.index, fontsize=10)
ax.set_xlabel("number of terms")
ax.set_title("Latin Morphological Endings\non Arabic-Derived Terms", fontsize=12)
for i, v in enumerate(ending_counts.values):
    ax.text(v + 0.5, i, str(v), va="center", fontsize=9)

# Panel 2: endings by etymology type (stacked)
ax = axes[1]
cross = pd.crosstab(clean_df["etymology_type"], clean_df["latin_ending"])
# Reorder
etym_order = clean_df["etymology_type"].value_counts().index.tolist()
cross = cross.reindex(etym_order)
cross.plot(kind="barh", stacked=True, ax=ax, colormap="Set2", legend=False)
ax.set_xlabel("number of terms")
ax.set_title("Endings by Etymology Type", fontsize=12)
ax.legend(bbox_to_anchor=(1.0, 1.0), fontsize=7, title="ending")

# Panel 3: examples table
ax = axes[2]
ax.axis("off")
examples = []
for ending in ending_counts.index[:7]:
    subset = clean_df[clean_df["latin_ending"] == ending]
    top_ex = subset["detected_string"].value_counts().head(4).index.tolist()
    examples.append(f"  {ending:20s}  {', '.join(top_ex)}")
header = "  Ending               Examples\n  " + "─" * 50
ax.text(0.0, 0.95, header + "\n" + "\n".join(examples),
        transform=ax.transAxes, fontsize=10, va="top", fontfamily="monospace",
        linespacing=1.6)
ax.set_title("Examples per Ending Type", fontsize=12)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "latin_morphology.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ latin_morphology.png")


# ── Fig 2: ARABIC ROOT → LATIN FORM MAPPING ─────────────────────
# Show how Arabic roots map to one or more Latin forms
print("\nFig 2: Arabic root to Latin form mapping…")

# Group by normalized_arabic to find Arabic roots with multiple Latin forms
root_mapping = clean_df.dropna(subset=["arabic_script"]).groupby("arabic_script").agg(
    latin_forms=("detected_string", lambda x: sorted(x.unique())),
    n_forms=("detected_string", "nunique"),
    n_entries=("lemma", "nunique"),
    english=("english_translation", "first"),
).sort_values("n_forms", ascending=False)

# Also: Latin forms mapping to multiple Arabic roots
latin_mapping = clean_df.dropna(subset=["arabic_script"]).groupby("detected_string").agg(
    arabic_forms=("arabic_script", lambda x: sorted(x.unique())),
    n_arabic=("arabic_script", "nunique"),
    english=("english_translation", "first"),
).sort_values("n_arabic", ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(18, 10))

# Left: Arabic roots with multiple Latin forms
ax = axes[0]
multi_latin = root_mapping[root_mapping["n_forms"] > 1].head(20)
y = np.arange(len(multi_latin))
ax.barh(y, multi_latin["n_forms"], color=PAL["orange"])
labels_left = []
for ar, row in multi_latin.iterrows():
    latin_str = ", ".join(row["latin_forms"][:4])
    if len(row["latin_forms"]) > 4:
        latin_str += "…"
    labels_left.append(f'{ar}')
ax.set_yticks(y)
ax.set_yticklabels(labels_left, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel("number of distinct Latin forms")
ax.set_title("One Arabic Root → Multiple Latin Forms\n(Top 20 Arabic terms with variant spellings)", fontsize=11)
# Annotate with Latin forms
for i, (ar, row) in enumerate(multi_latin.iterrows()):
    latin_str = ", ".join(row["latin_forms"][:3])
    if len(row["latin_forms"]) > 3:
        latin_str += f" (+{len(row['latin_forms'])-3})"
    ax.text(row["n_forms"] + 0.05, i, latin_str, va="center", fontsize=7,
            color=PAL["darkblue"])

# Right: Latin forms with multiple Arabic attributions
ax = axes[1]
multi_arabic = latin_mapping[latin_mapping["n_arabic"] > 1].head(20)
if len(multi_arabic) > 0:
    y2 = np.arange(len(multi_arabic))
    ax.barh(y2, multi_arabic["n_arabic"], color=PAL["teal"])
    labels_right = []
    for lat, row in multi_arabic.iterrows():
        labels_right.append(lat)
    ax.set_yticks(y2)
    ax.set_yticklabels(labels_right, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("number of distinct Arabic attributions")
    ax.set_title("One Latin Form → Multiple Arabic Roots?\n(Terms with competing etymologies)", fontsize=11)
    for i, (lat, row) in enumerate(multi_arabic.iterrows()):
        ar_str = " / ".join(row["arabic_forms"][:3])
        ax.text(row["n_arabic"] + 0.05, i, ar_str, va="center", fontsize=7,
                color=PAL["darkblue"])
else:
    ax.text(0.5, 0.5, "No Latin terms with\nmultiple Arabic roots found",
            ha="center", va="center", transform=ax.transAxes, fontsize=14)
    ax.set_title("One Latin Form → Multiple Arabic Roots?", fontsize=11)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "arabic_latin_mapping.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ arabic_latin_mapping.png")


# ── Fig 3: ETYMOLOGY TYPE × SEMANTIC DOMAIN ─────────────────────
# Which adaptation strategy was used for which kind of substance?
print("\nFig 3: Etymology × semantic domain…")

fig, axes = plt.subplots(1, 2, figsize=(18, 8))

# Left: heatmap
ax = axes[0]
etym_domain = pd.crosstab(clean_df["etymology_type"], clean_df["domain"])
etym_order = clean_df["etymology_type"].value_counts().index.tolist()
domain_order = ["Minerals & Salts", "Organic & Natural", "Apparatus & Process",
                "Medical & Alchemical", "Other", "Unclassified"]
domain_order = [d for d in domain_order if d in etym_domain.columns]
etym_domain = etym_domain.reindex(index=etym_order, columns=domain_order).fillna(0)

im = ax.imshow(etym_domain.values, aspect="auto", cmap="YlGnBu", interpolation="nearest")
ax.set_xticks(range(len(domain_order)))
ax.set_xticklabels([d.replace(" & ", "\n& ") for d in domain_order], fontsize=9, rotation=30, ha="right")
ax.set_yticks(range(len(etym_order)))
ax.set_yticklabels(etym_order, fontsize=10)
for i in range(len(etym_order)):
    for j in range(len(domain_order)):
        val = int(etym_domain.values[i, j])
        if val > 0:
            ax.text(j, i, str(val), ha="center", va="center",
                    fontsize=9, color="white" if val > 8 else "black")
ax.set_title("How Each Semantic Domain\nAdapted Arabic Terms", fontsize=12)
plt.colorbar(im, ax=ax, shrink=0.6, label="count")

# Right: proportional view — for each domain, what % uses each etymology?
ax = axes[1]
etym_domain_pct = etym_domain.div(etym_domain.sum(axis=0), axis=1) * 100
etym_domain_pct = etym_domain_pct.T  # domains as rows
etym_domain_pct.plot(kind="barh", stacked=True, ax=ax, colormap="Set2", width=0.7)
ax.set_xlabel("% of terms in domain")
ax.set_title("Proportion of Etymology Types\nWithin Each Semantic Domain", fontsize=12)
ax.legend(bbox_to_anchor=(1.0, 1.0), fontsize=7, title="etymology type")
ax.set_xlim(0, 100)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "etymology_x_domain.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ etymology_x_domain.png")


# ── Fig 4: ENTRY TEXT EXCERPTS — WHAT DO THE ENTRIES ACTUALLY SAY? ─
# Show actual dictionary text for top Arabic terms
print("\nFig 4: Entry text excerpts…")

# Get entry texts from XML for top Arabic terms
hw_to_text = dict(zip(xml_df["headword"], xml_df["full_text"]))

top_terms_for_excerpt = ["Alkali", "Borax", "Elixir", "Alcohol",
                         "Alembicum", "Naphtha", "Mumia", "Colcotar",
                         "Natron", "Realgar", "Athanor", "Tutia"]
# Match to actual headwords (case-insensitive)
hw_lower_map = {hw.lower(): hw for hw in xml_df["headword"]}

fig = plt.figure(figsize=(20, 16))
gs = gridspec.GridSpec(4, 3, hspace=0.4, wspace=0.3)

for idx, term in enumerate(top_terms_for_excerpt):
    ax = fig.add_subplot(gs[idx // 3, idx % 3])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Find entry text
    hw_key = hw_lower_map.get(term.lower(), term)
    entry_text = hw_to_text.get(hw_key, "")

    # Get Arabic info from clean_df
    matches = clean_df[clean_df["lemma"].str.lower() == term.lower()]
    arabic = matches["arabic_script"].dropna().iloc[0] if len(matches) > 0 and not matches["arabic_script"].dropna().empty else ""
    english = matches["english_translation"].dropna().iloc[0] if len(matches) > 0 and not matches["english_translation"].dropna().empty else ""
    etym = matches["etymology_type"].iloc[0] if len(matches) > 0 else ""

    # Truncate entry text
    if len(entry_text) > 300:
        entry_text = entry_text[:297] + "…"
    wrapped = textwrap.fill(entry_text, width=45)

    # Header
    ax.text(0.0, 1.0, f"{hw_key}", fontsize=11, fontweight="bold",
            color=PAL["darkblue"], va="top")
    from matplotlib.font_manager import FontProperties
    arabic_font = FontProperties(fname="/System/Library/Fonts/GeezaPro.ttc")
    ax.text(0.0, 0.92, f"{arabic}", fontsize=11,
            color=PAL["orange"], va="top", fontproperties=arabic_font)
    ax.text(0.0, 0.85, f'= "{english}"', fontsize=9,
            color=PAL["orange"], va="top", style="italic")
    ax.text(0.0, 0.78, f"[{etym}]", fontsize=8, color=PAL["gray"], va="top")

    # Entry text
    ax.text(0.0, 0.71, wrapped, fontsize=7.5, va="top", fontfamily="serif",
            linespacing=1.4, color="#333333")

    # Border
    ax.add_patch(mpatches.FancyBboxPatch(
        (-0.02, -0.02), 1.04, 1.04, boxstyle="round,pad=0.02",
        facecolor="#FAFAF5", edgecolor=PAL["gray"], linewidth=0.8,
        transform=ax.transAxes, zorder=-1))

fig.suptitle("Dictionary Entry Excerpts: 12 Key Arabic-Origin Terms in Ruland's Lexicon",
             fontsize=14, y=0.98, fontweight="bold")
fig.savefig(os.path.join(OUTDIR, "entry_text_excerpts.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ entry_text_excerpts.png")


# ── Fig 5: ETYMOLOGY × LETTER SECTION ───────────────────────────
# Which adaptation pattern dominates in which part of the alphabet?
print("\nFig 5: Etymology by letter section…")

letters_order = sorted(xml_df["first_letter"].unique())

fig, ax = plt.subplots(figsize=(18, 8))

etym_letter = pd.crosstab(clean_df["first_letter"], clean_df["etymology_type"])
etym_letter = etym_letter.reindex(index=letters_order).fillna(0)
# Keep only letters with data
etym_letter = etym_letter[etym_letter.sum(axis=1) > 0]

etym_colors = {
    "al- prefix preserved": PAL["blue"],
    "al- assimilated": PAL["lightblue"],
    "direct transliteration": PAL["orange"],
    "other adaptation": PAL["teal"],
    "compound / phrase": PAL["purple"],
    "personal name": PAL["red"],
}
col_order = [c for c in ["al- prefix preserved", "direct transliteration",
                          "other adaptation", "al- assimilated",
                          "compound / phrase", "personal name"]
             if c in etym_letter.columns]
etym_letter = etym_letter[col_order]
colors_list = [etym_colors.get(c, PAL["gray"]) for c in col_order]

etym_letter.plot(kind="bar", stacked=True, ax=ax, color=colors_list, width=0.75)
ax.set_xlabel("letter section", fontsize=12)
ax.set_ylabel("number of Arabic term detections", fontsize=12)
ax.set_title("Etymology Adaptation Patterns Across the Dictionary\n"
             "(How Arabic terms entered Latin, by letter section)", fontsize=13)
ax.legend(title="etymology type", bbox_to_anchor=(1.0, 1.0), fontsize=9)
ax.set_xticklabels(etym_letter.index, rotation=0)

# Annotate totals
for i, letter in enumerate(etym_letter.index):
    total = etym_letter.loc[letter].sum()
    if total > 0:
        ax.text(i, total + 0.5, str(int(total)), ha="center", fontsize=8,
                fontweight="bold")

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "etymology_by_letter.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ etymology_by_letter.png")


# ── Fig 6: CONFIDENCE BY ETYMOLOGY TYPE ──────────────────────────
# Are some adaptation patterns detected more reliably?
print("\nFig 6: Confidence by etymology type…")

fig, axes = plt.subplots(1, 2, figsize=(16, 7))

# Left: violin/box plot of confidence by etymology
ax = axes[0]
etym_order_conf = clean_df.groupby("etymology_type")["confidence_score"].median().sort_values(ascending=False).index
plot_data = clean_df[clean_df["etymology_type"].isin(etym_order_conf)]
sns.boxplot(data=plot_data, y="etymology_type", x="confidence_score",
            order=etym_order_conf, ax=ax, palette="Set2", width=0.6)
ax.set_xlabel("confidence score")
ax.set_ylabel("")
ax.set_title("Detection Confidence by Etymology Type", fontsize=12)
ax.axvline(0.8, ls="--", color=PAL["red"], alpha=0.5, label="gold threshold (0.8)")
ax.legend(fontsize=8)

# Right: quality tier distribution per etymology
ax = axes[1]
tier_etym = pd.crosstab(clean_df["etymology_type"], clean_df["quality_tier"])
tier_order = ["gold", "silver", "bronze"]
tier_etym = tier_etym.reindex(columns=[t for t in tier_order if t in tier_etym.columns])
tier_etym = tier_etym.reindex(etym_order_conf)
tier_colors = {"gold": PAL["gold"], "silver": PAL["gray"], "bronze": PAL["brown"]}
tier_etym.plot(kind="barh", stacked=True, ax=ax,
               color=[tier_colors.get(c, PAL["gray"]) for c in tier_etym.columns],
               width=0.6)
ax.set_xlabel("number of terms")
ax.set_ylabel("")
ax.set_title("Quality Tier Distribution by Etymology Type", fontsize=12)
ax.legend(title="quality tier")

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "confidence_by_etymology.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ confidence_by_etymology.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PART B: ALPHABETICAL TIMELINE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Join Arabic detection info to the sequential XML entries
arabic_per_hw = clean_df.groupby("lemma").agg(
    arabic_count=("detected_string", "count"),
    arabic_terms=("detected_string", lambda x: ", ".join(sorted(x.unique()))),
    domains=("domain", lambda x: ", ".join(sorted(x.unique()))),
    etym_types=("etymology_type", lambda x: ", ".join(sorted(x.unique()))),
).rename_axis("headword")

seq_df = xml_df.merge(arabic_per_hw, on="headword", how="left")
seq_df["arabic_count"] = seq_df["arabic_count"].fillna(0).astype(int)
seq_df["has_arabic"] = seq_df["arabic_count"] > 0
seq_df = seq_df.sort_values("seq_idx").reset_index(drop=True)


# ── Fig 7: DICTIONARY SKYLINE ────────────────────────────────────
# Every entry as a thin vertical bar; height = word count; color = Arabic
print("\nFig 7: Dictionary skyline…")

fig, axes = plt.subplots(2, 1, figsize=(22, 10), gridspec_kw={"height_ratios": [3, 1]})

# Top: skyline
ax = axes[0]
n = len(seq_df)
x = np.arange(n)
colors_sky = [PAL["orange"] if ha else PAL["lightblue"]
              for ha in seq_df["has_arabic"]]
# Use log scale for height to make short entries visible
heights = np.log1p(seq_df["word_count"].values)

ax.bar(x, heights, width=1.0, color=colors_sky, linewidth=0, edgecolor="none")
ax.set_ylabel("entry length (log scale)", fontsize=11)
ax.set_title("The Dictionary Skyline: Every Entry in Ruland's Lexicon, A to Z\n"
             "(orange = entry contains Arabic-tradition terms; blue = no Arabic terms)",
             fontsize=13)

# Add letter section boundaries
prev_letter = ""
letter_positions = []
for i, row in seq_df.iterrows():
    if row["first_letter"] != prev_letter:
        letter_positions.append((i, row["first_letter"]))
        prev_letter = row["first_letter"]

for pos, letter in letter_positions:
    ax.axvline(pos, color="gray", alpha=0.3, linewidth=0.5)
    ax.text(pos + 5, ax.get_ylim()[1] * 0.95, letter, fontsize=9,
            fontweight="bold", color=PAL["darkblue"], va="top")

ax.set_xlim(0, n)
ax.set_xticks([])

# Add legend
handles = [mpatches.Patch(color=PAL["orange"], label="contains Arabic terms"),
           mpatches.Patch(color=PAL["lightblue"], label="no Arabic terms")]
ax.legend(handles=handles, loc="upper right", fontsize=10)

# Bottom: rolling Arabic density
ax = axes[1]
window = 50
rolling_arabic = pd.Series(seq_df["has_arabic"].astype(float)).rolling(window, center=True).mean() * 100
ax.fill_between(x, rolling_arabic, alpha=0.6, color=PAL["orange"])
ax.plot(x, rolling_arabic, color=PAL["darkorange"], linewidth=1)
ax.set_ylabel(f"Arabic density\n(% in {window}-entry window)", fontsize=10)
ax.set_xlabel("sequential position in dictionary (entry number)", fontsize=11)
ax.set_xlim(0, n)
ax.set_ylim(0, rolling_arabic.max() * 1.2 if rolling_arabic.max() > 0 else 10)

# Letter markers
for pos, letter in letter_positions:
    ax.axvline(pos, color="gray", alpha=0.2, linewidth=0.5)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "dictionary_skyline.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ dictionary_skyline.png")


# ── Fig 8: CUMULATIVE DISCOVERY CURVE ────────────────────────────
# As you read A→Z, how does your knowledge of Arabic terms accumulate?
print("\nFig 8: Cumulative discovery curve…")

fig, axes = plt.subplots(2, 1, figsize=(18, 10), gridspec_kw={"height_ratios": [2, 1]})

# Track unique terms discovered as we traverse the dictionary
seen_terms = set()
seen_entries = set()
cumul_terms = []
cumul_entries = []
entry_positions = []

for _, row in seq_df.iterrows():
    if row["has_arabic"]:
        terms = str(row.get("arabic_terms", "")).split(", ")
        for t in terms:
            if t and t != "nan":
                seen_terms.add(t)
        seen_entries.add(row["headword"])
    cumul_terms.append(len(seen_terms))
    cumul_entries.append(len(seen_entries))

# Top: cumulative unique terms + entries
ax = axes[0]
ax.plot(range(n), cumul_terms, color=PAL["orange"], linewidth=2,
        label="unique Arabic terms discovered")
ax.plot(range(n), cumul_entries, color=PAL["blue"], linewidth=2, linestyle="--",
        label="dictionary entries with Arabic terms")
ax.set_ylabel("cumulative count", fontsize=11)
ax.set_title("Cumulative Discovery: Arabic Terms Encountered While Reading A → Z\n"
             "(Each step rightward = next dictionary entry in sequence)", fontsize=13)
ax.legend(fontsize=10)

# Mark letter boundaries and annotate key discovery moments
for pos, letter in letter_positions:
    ax.axvline(pos, color="gray", alpha=0.15, linewidth=0.5)
    ax.text(pos, ax.get_ylim()[1] * 0.02, letter, fontsize=8,
            color=PAL["darkblue"], ha="center", fontweight="bold")

# Annotate steepest jumps — where do we learn the most new terms?
diffs = np.diff(cumul_terms)
# Find letter-section boundaries and compute per-section gain
section_gains = []
for i in range(len(letter_positions)):
    start = letter_positions[i][0]
    end = letter_positions[i+1][0] if i+1 < len(letter_positions) else n
    letter = letter_positions[i][1]
    gain = cumul_terms[end-1] - cumul_terms[start]
    section_gains.append((letter, gain, start, end))

section_gains.sort(key=lambda x: -x[1])
# Annotate top 5 sections
for rank, (letter, gain, start, end) in enumerate(section_gains[:5]):
    mid = (start + end) // 2
    y_val = cumul_terms[mid]
    ax.annotate(f"{letter}: +{gain} terms",
                xy=(mid, y_val), xytext=(mid + 80, y_val + 15 + rank*12),
                fontsize=8, color=PAL["darkorange"],
                arrowprops=dict(arrowstyle="->", color=PAL["darkorange"], lw=0.8))

# Bottom: per-section gain bar chart
ax = axes[1]
gain_df = pd.DataFrame(section_gains, columns=["letter", "gain", "start", "end"])
gain_df = gain_df.sort_values("start")
bars = ax.bar(gain_df["letter"], gain_df["gain"],
              color=[PAL["orange"] if g > 10 else PAL["lightblue"] for g in gain_df["gain"]])
ax.set_xlabel("letter section", fontsize=11)
ax.set_ylabel("new Arabic terms\ndiscovered", fontsize=10)
ax.set_title("Arabic Term Discovery by Letter Section", fontsize=12)
for i, row in gain_df.iterrows():
    if row["gain"] > 0:
        ax.text(list(gain_df["letter"]).index(row["letter"]), row["gain"] + 0.5,
                str(int(row["gain"])), ha="center", fontsize=8)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "cumulative_discovery.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ cumulative_discovery.png")


# ── Fig 9: SEMANTIC STRATIGRAPHY ─────────────────────────────────
# Stacked area: what kinds of Arabic terms appear as we move A→Z?
print("\nFig 9: Semantic stratigraphy…")

# For each entry position, track cumulative domain counts
domain_names = ["Minerals & Salts", "Organic & Natural", "Apparatus & Process",
                "Medical & Alchemical", "Other", "Unclassified"]
domain_cumul = {d: [] for d in domain_names}
domain_counts = {d: 0 for d in domain_names}

# Build a mapping: headword → list of domains from clean_df
hw_domains = clean_df.groupby("lemma")["domain"].apply(list).to_dict()

for _, row in seq_df.iterrows():
    hw = row["headword"]
    if hw in hw_domains:
        for d in hw_domains[hw]:
            if d in domain_counts:
                domain_counts[d] += 1
    for d in domain_names:
        domain_cumul[d].append(domain_counts[d])

fig, ax = plt.subplots(figsize=(20, 8))

# Stacked area
x_pos = np.arange(n)
domain_colors = {
    "Minerals & Salts": PAL["blue"],
    "Organic & Natural": PAL["green"],
    "Apparatus & Process": PAL["orange"],
    "Medical & Alchemical": PAL["red"],
    "Other": PAL["gray"],
    "Unclassified": PAL["lightblue"],
}

bottoms = np.zeros(n)
for domain in domain_names:
    vals = np.array(domain_cumul[domain], dtype=float)
    ax.fill_between(x_pos, bottoms, bottoms + vals, alpha=0.7,
                    color=domain_colors[domain], label=domain)
    bottoms += vals

ax.set_xlabel("sequential position in dictionary (entry number)", fontsize=11)
ax.set_ylabel("cumulative Arabic term count", fontsize=11)
ax.set_title("Semantic Stratigraphy: Arabic Term Domains Accumulating A → Z\n"
             "(Reading the dictionary from start to finish, what kinds of Arabic terms do we encounter?)",
             fontsize=13)
ax.legend(loc="upper left", fontsize=9, title="semantic domain")
ax.set_xlim(0, n)

# Letter markers
for pos, letter in letter_positions:
    ax.axvline(pos, color="white", alpha=0.4, linewidth=0.5)
    ax.text(pos + 3, ax.get_ylim()[1] * 0.98, letter, fontsize=8,
            fontweight="bold", color="white", va="top")

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "semantic_stratigraphy.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ semantic_stratigraphy.png")


# ── Fig 10: FIRST APPEARANCE — WHEN ARE KEY TERMS FIRST ENCOUNTERED? ─
print("\nFig 10: First appearance of key terms…")

# For each Arabic term, find the earliest entry (by seq_idx) where it appears
term_first = {}
term_all_positions = defaultdict(list)

for _, row in seq_df.iterrows():
    if row["has_arabic"]:
        terms = str(row.get("arabic_terms", "")).split(", ")
        for t in terms:
            if t and t != "nan":
                if t not in term_first:
                    term_first[t] = (row["seq_idx"], row["headword"], row["first_letter"])
                term_all_positions[t].append(row["seq_idx"])

# Select the 30 most frequent terms
top_freq = clean_df["detected_string"].value_counts().head(30).index.tolist()
top_freq_with_pos = []
for t in top_freq:
    if t in term_first:
        first_pos, first_hw, first_letter = term_first[t]
        all_pos = term_all_positions[t]
        top_freq_with_pos.append({
            "term": t, "first_pos": first_pos, "first_hw": first_hw,
            "first_letter": first_letter, "n_appearances": len(all_pos),
            "all_positions": all_pos,
        })

top_df = pd.DataFrame(top_freq_with_pos).sort_values("first_pos")

fig, ax = plt.subplots(figsize=(20, 10))

y_pos = np.arange(len(top_df))
# Draw a line from first to last appearance for each term
for i, (_, row) in enumerate(top_df.iterrows()):
    positions = sorted(row["all_positions"])
    # Span line
    ax.plot([positions[0], positions[-1]], [i, i],
            color=PAL["lightblue"], linewidth=2, alpha=0.5)
    # Individual appearances as dots
    ax.scatter(positions, [i] * len(positions),
               s=20, color=PAL["orange"], zorder=3, alpha=0.7)
    # First appearance marker
    ax.scatter([positions[0]], [i], s=80, color=PAL["red"],
               zorder=4, marker="D", edgecolors="white", linewidths=0.5)

ax.set_yticks(y_pos)
ax.set_yticklabels([f'{row["term"]}  (first in "{row["first_hw"]}")'
                     for _, row in top_df.iterrows()], fontsize=9)
ax.invert_yaxis()
ax.set_xlabel("sequential position in dictionary (entry number)", fontsize=11)
ax.set_title("First Appearance and Lifespan of Key Arabic Terms\n"
             "(Diamond = first encounter; dots = all mentions; line = span from first to last)",
             fontsize=13)

# Letter boundaries
for pos, letter in letter_positions:
    ax.axvline(pos, color="gray", alpha=0.15, linewidth=0.5)
    ax.text(pos, -0.8, letter, fontsize=8, ha="center",
            color=PAL["darkblue"], fontweight="bold")

ax.set_xlim(-10, n + 10)
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "first_appearance.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ first_appearance.png")


# ── Fig 11: ARABIC DENSITY WAVE ──────────────────────────────────
# Rolling density with different window sizes + domain breakdown
print("\nFig 11: Arabic density wave…")

fig, axes = plt.subplots(3, 1, figsize=(20, 12), sharex=True)

# Panel 1: multiple window sizes
ax = axes[0]
for window_sz, color, alpha in [(20, PAL["orange"], 0.3),
                                 (50, PAL["red"], 0.5),
                                 (100, PAL["darkblue"], 0.8)]:
    rolling = pd.Series(seq_df["has_arabic"].astype(float)).rolling(
        window_sz, center=True).mean() * 100
    ax.plot(range(n), rolling, color=color, linewidth=1.5, alpha=alpha,
            label=f"{window_sz}-entry window")
ax.set_ylabel("% entries with Arabic", fontsize=10)
ax.set_title("Arabic Density Waves: How Arabic Concentration Ebbs and Flows A → Z\n"
             "(Multiple smoothing windows reveal patterns at different scales)", fontsize=13)
ax.legend(fontsize=9)

# Panel 2: entry length rolling average (is there a correlation?)
ax = axes[1]
rolling_wc = pd.Series(seq_df["word_count"].astype(float)).rolling(50, center=True).mean()
ax.fill_between(range(n), rolling_wc, alpha=0.4, color=PAL["purple"])
ax.plot(range(n), rolling_wc, color=PAL["purple"], linewidth=1)
ax.set_ylabel("mean entry length\n(50-entry window)", fontsize=10)
ax.set_title("Entry Length Wave: Do Longer Entries Coincide with Arabic-Dense Regions?", fontsize=12)

# Panel 3: mark specific "peaks" of Arabic density
ax = axes[2]
rolling_50 = pd.Series(seq_df["has_arabic"].astype(float)).rolling(50, center=True).mean() * 100
ax.fill_between(range(n), rolling_50, alpha=0.5, color=PAL["orange"])
ax.plot(range(n), rolling_50, color=PAL["darkorange"], linewidth=1.5)

# Find peaks (local maxima above 20%)
from scipy.signal import find_peaks as _find_peaks
try:
    peaks, _ = _find_peaks(rolling_50.fillna(0).values, height=15, distance=100)
    for p in peaks:
        hw = seq_df.iloc[p]["headword"] if p < len(seq_df) else ""
        letter = seq_df.iloc[p]["first_letter"] if p < len(seq_df) else ""
        ax.annotate(f"peak near '{letter}' section\n({hw}…)",
                    xy=(p, rolling_50.iloc[p]),
                    xytext=(p, rolling_50.iloc[p] + 8),
                    fontsize=8, color=PAL["red"],
                    arrowprops=dict(arrowstyle="->", color=PAL["red"], lw=0.8),
                    ha="center")
except ImportError:
    # If scipy not available, skip peak detection
    pass

ax.set_ylabel("Arabic density (%)", fontsize=10)
ax.set_xlabel("sequential position in dictionary (entry number)", fontsize=11)
ax.set_title("Arabic Density with Peak Annotations", fontsize=12)

# Letter markers on all panels
for axi in axes:
    for pos, letter in letter_positions:
        axi.axvline(pos, color="gray", alpha=0.12, linewidth=0.5)
    axi.set_xlim(0, n)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "density_wave.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ density_wave.png")


print(f"\nAll done. {len(os.listdir(OUTDIR))} files in {OUTDIR}")
for f in sorted(os.listdir(OUTDIR)):
    print(f"  {f}")
