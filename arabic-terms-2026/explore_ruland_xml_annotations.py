#!/usr/bin/env python3
"""
Ruland 1612 – XML Annotation Analysis
======================================
Exploiting the TEI XML structure: bilingual entries (Latin/German),
variant spellings, authority citations, entry complexity, page-level
distribution, and code-switching patterns.
"""

import os, re, textwrap
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import seaborn as sns
from collections import Counter, defaultdict

# ── paths ───────────────────────────────────────────────────────────
XML_PATH = "/tmp/Ruland.xml"
CSV_CLEAN = "/Users/slang/claude/ruland_exploration/ruland_arabic_cleaned.csv"
OUTDIR = "/Users/slang/claude/ruland_exploration/07_xml_annotations"
os.makedirs(OUTDIR, exist_ok=True)

sns.set_theme(style="whitegrid", font_scale=1.05)
PAL = {
    "blue": "#4C78A8", "orange": "#F58518", "teal": "#72B7B2",
    "red": "#E45756", "green": "#54A24B", "purple": "#B279A2",
    "pink": "#FF9DA6", "brown": "#9D7660", "gray": "#BAB0AC",
    "gold": "#EECA3B", "darkblue": "#2D4A7A", "lightblue": "#9ECAE9",
    "darkorange": "#D4780A", "darkgreen": "#2E7D32",
}

ns = "{http://www.tei-c.org/ns/1.0}"
xml_ns = "{http://www.w3.org/XML/1998/namespace}"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PARSE XML with full annotation detail
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("Parsing XML with annotation detail…")

tree = ET.parse(XML_PATH)
root = tree.getroot()

entries = []
current_page = 0

# Track page breaks at document level first
page_positions = []  # (seq_idx_approx, page_num)

seq_idx = 0
for elem in root.iter():
    tag = elem.tag.replace(ns, "")
    if tag == "pb":
        pn = elem.get("n", "")
        try:
            current_page = int(pn)
        except ValueError:
            current_page += 1
        page_positions.append((seq_idx, current_page))
    if tag == "entry":
        form_el = elem.find(f".//{ns}form[@type='lemma']")
        hw = form_el.text.strip() if form_el is not None and form_el.text else ""
        full_text = "".join(elem.itertext()).strip()

        # German translations
        cit_de = elem.findall(f".//{ns}cit[@{xml_ns}lang='de']")
        de_texts = []
        for c in cit_de:
            quote = c.find(f"{ns}quote")
            if quote is not None:
                qt = "".join(quote.itertext()).strip()
                if qt:
                    de_texts.append(qt)
        has_german = len(de_texts) > 0
        german_text = " ".join(de_texts)
        german_word_count = len(german_text.split()) if german_text else 0

        # Fraktur-marked text
        fraktur_cits = [c for c in elem.findall(f".//{ns}cit")
                        if "fraktur" in c.get("style", "")]
        fraktur_word_count = 0
        for fc in fraktur_cits:
            ft = "".join(fc.itertext()).strip()
            fraktur_word_count += len(ft.split())

        # Variant forms
        variants = elem.findall(f".//{ns}form[@type='variant']")
        variant_texts = []
        for v in variants:
            vt = v.text.strip() if v.text else ""
            if vt:
                variant_texts.append(vt)

        # Orthographic variants
        orths = elem.findall(f".//{ns}orth")
        orth_texts = []
        for o in orths:
            ot = o.text.strip() if o.text else ""
            if ot:
                orth_texts.append(ot)

        # Phrases
        phrases = elem.findall(f".//{ns}form[@type='phrase']")

        # Notes
        notes = elem.findall(f".//{ns}note")
        note_texts = []
        for n in notes:
            nt = "".join(n.itertext()).strip()
            if nt:
                note_texts.append(nt)

        # Definitions
        defs = elem.findall(f".//{ns}def")
        has_def = len(defs) > 0

        # Senses
        senses = elem.findall(f".//{ns}sense")

        # Entry type (letter section)
        entry_type = elem.get("type", "")

        # Count structural elements
        word_count = len(full_text.split())

        entries.append({
            "seq_idx": seq_idx,
            "headword": hw,
            "first_letter": hw[0].upper() if hw else "",
            "entry_type": entry_type,
            "word_count": word_count,
            "full_text": full_text,
            # Bilingual
            "has_german": has_german,
            "n_german_segments": len(de_texts),
            "german_word_count": german_word_count,
            "fraktur_word_count": fraktur_word_count,
            "german_ratio": german_word_count / word_count if word_count > 0 else 0,
            # Variants
            "n_variants": len(variant_texts),
            "variant_texts": "; ".join(variant_texts) if variant_texts else "",
            "n_orths": len(orth_texts),
            "orth_texts": "; ".join(orth_texts) if orth_texts else "",
            # Structure
            "has_phrase": len(phrases) > 0,
            "n_notes": len(notes),
            "note_texts": " ||| ".join(note_texts) if note_texts else "",
            "has_def": has_def,
            "n_senses": len(senses),
            "n_defs": len(defs),
            # Page
            "page": current_page,
        })
        seq_idx += 1

xml_df = pd.DataFrame(entries)
xml_df = xml_df[xml_df["headword"] != ""]

# Load cleaned Arabic CSV
clean_df = pd.read_csv(CSV_CLEAN)
arabic_lemmas = set(clean_df["lemma"].unique())
arabic_per_hw = clean_df.groupby("lemma").agg(
    arabic_count=("detected_string", "count"),
    arabic_terms=("detected_string", lambda x: ", ".join(sorted(x.unique()))),
).rename_axis("headword")

xml_df["has_arabic"] = xml_df["headword"].isin(arabic_lemmas)
xml_df = xml_df.merge(arabic_per_hw, on="headword", how="left")
xml_df["arabic_count"] = xml_df["arabic_count"].fillna(0).astype(int)

print(f"  Parsed {len(xml_df)} entries")
print(f"  Entries with German: {xml_df['has_german'].sum()} ({100*xml_df['has_german'].mean():.1f}%)")
print(f"  Entries with variants: {(xml_df['n_variants'] > 0).sum()}")
print(f"  Entries with notes: {(xml_df['n_notes'] > 0).sum()}")
print(f"  Entries with Arabic: {xml_df['has_arabic'].sum()}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 1: BILINGUAL OVERVIEW — GERMAN TRANSLATIONS × ARABIC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 1: Bilingual overview…")

fig, axes = plt.subplots(2, 2, figsize=(18, 14))

# Panel 1: German translation rate — Arabic vs non-Arabic entries
ax = axes[0, 0]
arabic_german = xml_df[xml_df["has_arabic"]]["has_german"].mean() * 100
nonarabic_german = xml_df[~xml_df["has_arabic"]]["has_german"].mean() * 100
bars = ax.bar(["Arabic-origin\nentries", "Non-Arabic\nentries"],
              [arabic_german, nonarabic_german],
              color=[PAL["orange"], PAL["blue"]], width=0.5)
ax.set_ylabel("% of entries with German translation")
ax.set_title("Do Arabic-Origin Entries Get German Translations?", fontsize=12)
ax.set_ylim(0, 100)
for bar, pct in zip(bars, [arabic_german, nonarabic_german]):
    n = int(xml_df[xml_df["has_arabic"]]["has_german"].sum()) if bar.get_x() < 0.5 else int(xml_df[~xml_df["has_arabic"]]["has_german"].sum())
    total = xml_df["has_arabic"].sum() if bar.get_x() < 0.5 else (~xml_df["has_arabic"]).sum()
    ax.text(bar.get_x() + bar.get_width()/2, pct + 2,
            f"{pct:.1f}%\n({n}/{total})", ha="center", fontsize=10)

# Panel 2: German translation rate by letter section
ax = axes[0, 1]
letters_order = sorted(xml_df["first_letter"].unique())
letter_bilingual = xml_df.groupby("first_letter").agg(
    german_rate_all=("has_german", "mean"),
).reindex(letters_order) * 100

# Arabic entries only
arabic_only = xml_df[xml_df["has_arabic"]]
letter_bilingual_ar = arabic_only.groupby("first_letter")["has_german"].mean().reindex(letters_order) * 100

x = np.arange(len(letters_order))
w = 0.35
ax.bar(x - w/2, letter_bilingual["german_rate_all"], w,
       label="all entries", color=PAL["blue"], alpha=0.7)
ax.bar(x + w/2, letter_bilingual_ar.fillna(0), w,
       label="Arabic-origin entries", color=PAL["orange"], alpha=0.7)
ax.set_xticks(x)
ax.set_xticklabels(letters_order, fontsize=8)
ax.set_ylabel("% with German translation")
ax.set_title("German Translation Rate by Letter Section", fontsize=12)
ax.legend(fontsize=9)

# Panel 3: German proportion of entry text
ax = axes[1, 0]
# For entries with German, what fraction of the text is German?
bilingual_entries = xml_df[xml_df["has_german"]].copy()
arabic_bilingual = bilingual_entries[bilingual_entries["has_arabic"]]
nonarabic_bilingual = bilingual_entries[~bilingual_entries["has_arabic"]]

data_ratio = pd.DataFrame({
    "group": (["Arabic entries"] * len(arabic_bilingual) +
              ["Non-Arabic entries"] * len(nonarabic_bilingual)),
    "german_ratio": list(arabic_bilingual["german_ratio"]) + list(nonarabic_bilingual["german_ratio"]),
})
# Cap ratio at 1 for display
data_ratio["german_ratio"] = data_ratio["german_ratio"].clip(upper=1.0) * 100

sns.boxplot(data=data_ratio, x="group", y="german_ratio", ax=ax,
            palette=[PAL["orange"], PAL["blue"]], width=0.4)
ax.set_ylabel("German text as % of total entry")
ax.set_xlabel("")
ax.set_title("How Much German? Text Proportion\n(among entries with German translations)", fontsize=12)

# Panel 4: examples — Arabic entries with German translations
ax = axes[1, 1]
ax.axis("off")
# Find Arabic entries with longest German text
top_de_arabic = xml_df[(xml_df["has_arabic"]) & (xml_df["has_german"])].nlargest(12, "german_word_count")
text = "Arabic Entries with German Translations\n"
text += "═" * 55 + "\n\n"
for _, row in top_de_arabic.iterrows():
    hw = row["headword"][:25]
    de_wc = row["german_word_count"]
    total_wc = row["word_count"]
    pct = 100 * row["german_ratio"]
    text += f"▸ {hw:25s}  {de_wc:3d} German words / {total_wc:4d} total ({pct:.0f}%)\n"
ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9.5,
        va="top", fontfamily="monospace", linespacing=1.4)
ax.set_title("Arabic Entries with Most German Text", fontsize=12)

plt.suptitle("Bilingual Analysis: Latin/German in Ruland's Dictionary × Arabic Content",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "bilingual_overview.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ bilingual_overview.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 2: CODE-SWITCHING — LATIN ↔ GERMAN PATTERNS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 2: Code-switching patterns…")

fig, axes = plt.subplots(2, 2, figsize=(18, 13))

# Panel 1: Distribution of German ratio for Arabic vs non-Arabic
ax = axes[0, 0]
bins_r = np.arange(0, 1.05, 0.05)
arabic_ratios = xml_df[xml_df["has_arabic"] & xml_df["has_german"]]["german_ratio"].clip(upper=1.0)
nonarabic_ratios = xml_df[~xml_df["has_arabic"] & xml_df["has_german"]]["german_ratio"].clip(upper=1.0)
ax.hist(arabic_ratios, bins=bins_r, alpha=0.6, color=PAL["orange"],
        label=f"Arabic entries (n={len(arabic_ratios)})", density=True)
ax.hist(nonarabic_ratios, bins=bins_r, alpha=0.6, color=PAL["blue"],
        label=f"Non-Arabic entries (n={len(nonarabic_ratios)})", density=True)
ax.set_xlabel("German text as fraction of total entry")
ax.set_ylabel("density")
ax.set_title("German Text Proportion: Arabic vs Non-Arabic Entries", fontsize=12)
ax.legend(fontsize=9)

# Panel 2: number of German segments per entry
ax = axes[0, 1]
seg_arabic = xml_df[xml_df["has_arabic"]]["n_german_segments"]
seg_nonarabic = xml_df[~xml_df["has_arabic"]]["n_german_segments"]
max_seg = min(10, max(seg_arabic.max(), seg_nonarabic.max()) + 1)
bins_s = np.arange(-0.5, max_seg + 1.5, 1)
ax.hist(seg_arabic, bins=bins_s, alpha=0.6, color=PAL["orange"],
        label="Arabic entries", density=True)
ax.hist(seg_nonarabic, bins=bins_s, alpha=0.6, color=PAL["blue"],
        label="Non-Arabic entries", density=True)
ax.set_xlabel("number of German translation segments per entry")
ax.set_ylabel("density")
ax.set_title("German Segments per Entry: How Often Does Ruland Switch?", fontsize=12)
ax.legend(fontsize=9)

# Panel 3: German ratio vs entry length scatter
ax = axes[1, 0]
has_de_df = xml_df[xml_df["has_german"]].copy()
ax.scatter(has_de_df[~has_de_df["has_arabic"]]["word_count"],
           has_de_df[~has_de_df["has_arabic"]]["german_ratio"].clip(upper=1.0) * 100,
           alpha=0.3, s=15, color=PAL["blue"], label="non-Arabic")
ax.scatter(has_de_df[has_de_df["has_arabic"]]["word_count"],
           has_de_df[has_de_df["has_arabic"]]["german_ratio"].clip(upper=1.0) * 100,
           alpha=0.5, s=25, color=PAL["orange"], label="Arabic", zorder=3)
ax.set_xlabel("entry length (words)")
ax.set_ylabel("German text as % of entry")
ax.set_title("Entry Length vs German Proportion\n(Do longer entries have more or less German?)", fontsize=12)
ax.set_xscale("log")
ax.legend(fontsize=9)

# Panel 4: Fraktur-marked text analysis
ax = axes[1, 1]
# Entries where Fraktur word count > 0
fraktur_entries = xml_df[xml_df["fraktur_word_count"] > 0].copy()
fraktur_entries["fraktur_ratio"] = fraktur_entries["fraktur_word_count"] / fraktur_entries["word_count"]
arabic_fraktur = fraktur_entries[fraktur_entries["has_arabic"]]
nonarabic_fraktur = fraktur_entries[~fraktur_entries["has_arabic"]]

labels_f = ["Arabic entries", "Non-Arabic entries"]
means_f = [arabic_fraktur["fraktur_ratio"].mean() * 100 if len(arabic_fraktur) > 0 else 0,
           nonarabic_fraktur["fraktur_ratio"].mean() * 100 if len(nonarabic_fraktur) > 0 else 0]
counts_f = [len(arabic_fraktur), len(nonarabic_fraktur)]
bars = ax.bar(labels_f, means_f, color=[PAL["orange"], PAL["blue"]], width=0.4)
ax.set_ylabel("mean Fraktur text as % of entry")
ax.set_title("Fraktur (German Script) Proportion\n(among entries with Fraktur text)", fontsize=12)
for bar, m, c in zip(bars, means_f, counts_f):
    ax.text(bar.get_x() + bar.get_width()/2, m + 1,
            f"{m:.1f}%\n(n={c})", ha="center", fontsize=10)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "code_switching.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ code_switching.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 3: AUTHORITY CITATIONS IN NOTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 3: Authority citations in notes…")

# Known authorities to search for in note texts
AUTHORITIES = {
    "Pliny": ["plin", "plini"],
    "Dioscorides": ["dioscorid"],
    "Galen": ["galen"],
    "Avicenna": ["avicenn"],
    "Geber/Jabir": ["geber", "gebri", "jabir"],
    "Rhazes": ["rhazes", "rhasis"],
    "Albertus Magnus": ["albert"],
    "Paracelsus/Theophrastus": ["paracel", "theophrast"],
    "Aristotle": ["aristotel", "aristot"],
    "Lull/Lullus": ["lull"],
    "Arnold of Villanova": ["arnold"],
    "Thomas Aquinas": ["thomas", "aquin"],
    "Serapio": ["serapio"],
}

# Also search full entry texts for these authorities
def find_authorities(text):
    """Find all authority names mentioned in text."""
    found = []
    t = text.lower()
    for auth, keywords in AUTHORITIES.items():
        for kw in keywords:
            if kw in t:
                found.append(auth)
                break
    return found

xml_df["authorities"] = xml_df["full_text"].apply(find_authorities)
xml_df["n_authorities"] = xml_df["authorities"].apply(len)
xml_df["has_authorities"] = xml_df["n_authorities"] > 0

fig, axes = plt.subplots(2, 2, figsize=(20, 14))

# Panel 1: authority citation frequency overall
ax = axes[0, 0]
auth_counter = Counter()
for auths in xml_df["authorities"]:
    for a in auths:
        auth_counter[a] += 1
auth_s = pd.Series(auth_counter).sort_values(ascending=True)
auth_colors = []
arabic_authors = {"Avicenna", "Geber/Jabir", "Rhazes", "Serapio"}
for a in auth_s.index:
    auth_colors.append(PAL["orange"] if a in arabic_authors else PAL["blue"])
ax.barh(range(len(auth_s)), auth_s.values, color=auth_colors)
ax.set_yticks(range(len(auth_s)))
ax.set_yticklabels(auth_s.index, fontsize=10)
ax.set_xlabel("number of entries citing this authority")
ax.set_title("Authority Citations in Ruland's Dictionary\n(orange = Arabic/Islamic scholar; blue = Greek/Latin/European)",
             fontsize=12)
for i, v in enumerate(auth_s.values):
    ax.text(v + 2, i, str(v), va="center", fontsize=9)

# Panel 2: Arabic vs non-Arabic entries — authority citation rate
ax = axes[0, 1]
arabic_auth_rate = xml_df[xml_df["has_arabic"]]["has_authorities"].mean() * 100
nonarabic_auth_rate = xml_df[~xml_df["has_arabic"]]["has_authorities"].mean() * 100
bars = ax.bar(["Arabic-origin\nentries", "Non-Arabic\nentries"],
              [arabic_auth_rate, nonarabic_auth_rate],
              color=[PAL["orange"], PAL["blue"]], width=0.4)
ax.set_ylabel("% of entries citing any authority")
ax.set_title("Do Arabic Entries Cite More Authorities?", fontsize=12)
for bar, pct in zip(bars, [arabic_auth_rate, nonarabic_auth_rate]):
    ax.text(bar.get_x() + bar.get_width()/2, pct + 1,
            f"{pct:.1f}%", ha="center", fontsize=11)

# Panel 3: which authorities appear in Arabic vs non-Arabic entries?
ax = axes[1, 0]
auth_arabic = Counter()
auth_nonarabic = Counter()
for _, row in xml_df.iterrows():
    for a in row["authorities"]:
        if row["has_arabic"]:
            auth_arabic[a] += 1
        else:
            auth_nonarabic[a] += 1

all_auths = sorted(set(list(auth_arabic.keys()) + list(auth_nonarabic.keys())),
                    key=lambda x: auth_arabic.get(x, 0) + auth_nonarabic.get(x, 0))
y = np.arange(len(all_auths))
w = 0.35
ax.barh(y - w/2, [auth_arabic.get(a, 0) for a in all_auths], w,
        label="Arabic-origin entries", color=PAL["orange"])
ax.barh(y + w/2, [auth_nonarabic.get(a, 0) for a in all_auths], w,
        label="Non-Arabic entries", color=PAL["blue"])
ax.set_yticks(y)
ax.set_yticklabels(all_auths, fontsize=9)
ax.set_xlabel("number of entries")
ax.set_title("Authority Citations: Arabic vs Non-Arabic Entries", fontsize=12)
ax.legend(fontsize=9)

# Panel 4: co-citation network (text summary)
ax = axes[1, 1]
ax.axis("off")
# Find entries that cite both an Arabic and a Western authority
mixed_citations = []
for _, row in xml_df.iterrows():
    auths = set(row["authorities"])
    arab = auths & arabic_authors
    western = auths - arabic_authors
    if arab and western:
        mixed_citations.append({
            "headword": row["headword"],
            "arabic_auths": ", ".join(sorted(arab)),
            "western_auths": ", ".join(sorted(western)),
        })

text = f"Entries Citing Both Arabic AND Western Authorities\n"
text += f"({'=' * 55})\n"
text += f"Total: {len(mixed_citations)} entries\n\n"
for mc in mixed_citations[:15]:
    text += f"▸ {mc['headword'][:25]}\n"
    text += f"  Arabic: {mc['arabic_auths']}\n"
    text += f"  Western: {mc['western_auths']}\n\n"
if len(mixed_citations) > 15:
    text += f"  … and {len(mixed_citations) - 15} more"

ax.text(0.02, 0.98, text, transform=ax.transAxes, fontsize=8.5,
        va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title("Cross-Tradition Citations", fontsize=12)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "authority_citations.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ authority_citations.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 4: VARIANT SPELLINGS × ARABIC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 4: Variant spellings…")

fig, axes = plt.subplots(1, 3, figsize=(22, 9))

# Panel 1: variant rate — Arabic vs non-Arabic
ax = axes[0]
xml_df["has_variants"] = (xml_df["n_variants"] > 0) | (xml_df["n_orths"] > 0)
xml_df["total_variants"] = xml_df["n_variants"] + xml_df["n_orths"]

ar_variant_rate = xml_df[xml_df["has_arabic"]]["has_variants"].mean() * 100
nonar_variant_rate = xml_df[~xml_df["has_arabic"]]["has_variants"].mean() * 100
bars = ax.bar(["Arabic-origin\nentries", "Non-Arabic\nentries"],
              [ar_variant_rate, nonar_variant_rate],
              color=[PAL["orange"], PAL["blue"]], width=0.4)
ax.set_ylabel("% of entries with variant spellings")
ax.set_title("Spelling Variation Rate:\nArabic vs Non-Arabic Entries", fontsize=12)
for bar, pct in zip(bars, [ar_variant_rate, nonar_variant_rate]):
    ax.text(bar.get_x() + bar.get_width()/2, pct + 0.5,
            f"{pct:.1f}%", ha="center", fontsize=11)

# Panel 2: Arabic entries with variants — what are they?
ax = axes[1]
arabic_with_vars = xml_df[(xml_df["has_arabic"]) & (xml_df["has_variants"])].copy()
arabic_with_vars["all_variants"] = arabic_with_vars.apply(
    lambda r: "; ".join(filter(None, [r["variant_texts"], r["orth_texts"]])), axis=1)
arabic_with_vars = arabic_with_vars.sort_values("total_variants", ascending=False)

y = np.arange(len(arabic_with_vars))
ax.barh(y, arabic_with_vars["total_variants"], color=PAL["teal"])
labels_v = []
for _, row in arabic_with_vars.iterrows():
    vars_str = row["all_variants"][:50]
    if len(row["all_variants"]) > 50:
        vars_str += "…"
    labels_v.append(f'{row["headword"]}')
ax.set_yticks(y)
ax.set_yticklabels(labels_v, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel("number of variant forms")
ax.set_title("Arabic Entries with Spelling Variants", fontsize=12)
# Annotate with actual variants
for i, (_, row) in enumerate(arabic_with_vars.iterrows()):
    vars_str = row["all_variants"][:55]
    if len(row["all_variants"]) > 55:
        vars_str += "…"
    ax.text(row["total_variants"] + 0.1, i, vars_str, va="center", fontsize=7,
            color=PAL["darkblue"])

# Panel 3: variant forms that look Arabic
ax = axes[2]
ax.axis("off")
text = "Variant Spellings Suggesting Arabic Forms\n"
text += "═" * 55 + "\n\n"
# Identify variants containing Arabic-looking patterns
arabic_patterns = ["al", "ki", "az", "za", "kh", "dh"]
for _, row in arabic_with_vars.iterrows():
    all_vars = row["all_variants"].split("; ")
    arabic_looking = [v for v in all_vars if v and
                      any(v.lower().startswith(p) for p in ["al", "ki", "az"])]
    if arabic_looking or any("arabic" in v.lower() for v in all_vars):
        text += f"▸ {row['headword']}\n"
        text += f"  Variants: {', '.join(all_vars[:5])}\n\n"

# Also show non-Arabic entries with Arabic-looking variants
nonar_with_vars = xml_df[(~xml_df["has_arabic"]) & (xml_df["has_variants"])].copy()
nonar_with_vars["all_variants"] = nonar_with_vars.apply(
    lambda r: "; ".join(filter(None, [r["variant_texts"], r["orth_texts"]])), axis=1)
arabic_like_nonar = []
for _, row in nonar_with_vars.iterrows():
    all_vars = row["all_variants"].split("; ")
    for v in all_vars:
        if v and v.lower().startswith(("al", "ki", "az")):
            arabic_like_nonar.append((row["headword"], v))
            break

if arabic_like_nonar:
    text += "\nNon-Arabic entries with Arabic-looking variants:\n"
    text += "─" * 50 + "\n"
    for hw, var in arabic_like_nonar[:8]:
        text += f"  {hw:25s} → {var}\n"

ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9,
        va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title("Arabic-Looking Variant Forms", fontsize=12)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "variant_spellings.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ variant_spellings.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 5: ENTRY STRUCTURAL COMPLEXITY × ARABIC
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 5: Entry structural complexity…")

# Complexity score: sum of structural features
xml_df["complexity"] = (
    xml_df["has_german"].astype(int) +
    xml_df["has_variants"].astype(int) +
    (xml_df["n_notes"] > 0).astype(int) +
    xml_df["has_def"].astype(int) +
    (xml_df["n_german_segments"] > 1).astype(int) +
    xml_df["has_phrase"].astype(int) +
    xml_df["has_authorities"].astype(int)
)

fig, axes = plt.subplots(2, 2, figsize=(18, 14))

# Panel 1: complexity distribution — Arabic vs non-Arabic
ax = axes[0, 0]
max_c = xml_df["complexity"].max()
bins_c = np.arange(-0.5, max_c + 1.5, 1)
ax.hist(xml_df[xml_df["has_arabic"]]["complexity"], bins=bins_c, alpha=0.6,
        color=PAL["orange"], label="Arabic entries", density=True)
ax.hist(xml_df[~xml_df["has_arabic"]]["complexity"], bins=bins_c, alpha=0.6,
        color=PAL["blue"], label="Non-Arabic entries", density=True)
ax.set_xlabel("structural complexity score")
ax.set_ylabel("density")
ax.set_title("Entry Complexity: Arabic vs Non-Arabic\n(higher = more structural features)", fontsize=12)
ax.legend(fontsize=9)
# Add means
ar_mean = xml_df[xml_df["has_arabic"]]["complexity"].mean()
nonar_mean = xml_df[~xml_df["has_arabic"]]["complexity"].mean()
ax.axvline(ar_mean, color=PAL["orange"], ls="--", lw=2, alpha=0.8)
ax.axvline(nonar_mean, color=PAL["blue"], ls="--", lw=2, alpha=0.8)
ax.text(ar_mean + 0.1, ax.get_ylim()[1] * 0.9, f"Arabic\nmean={ar_mean:.1f}",
        fontsize=9, color=PAL["darkorange"])
ax.text(nonar_mean + 0.1, ax.get_ylim()[1] * 0.7, f"Non-Arabic\nmean={nonar_mean:.1f}",
        fontsize=9, color=PAL["darkblue"])

# Panel 2: individual feature rates
ax = axes[0, 1]
features = {
    "has German\ntranslation": ("has_german", True),
    "has variant\nspellings": ("has_variants", True),
    "has scholarly\nnotes": ("n_notes", lambda x: x > 0),
    "has explicit\ndefinition": ("has_def", True),
    "cites\nauthorities": ("has_authorities", True),
    "has phrase\nheadword": ("has_phrase", True),
}
feat_names = list(features.keys())
ar_rates = []
nonar_rates = []
for feat_name, (col, cond) in features.items():
    if cond is True:
        ar_rates.append(xml_df[xml_df["has_arabic"]][col].mean() * 100)
        nonar_rates.append(xml_df[~xml_df["has_arabic"]][col].mean() * 100)
    else:
        ar_rates.append(xml_df[xml_df["has_arabic"]][col].apply(cond).mean() * 100)
        nonar_rates.append(xml_df[~xml_df["has_arabic"]][col].apply(cond).mean() * 100)

y_f = np.arange(len(feat_names))
ax.barh(y_f - 0.15, ar_rates, 0.3, label="Arabic entries", color=PAL["orange"])
ax.barh(y_f + 0.15, nonar_rates, 0.3, label="Non-Arabic entries", color=PAL["blue"])
ax.set_yticks(y_f)
ax.set_yticklabels(feat_names, fontsize=10)
ax.set_xlabel("% of entries with feature")
ax.set_title("Structural Feature Rates:\nArabic vs Non-Arabic", fontsize=12)
ax.legend(fontsize=9)

# Panel 3: complexity by letter section
ax = axes[1, 0]
letter_complexity = xml_df.groupby("first_letter").agg(
    mean_complexity=("complexity", "mean"),
    mean_complexity_arabic=("complexity", lambda x: x[xml_df.loc[x.index, "has_arabic"]].mean()
                            if xml_df.loc[x.index, "has_arabic"].any() else np.nan),
).reindex(letters_order)
# Separate calculation for Arabic entries
ar_complexity_by_letter = xml_df[xml_df["has_arabic"]].groupby("first_letter")["complexity"].mean()

x = np.arange(len(letters_order))
ax.bar(x - 0.175, letter_complexity["mean_complexity"], 0.35,
       label="all entries", color=PAL["blue"], alpha=0.7)
ar_vals = ar_complexity_by_letter.reindex(letters_order).fillna(0)
ax.bar(x + 0.175, ar_vals, 0.35,
       label="Arabic entries", color=PAL["orange"], alpha=0.7)
ax.set_xticks(x)
ax.set_xticklabels(letters_order, fontsize=8)
ax.set_ylabel("mean complexity score")
ax.set_title("Entry Complexity by Letter Section", fontsize=12)
ax.legend(fontsize=9)

# Panel 4: most complex Arabic entries
ax = axes[1, 1]
ax.axis("off")
top_complex = xml_df[xml_df["has_arabic"]].nlargest(15, "complexity")
text = "Most Structurally Complex Arabic Entries\n"
text += "═" * 55 + "\n\n"
text += f"{'Entry':22s} {'Score':5s} {'Features'}\n"
text += "─" * 55 + "\n"
for _, row in top_complex.iterrows():
    feats = []
    if row["has_german"]: feats.append("DE")
    if row["has_variants"]: feats.append("var")
    if row["n_notes"] > 0: feats.append("note")
    if row["has_def"]: feats.append("def")
    if row["has_authorities"]: feats.append("auth")
    if row["has_phrase"]: feats.append("phr")
    text += f'{row["headword"][:22]:22s} {row["complexity"]:5.0f}   {", ".join(feats)}\n'
ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9.5,
        va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title("Top 15 Most Complex Arabic Entries", fontsize=12)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "entry_complexity.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ entry_complexity.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 6: PAGE-LEVEL DISTRIBUTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 6: Page-level distribution…")

fig, axes = plt.subplots(3, 1, figsize=(20, 14), sharex=True)

# Group by page
page_stats = xml_df.groupby("page").agg(
    n_entries=("headword", "count"),
    n_arabic=("has_arabic", "sum"),
    mean_wc=("word_count", "mean"),
    has_german=("has_german", "sum"),
).reset_index()
page_stats["arabic_pct"] = 100 * page_stats["n_arabic"] / page_stats["n_entries"]
page_stats["german_pct"] = 100 * page_stats["has_german"] / page_stats["n_entries"]

# Panel 1: entries per page with Arabic overlay
ax = axes[0]
ax.bar(page_stats["page"], page_stats["n_entries"], color=PAL["lightblue"],
       width=1.0, label="total entries")
ax.bar(page_stats["page"], page_stats["n_arabic"], color=PAL["orange"],
       width=1.0, label="Arabic entries", alpha=0.8)
ax.set_ylabel("entries per page")
ax.set_title("Page-by-Page View of Ruland's Dictionary\n"
             "(each bar = one printed page)", fontsize=13)
ax.legend(fontsize=9)

# Panel 2: Arabic density per page (rolling)
ax = axes[1]
window_p = 10
rolling_ar = page_stats["arabic_pct"].rolling(window_p, center=True, min_periods=1).mean()
ax.fill_between(page_stats["page"], rolling_ar, alpha=0.5, color=PAL["orange"])
ax.plot(page_stats["page"], rolling_ar, color=PAL["darkorange"], linewidth=1.5)
ax.set_ylabel(f"Arabic density (%)\n({window_p}-page rolling avg)")
ax.set_title("Arabic Term Density Across the Physical Pages", fontsize=12)

# Panel 3: German translation density per page
ax = axes[2]
rolling_de = page_stats["german_pct"].rolling(window_p, center=True, min_periods=1).mean()
ax.fill_between(page_stats["page"], rolling_de, alpha=0.5, color=PAL["teal"])
ax.plot(page_stats["page"], rolling_de, color=PAL["darkgreen"], linewidth=1.5)
ax.set_ylabel(f"German translation\ndensity (%)")
ax.set_xlabel("page number in original printed edition", fontsize=11)
ax.set_title("German Translation Density Across the Physical Pages", fontsize=12)

# Add letter section markers to all panels
# Find page ranges per letter
letter_pages = xml_df.groupby("entry_type")["page"].agg(["min", "max"])
for axi in axes:
    for letter, row in letter_pages.iterrows():
        if letter and len(letter) == 1:
            mid = (row["min"] + row["max"]) / 2
            axi.axvline(row["min"], color="gray", alpha=0.15, linewidth=0.5)
            if axi == axes[0]:
                axi.text(mid, axi.get_ylim()[1] * 0.95, letter, fontsize=8,
                         ha="center", fontweight="bold", color=PAL["darkblue"])

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "page_distribution.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ page_distribution.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 7: NOTES ANALYSIS — WHAT DO THE XML NOTES SAY?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 7: XML notes analysis…")

noted_entries = xml_df[xml_df["n_notes"] > 0].copy()

fig, axes = plt.subplots(1, 3, figsize=(22, 9))

# Panel 1: notes by letter section
ax = axes[0]
notes_by_letter = xml_df.groupby("first_letter")["n_notes"].sum().reindex(letters_order).fillna(0)
entries_by_letter = xml_df.groupby("first_letter").size().reindex(letters_order).fillna(0)
notes_rate = (100 * notes_by_letter / entries_by_letter).fillna(0)

x = np.arange(len(letters_order))
ax.bar(x, notes_by_letter, color=PAL["purple"])
ax.set_xticks(x)
ax.set_xticklabels(letters_order, fontsize=8)
ax.set_ylabel("number of note elements")
ax.set_title("XML Notes by Letter Section", fontsize=12)
# Add note rate
ax2 = ax.twinx()
ax2.plot(x, notes_rate, color=PAL["red"], marker="o", markersize=4, linewidth=1.5)
ax2.set_ylabel("notes per 100 entries (red line)", fontsize=9, color=PAL["red"])
ax2.tick_params(axis="y", labelcolor=PAL["red"])

# Panel 2: notes in Arabic vs non-Arabic entries
ax = axes[1]
ar_note_rate = xml_df[xml_df["has_arabic"]]["n_notes"].mean()
nonar_note_rate = xml_df[~xml_df["has_arabic"]]["n_notes"].mean()
bars = ax.bar(["Arabic-origin\nentries", "Non-Arabic\nentries"],
              [ar_note_rate, nonar_note_rate],
              color=[PAL["orange"], PAL["blue"]], width=0.4)
ax.set_ylabel("mean notes per entry")
ax.set_title("Scholarly Notes: Arabic vs Non-Arabic", fontsize=12)
for bar, val in zip(bars, [ar_note_rate, nonar_note_rate]):
    ax.text(bar.get_x() + bar.get_width()/2, val + 0.01,
            f"{val:.2f}", ha="center", fontsize=11)

# Panel 3: most heavily annotated entries
ax = axes[2]
top_noted = xml_df.nlargest(20, "n_notes")
y = np.arange(len(top_noted))
colors_tn = [PAL["orange"] if ha else PAL["blue"] for ha in top_noted["has_arabic"]]
ax.barh(y, top_noted["n_notes"], color=colors_tn)
ax.set_yticks(y)
ax.set_yticklabels(top_noted["headword"], fontsize=9)
ax.invert_yaxis()
ax.set_xlabel("number of note elements")
ax.set_title("Most Annotated Entries\n(orange = Arabic, blue = non-Arabic)", fontsize=12)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "xml_notes_analysis.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ xml_notes_analysis.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 8: GERMAN TRANSLATION CONTENT — WHAT'S IN THE GERMAN TEXT?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 8: German translation content…")

# Re-parse to get actual German text for Arabic entries
arabic_german_entries = []
for entry in root.iter(f"{ns}entry"):
    form_el = entry.find(f".//{ns}form[@type='lemma']")
    hw = form_el.text.strip() if form_el is not None and form_el.text else ""
    if hw not in arabic_lemmas:
        continue
    cit_de = entry.findall(f".//{ns}cit[@{xml_ns}lang='de']")
    de_texts = []
    for c in cit_de:
        quote = c.find(f"{ns}quote")
        if quote is not None:
            qt = "".join(quote.itertext()).strip()
            if qt:
                de_texts.append(qt)
    if de_texts:
        arabic_german_entries.append({
            "headword": hw,
            "german_text": " ".join(de_texts),
            "german_word_count": sum(len(t.split()) for t in de_texts),
        })

de_df = pd.DataFrame(arabic_german_entries)

fig, axes = plt.subplots(1, 2, figsize=(20, 10))

# Left: word cloud substitute — most common German words in Arabic entries
ax = axes[0]
# Count German words
german_words = Counter()
stop_de = {"der", "die", "das", "und", "ist", "ein", "eine", "von", "zu",
           "den", "des", "dem", "in", "mit", "auf", "es", "oder", "vnd",
           "auch", "so", "als", "wie", "wird", "nicht", "sich", "er",
           "sie", "aber", "hat", "man", "noch", "wann", "da", "nach",
           "ond", "denn", "was", "werden", "kan", "sein", "einer",
           "einem", "einen", "eines", "ander", "andere", "anderen",
           "soll", "kan", "wenn"}
for text in de_df["german_text"]:
    for word in text.split():
        w = word.strip(".,;:!?()\"'").lower()
        if len(w) > 2 and w not in stop_de and w.isalpha():
            german_words[w] += 1

top_words = pd.Series(dict(german_words.most_common(35)))
ax.barh(range(len(top_words)), top_words.values, color=PAL["teal"])
ax.set_yticks(range(len(top_words)))
ax.set_yticklabels(top_words.index, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel("frequency")
ax.set_title("Most Frequent German Words in\nArabic-Origin Entry Translations\n(stop words removed)",
             fontsize=12)

# Right: sample German translations for key Arabic terms
ax = axes[1]
ax.axis("off")
key_terms = ["Alkali", "Borax", "Elixir", "Alcohol", "Naphtha", "Mumia",
             "Colcotar", "Realgar", "Athanor", "Alumen"]
text = "German Translations for Key Arabic Terms\n"
text += "═" * 60 + "\n\n"
for term in key_terms:
    matches = de_df[de_df["headword"].str.lower() == term.lower()]
    if len(matches) > 0:
        de_text = matches.iloc[0]["german_text"][:120]
        if len(matches.iloc[0]["german_text"]) > 120:
            de_text += "…"
        wrapped = textwrap.fill(de_text, width=55)
        text += f"▸ {term}\n  {wrapped}\n\n"

ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9,
        va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title("German Translations for Arabic Terms", fontsize=12)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "german_content.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ german_content.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 9: CROSS-TRADITION SYNTHESIS — ARABIC TERMS IN MULTILINGUAL CONTEXT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 9: Cross-tradition synthesis…")

fig, axes = plt.subplots(2, 2, figsize=(18, 14))

# Panel 1: multilingual richness score
# How many "layers" does each entry have?
xml_df["multilingual_score"] = (
    xml_df["has_german"].astype(int) * 2 +  # German is major
    xml_df["has_arabic"].astype(int) * 2 +  # Arabic is major
    xml_df["has_authorities"].astype(int) +
    xml_df["has_variants"].astype(int) +
    (xml_df["n_notes"] > 0).astype(int)
)

ax = axes[0, 0]
bins_m = np.arange(-0.5, xml_df["multilingual_score"].max() + 1.5, 1)
ax.hist(xml_df[xml_df["has_arabic"]]["multilingual_score"], bins=bins_m, alpha=0.6,
        color=PAL["orange"], label="Arabic entries", density=True)
ax.hist(xml_df[~xml_df["has_arabic"]]["multilingual_score"], bins=bins_m, alpha=0.6,
        color=PAL["blue"], label="Non-Arabic entries", density=True)
ax.set_xlabel("multilingual richness score")
ax.set_ylabel("density")
ax.set_title("Multilingual Richness:\nArabic vs Non-Arabic Entries", fontsize=12)
ax.legend(fontsize=9)

# Panel 2: entries with all three traditions (Arabic + German + authority)
ax = axes[0, 1]
triple = xml_df[(xml_df["has_arabic"]) & (xml_df["has_german"]) & (xml_df["has_authorities"])]
double_ag = xml_df[(xml_df["has_arabic"]) & (xml_df["has_german"]) & (~xml_df["has_authorities"])]
double_aa = xml_df[(xml_df["has_arabic"]) & (~xml_df["has_german"]) & (xml_df["has_authorities"])]
arabic_only = xml_df[(xml_df["has_arabic"]) & (~xml_df["has_german"]) & (~xml_df["has_authorities"])]

venn_data = {
    "Arabic + German\n+ authorities": len(triple),
    "Arabic + German\nonly": len(double_ag),
    "Arabic + authorities\nonly": len(double_aa),
    "Arabic only\n(no German, no auth.)": len(arabic_only),
}
colors_venn = [PAL["gold"], PAL["teal"], PAL["purple"], PAL["lightblue"]]
ax.pie(venn_data.values(), labels=[f"{k}\n({v})" for k, v in venn_data.items()],
       colors=colors_venn, autopct="%1.1f%%", startangle=90,
       textprops={"fontsize": 9})
ax.set_title("Arabic Entries: Which Also Have\nGerman and/or Authority Citations?", fontsize=12)

# Panel 3: timeline of multilingual density
ax = axes[1, 0]
window_ml = 50
rolling_de = pd.Series(xml_df["has_german"].astype(float)).rolling(window_ml, center=True).mean() * 100
rolling_ar = pd.Series(xml_df["has_arabic"].astype(float)).rolling(window_ml, center=True).mean() * 100
rolling_auth = pd.Series(xml_df["has_authorities"].astype(float)).rolling(window_ml, center=True).mean() * 100

ax.fill_between(range(len(xml_df)), rolling_de, alpha=0.3, color=PAL["teal"], label="German translations")
ax.fill_between(range(len(xml_df)), rolling_ar, alpha=0.4, color=PAL["orange"], label="Arabic terms")
ax.fill_between(range(len(xml_df)), rolling_auth, alpha=0.3, color=PAL["purple"], label="Authority citations")
ax.plot(range(len(xml_df)), rolling_de, color=PAL["darkgreen"], linewidth=1)
ax.plot(range(len(xml_df)), rolling_ar, color=PAL["darkorange"], linewidth=1)
ax.plot(range(len(xml_df)), rolling_auth, color=PAL["purple"], linewidth=1)
ax.set_xlabel("sequential position in dictionary")
ax.set_ylabel(f"density (% in {window_ml}-entry window)")
ax.set_title("Three Layers of the Dictionary: Arabic, German, Authorities\n(50-entry rolling average)",
             fontsize=12)
ax.legend(fontsize=9, loc="upper right")
ax.set_xlim(0, len(xml_df))

# Letter markers
letter_first = xml_df.groupby("first_letter")["seq_idx"].min()
for letter, pos in letter_first.items():
    ax.axvline(pos, color="gray", alpha=0.1, linewidth=0.5)

# Panel 4: correlation between layers
ax = axes[1, 1]
# Per letter section: Arabic rate vs German rate vs authority rate
letter_rates = xml_df.groupby("first_letter").agg(
    arabic_rate=("has_arabic", "mean"),
    german_rate=("has_german", "mean"),
    authority_rate=("has_authorities", "mean"),
    n_entries=("headword", "count"),
).reindex(letters_order).dropna()

# Scatter: Arabic rate vs German rate, sized by entries
for _, row in letter_rates.iterrows():
    letter = row.name
    ax.scatter(row["arabic_rate"] * 100, row["german_rate"] * 100,
               s=row["n_entries"] * 0.8, alpha=0.6,
               color=PAL["orange"], edgecolors=PAL["darkorange"])
    ax.annotate(letter, (row["arabic_rate"] * 100, row["german_rate"] * 100),
                fontsize=10, fontweight="bold", ha="center", va="center")

ax.set_xlabel("Arabic term rate (%)")
ax.set_ylabel("German translation rate (%)")
ax.set_title("Letter Sections: Arabic Rate vs German Rate\n(bubble size = number of entries)",
             fontsize=12)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "cross_tradition.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ cross_tradition.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 10: ABBREVIATIONS AND SPECIAL MARKUP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 10: Abbreviations and special markup…")

# Parse abbreviation expansions
abbrevs = []
for entry in root.iter(f"{ns}entry"):
    form_el = entry.find(f".//{ns}form[@type='lemma']")
    hw = form_el.text.strip() if form_el is not None and form_el.text else ""
    for choice in entry.findall(f".//{ns}choice"):
        abbr = choice.find(f"{ns}abbr")
        expan = choice.find(f"{ns}expan")
        if abbr is not None and expan is not None:
            at = "".join(abbr.itertext()).strip()
            et = "".join(expan.itertext()).strip()
            abbrevs.append({"headword": hw, "abbr": at, "expansion": et,
                           "has_arabic": hw in arabic_lemmas})

abbr_df = pd.DataFrame(abbrevs) if abbrevs else pd.DataFrame(columns=["headword", "abbr", "expansion", "has_arabic"])

# Greek segments
greek_segs = []
for entry in root.iter(f"{ns}entry"):
    form_el = entry.find(f".//{ns}form[@type='lemma']")
    hw = form_el.text.strip() if form_el is not None and form_el.text else ""
    for seg in entry.findall(f".//{ns}seg[@type='greek']"):
        st = "".join(seg.itertext()).strip()
        greek_segs.append({"headword": hw, "greek_text": st,
                          "has_arabic": hw in arabic_lemmas})
greek_df = pd.DataFrame(greek_segs) if greek_segs else pd.DataFrame(columns=["headword", "greek_text", "has_arabic"])

fig, axes = plt.subplots(2, 2, figsize=(18, 12))

# Panel 1: abbreviation overview
ax = axes[0, 0]
if len(abbr_df) > 0:
    abbr_counts = abbr_df["expansion"].value_counts().head(15)
    ax.barh(range(len(abbr_counts)), abbr_counts.values, color=PAL["purple"])
    ax.set_yticks(range(len(abbr_counts)))
    ax.set_yticklabels(abbr_counts.index, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("count")
    ax.set_title(f"Abbreviation Expansions in XML\n({len(abbr_df)} total)", fontsize=12)
else:
    ax.text(0.5, 0.5, f"No abbreviation elements found\n(or {len(abbrevs)} found)",
            ha="center", va="center", transform=ax.transAxes)
    ax.set_title("Abbreviation Expansions", fontsize=12)

# Panel 2: special markup summary
ax = axes[0, 1]
markup_summary = {
    "Entries with <note>": (xml_df["n_notes"] > 0).sum(),
    "Entries with <def>": xml_df["has_def"].sum(),
    "Entries with variant forms": xml_df["has_variants"].sum(),
    "Entries with phrase heads": xml_df["has_phrase"].sum(),
    "German translations (cit@de)": xml_df["has_german"].sum(),
    "Fraktur-marked text": (xml_df["fraktur_word_count"] > 0).sum(),
    "Authority citations": xml_df["has_authorities"].sum(),
    "Abbreviation expansions": len(abbr_df),
    "Greek text segments": len(greek_df),
}
ms = pd.Series(markup_summary).sort_values(ascending=True)
colors_ms = [PAL["orange"] if "Arabic" in k else PAL["blue"] for k in ms.index]
ax.barh(range(len(ms)), ms.values, color=PAL["teal"])
ax.set_yticks(range(len(ms)))
ax.set_yticklabels(ms.index, fontsize=10)
ax.set_xlabel("count")
ax.set_title("XML Annotation Summary\n(structural features in the TEI encoding)", fontsize=12)
for i, v in enumerate(ms.values):
    ax.text(v + 5, i, str(v), va="center", fontsize=9)

# Panel 3: entries per page distribution
ax = axes[1, 0]
entries_per_page = xml_df.groupby("page").size()
ax.hist(entries_per_page, bins=30, color=PAL["blue"], edgecolor="white")
ax.set_xlabel("entries per page")
ax.set_ylabel("number of pages")
ax.set_title("Dictionary Density: Entries Per Printed Page", fontsize=12)
ax.axvline(entries_per_page.mean(), color=PAL["red"], ls="--",
           label=f"mean = {entries_per_page.mean():.1f}")
ax.axvline(entries_per_page.median(), color=PAL["orange"], ls="--",
           label=f"median = {entries_per_page.median():.1f}")
ax.legend(fontsize=9)

# Panel 4: page count and physical structure
ax = axes[1, 1]
total_pages = xml_df["page"].max() - xml_df["page"].min() + 1
letter_page_ranges = xml_df.groupby("entry_type").agg(
    first_page=("page", "min"),
    last_page=("page", "max"),
    n_entries=("headword", "count"),
).sort_values("first_page")
letter_page_ranges = letter_page_ranges[letter_page_ranges.index.str.len() == 1]
letter_page_ranges["page_span"] = letter_page_ranges["last_page"] - letter_page_ranges["first_page"] + 1

y_l = np.arange(len(letter_page_ranges))
ax.barh(y_l, letter_page_ranges["page_span"], color=PAL["blue"], alpha=0.7)
ax.set_yticks(y_l)
ax.set_yticklabels(letter_page_ranges.index, fontsize=9)
ax.set_xlabel("number of pages")
ax.set_title(f"Physical Size of Each Letter Section\n(total: {total_pages} pages)", fontsize=12)
for i, (_, row) in enumerate(letter_page_ranges.iterrows()):
    ax.text(row["page_span"] + 0.5, i,
            f'pp. {int(row["first_page"])}–{int(row["last_page"])}',
            va="center", fontsize=7.5)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "special_markup.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ special_markup.png")


print(f"\nAll done. {len(os.listdir(OUTDIR))} files in {OUTDIR}")
for f in sorted(os.listdir(OUTDIR)):
    print(f"  {f}")
