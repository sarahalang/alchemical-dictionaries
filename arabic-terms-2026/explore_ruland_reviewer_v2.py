#!/usr/bin/env python3
"""
Ruland 1612 – Detection Quality & Reviewer Analysis (v2)
=========================================================
Corrected interpretation: the TSV contains automatically detected
terms that were reviewed by 3 humans. The Etymology field indicates
what the reviewer thinks the ACTUAL origin is — when it's not
"Arabic", the detection was partially or fully incorrect.

The 363 terms in the TSV survived inclusion; the original pipeline
produced 928 detections, meaning 565 (60.9%) were excluded.

This analysis examines:
1. Detection pipeline quality (what was kept, what was excluded, why)
2. Characteristics of the included terms (etymology, confidence,
   notes, external validation)
3. Edge cases and misclassifications
4. What this tells us about Ruland's dictionary
"""

import os, re, textwrap
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import seaborn as sns
from collections import Counter

# ── paths ───────────────────────────────────────────────────────────
TSV_PATH = "/Users/slang/Downloads/Final Single Sheet - 2026-01-27_reviewerCopy_reducedFinalSingleSheet.tsv"
CSV_RAW = "/Users/slang/Downloads/schreibProjekte-slides/narrowingdown/output_4ofixed_reviewed_with_entries.csv"
OUTDIR = "/Users/slang/claude/ruland_exploration/06_reviewer_analysis"
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

# Reviewed / included terms
df = pd.read_csv(TSV_PATH, sep="\t")
df = df.rename(columns={
    "lemma /headword": "lemma",
    "3 human reviewer comparison verdict": "verdict",
    "Include (controled vocab, y/n)": "include",
    "normalized control string (harmonized) ": "norm_control",
})

# Original pipeline output (pre-review)
raw_df = pd.read_csv(CSV_RAW)
raw_df = raw_df.loc[:, ~raw_df.columns.str.startswith("Unnamed")]
for col in ["confidence_score", "irrelevance_probability"]:
    if col in raw_df.columns:
        raw_df[col] = pd.to_numeric(raw_df[col], errors="coerce")

# Normalize
df["verdict_clean"] = df["verdict"].str.strip().str.upper()
df["etymology_clean"] = df["Etymology"].fillna("not reviewed").str.strip()
# Normalize casing
etym_map = {
    "Arabic": "Arabic", "arabic": "Arabic",
    "Latinised Arabic": "Latinised Arabic",
    "Persian-Arabic": "Persian-Arabic",
    "Persian": "Persian",
    "unclear": "unclear", "mixed": "mixed",
    "not reviewed": "not reviewed",
}
df["etymology_clean"] = df["etymology_clean"].map(
    lambda x: etym_map.get(x, "other/specific"))

# Convert numeric columns from string to float
for col in ["confidence_score", "irrelevance_probability"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df["first_letter"] = df["lemma"].dropna().str.strip().str[0].str.upper()

# Wiki/EMLAP normalization
df["wiki_clean"] = df["wiki_match_flag"].astype(str).str.strip().str.lower()
df.loc[~df["wiki_clean"].isin(["yes", "no", "maybe"]), "wiki_clean"] = "other"
df["emlap_clean"] = df["emlap_match_flag"].astype(str).str.strip().str.lower()
df.loc[~df["emlap_clean"].isin(["yes_corpus", "no"]), "emlap_clean"] = "other"

print(f"  Reviewed (included): {len(df)} terms")
print(f"  Original pipeline: {len(raw_df)} detections")
print(f"  Excluded by review: {len(raw_df) - len(df)} ({100*(len(raw_df)-len(df))/len(raw_df):.1f}%)")

# Assign detection quality categories
def quality_category(row):
    e = row["etymology_clean"]
    if e == "Arabic":
        return "correctly detected\n(Arabic)"
    elif e == "Latinised Arabic":
        return "correctly detected\n(Latinised Arabic)"
    elif e in ["Persian-Arabic", "Persian"]:
        return "related tradition\n(Persian/Persian-Arabic)"
    elif e in ["mixed", "unclear"]:
        return "ambiguous\n(mixed/unclear origin)"
    elif e == "not reviewed":
        return "not yet classified"
    else:
        return "other/specific"

df["quality_cat"] = df.apply(quality_category, axis=1)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 1: DETECTION PIPELINE FUNNEL
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 1: Detection pipeline funnel…")

fig, axes = plt.subplots(1, 3, figsize=(22, 8))

# Panel 1: funnel from 928 → 363
ax = axes[0]
stages = ["AI detections\n(raw pipeline)", "After irrelevance\nfiltering (≤0.3)",
          "After human\nreview (included)"]
# Estimate the intermediate stage from the raw CSV
irr = raw_df["irrelevance_probability"]
n_after_irr = (irr.dropna() <= 0.3).sum() + irr.isna().sum()  # kept if ≤0.3 or missing
counts = [len(raw_df), n_after_irr, len(df)]
colors_f = [PAL["lightblue"], PAL["teal"], PAL["green"]]
bars = ax.barh(range(len(stages)), counts, color=colors_f, height=0.5)
ax.set_yticks(range(len(stages)))
ax.set_yticklabels(stages, fontsize=11)
ax.set_xlabel("number of detected terms")
ax.set_title("Detection Pipeline Funnel\n(from AI output to human-reviewed dataset)", fontsize=12)
ax.invert_yaxis()
for i, (bar, c) in enumerate(zip(bars, counts)):
    pct = 100 * c / len(raw_df)
    ax.text(c + 5, i, f"{c} ({pct:.0f}%)", va="center", fontsize=11, fontweight="bold")

# Panel 2: what was the detection accuracy?
ax = axes[1]
cat_counts = df["quality_cat"].value_counts()
cat_colors = {
    "correctly detected\n(Arabic)": PAL["green"],
    "correctly detected\n(Latinised Arabic)": PAL["teal"],
    "related tradition\n(Persian/Persian-Arabic)": PAL["purple"],
    "ambiguous\n(mixed/unclear origin)": PAL["orange"],
    "not yet classified": PAL["lightblue"],
    "other/specific": PAL["gray"],
}
colors_cat = [cat_colors.get(c, PAL["gray"]) for c in cat_counts.index]
ax.barh(range(len(cat_counts)), cat_counts.values, color=colors_cat)
ax.set_yticks(range(len(cat_counts)))
ax.set_yticklabels(cat_counts.index, fontsize=10)
ax.set_xlabel("number of terms")
ax.set_title("Detection Accuracy\n(among 363 included terms)", fontsize=12)
for i, v in enumerate(cat_counts.values):
    ax.text(v + 1, i, f"{v} ({100*v/len(df):.1f}%)", va="center", fontsize=9)

# Panel 3: summary
ax = axes[2]
ax.axis("off")
n_correct = (df["etymology_clean"].isin(["Arabic", "Latinised Arabic"])).sum()
n_related = (df["etymology_clean"].isin(["Persian-Arabic", "Persian"])).sum()
n_ambig = (df["etymology_clean"].isin(["mixed", "unclear"])).sum()
n_unrev = (df["etymology_clean"] == "not reviewed").sum()
n_other = len(df) - n_correct - n_related - n_ambig - n_unrev

text = f"""Detection Quality Summary
{'═' * 45}

Pipeline: 928 AI detections → 363 reviewed & included
Rejection rate: 60.9% of original detections excluded

Of the 363 included terms:

  Correctly Arabic:        {n_correct:3d}  ({100*n_correct/len(df):.1f}%)
    (Arabic + Latinised Arabic)

  Related tradition:        {n_related:3d}  ({100*n_related/len(df):.1f}%)
    (Persian, Persian-Arabic)

  Ambiguous/debated:        {n_ambig:3d}  ({100*n_ambig/len(df):.1f}%)
    (mixed or unclear origins)

  Not yet classified:       {n_unrev:3d}  ({100*n_unrev/len(df):.1f}%)
    (included but no etymology assigned)

  Other/specific:           {n_other:3d}  ({100*n_other/len(df):.1f}%)

Reviewer agreement:
  ARABIC verdict:          {(df['verdict_clean']=='ARABIC').sum():3d}  ({100*(df['verdict_clean']=='ARABIC').sum()/len(df):.1f}%)
  UNCERTAIN verdict:        {(df['verdict_clean']=='UNCERTAIN').sum():3d}  ({100*(df['verdict_clean']=='UNCERTAIN').sum()/len(df):.1f}%)
"""
ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9.5,
        va="top", fontfamily="monospace", linespacing=1.4)
ax.set_title("Summary", fontsize=12)

plt.suptitle("Detection Pipeline Quality: From AI Extraction to Human-Reviewed Arabic Terms",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "detection_funnel.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ detection_funnel.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 2: WHAT MAKES A DETECTION CORRECT OR AMBIGUOUS?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 2: Detection accuracy by features…")

fig, axes = plt.subplots(2, 2, figsize=(18, 14))

# Panel 1: confidence score by detection quality
ax = axes[0, 0]
qual_order = ["correctly detected\n(Arabic)", "correctly detected\n(Latinised Arabic)",
              "related tradition\n(Persian/Persian-Arabic)",
              "ambiguous\n(mixed/unclear origin)", "not yet classified"]
qual_order = [q for q in qual_order if q in df["quality_cat"].values]
plot_df = df[df["quality_cat"].isin(qual_order)].copy()
# Use simple bar chart of mean confidence
mean_conf = plot_df.groupby("quality_cat")["confidence_score"].mean().reindex(qual_order)
colors_q = [cat_colors.get(q, PAL["gray"]) for q in qual_order]
ax.barh(range(len(mean_conf)), mean_conf.values, color=colors_q, height=0.5)
ax.set_yticks(range(len(mean_conf)))
ax.set_yticklabels(qual_order, fontsize=10)
ax.set_xlabel("mean AI confidence score")
ax.set_title("AI Confidence by Actual Etymology\n(Does the AI 'know' when it's wrong?)", fontsize=12)
for i, v in enumerate(mean_conf.values):
    ax.text(v + 0.005, i, f"{v:.3f}", va="center", fontsize=10)

# Panel 2: irrelevance probability by detection quality
ax = axes[0, 1]
irr_vals = df.groupby("quality_cat")["irrelevance_probability"].mean().reindex(qual_order)
ax.barh(range(len(irr_vals)), irr_vals.values, color=colors_q, height=0.5)
ax.set_yticks(range(len(irr_vals)))
ax.set_yticklabels(qual_order, fontsize=10)
ax.set_xlabel("mean irrelevance probability")
ax.set_title("AI Irrelevance Score by Actual Etymology\n(Higher = AI thought it was less relevant)", fontsize=12)
for i, v in enumerate(irr_vals.values):
    if pd.notna(v):
        ax.text(v + 0.002, i, f"{v:.3f}", va="center", fontsize=10)

# Panel 3: which terms did the detector get "wrong"?
ax = axes[1, 0]
non_arabic = df[df["etymology_clean"].isin(["Persian", "Persian-Arabic", "mixed", "unclear"])].copy()
term_counts = non_arabic["norm_control"].value_counts()
y = np.arange(len(term_counts))
etym_of_term = non_arabic.groupby("norm_control")["etymology_clean"].first()
colors_na = [cat_colors.get(quality_category(non_arabic[non_arabic["norm_control"]==t].iloc[0]), PAL["gray"])
             for t in term_counts.index]
ax.barh(y, term_counts.values, color=colors_na)
ax.set_yticks(y)
labels_na = []
for term in term_counts.index:
    etym = etym_of_term.get(term, "")
    labels_na.append(f"{term}  [{etym}]")
ax.set_yticklabels(labels_na, fontsize=8.5)
ax.invert_yaxis()
ax.set_xlabel("count")
ax.set_title("Non-Arabic Terms Included Despite Misclassification\n(detected as Arabic but actually...)", fontsize=12)

# Panel 4: Wiktionary/EMLAP validation by quality category
ax = axes[1, 1]
wiki_by_cat = df.groupby("quality_cat").apply(
    lambda g: 100 * (g["wiki_clean"] == "yes").sum() / len(g)).reindex(qual_order)
emlap_by_cat = df.groupby("quality_cat").apply(
    lambda g: 100 * (g["emlap_clean"] == "yes_corpus").sum() / len(g)).reindex(qual_order)

y_v = np.arange(len(qual_order))
ax.barh(y_v - 0.15, wiki_by_cat.values, 0.3, label="Wiktionary match",
        color=PAL["orange"])
ax.barh(y_v + 0.15, emlap_by_cat.values, 0.3, label="EMLAP corpus match",
        color=PAL["teal"])
ax.set_yticks(y_v)
ax.set_yticklabels(qual_order, fontsize=10)
ax.set_xlabel("% of terms with external match")
ax.set_title("External Validation by Detection Quality\n(Do correctly detected terms validate better?)", fontsize=12)
ax.legend(fontsize=9)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "detection_accuracy.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ detection_accuracy.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 3: REVIEWER NOTES — WHAT HUMAN EXPERTS DOCUMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 3: Reviewer notes…")

notes_df = df[df["notes"].notna()].copy()

# Categorize notes by what they tell us about detection quality
def categorize_note_v2(note):
    n = str(note).lower()
    if "debated" in n or "unclear" in n or "origins" in n:
        return "flags debated etymology"
    if "from al-" in n or "al-" in n:
        return "documents Arabic source (al-)"
    if "from " in n and ("arabic" in n or "persian" in n or "mumiya" in n or "iksir" in n):
        return "documents Arabic/Persian source"
    if "personal name" in n or "avicenna" in n or "author" in n:
        return "flags personal name (edge case)"
    if "latin" in n and ("related" in n or "potentially" in n or "but" in n):
        return "notes Latin confusion risk"
    if "greek" in n or "egyptian" in n:
        return "notes Greek/Egyptian alternative"
    if "lemmatiz" in n or "badly" in n:
        return "flags data quality issue"
    if "paracels" in n or "pseudo" in n:
        return "flags Pseudo-Arabic"
    if "edge case" in n or "kind of" in n or "probably" in n or "likely" in n:
        return "hedged/uncertain judgment"
    return "specific etymology note"

notes_df["note_type"] = notes_df["notes"].apply(categorize_note_v2)

fig, axes = plt.subplots(1, 3, figsize=(22, 9))

# Panel 1: note categories
ax = axes[0]
cat_counts = notes_df["note_type"].value_counts()
cat_colors_n = [PAL["blue"], PAL["green"], PAL["teal"], PAL["orange"],
                PAL["purple"], PAL["red"], PAL["brown"], PAL["pink"],
                PAL["gray"], PAL["darkblue"]][:len(cat_counts)]
ax.barh(range(len(cat_counts)), cat_counts.values, color=cat_colors_n)
ax.set_yticks(range(len(cat_counts)))
ax.set_yticklabels(cat_counts.index, fontsize=10)
ax.set_xlabel("number of notes")
ax.set_title("What Reviewers Documented\n(note categories by function)", fontsize=12)
for i, v in enumerate(cat_counts.values):
    ax.text(v + 0.5, i, str(v), va="center", fontsize=9)

# Panel 2: most common specific notes
ax = axes[1]
note_counts = notes_df["notes"].value_counts().head(18)
y = np.arange(len(note_counts))
# Color by whether note flags a problem or confirms Arabic
note_colors = []
for note in note_counts.index:
    n = str(note).lower()
    if "debated" in n or "unclear" in n or "latin" in n or "greek" in n or "edge" in n:
        note_colors.append(PAL["orange"])
    else:
        note_colors.append(PAL["green"])
ax.barh(y, note_counts.values, color=note_colors)
ax.set_yticks(y)
labels_n = [textwrap.fill(str(n), width=50)[:90] for n in note_counts.index]
ax.set_yticklabels(labels_n, fontsize=7)
ax.invert_yaxis()
ax.set_xlabel("count")
ax.set_title("Most Common Reviewer Notes\n(green = confirms Arabic; orange = flags issue)", fontsize=12)

# Panel 3: notes vs detection quality
ax = axes[2]
# What % of each quality category has notes?
note_rate_by_cat = df.groupby("quality_cat").apply(
    lambda g: 100 * g["notes"].notna().sum() / len(g)
).reindex(qual_order)
colors_nr = [cat_colors.get(q, PAL["gray"]) for q in qual_order]
ax.barh(range(len(note_rate_by_cat)), note_rate_by_cat.values, color=colors_nr, height=0.5)
ax.set_yticks(range(len(note_rate_by_cat)))
ax.set_yticklabels(qual_order, fontsize=10)
ax.set_xlabel("% of terms with reviewer notes")
ax.set_title("Note Coverage by Detection Quality\n(Are problematic detections more annotated?)", fontsize=12)
for i, v in enumerate(note_rate_by_cat.values):
    ax.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=10)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "reviewer_notes_v2.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ reviewer_notes_v2.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 4: EDGE CASES AND MISCLASSIFICATIONS — CLOSE UP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 4: Edge cases close-up…")

fig = plt.figure(figsize=(22, 14))
gs = gridspec.GridSpec(2, 2, hspace=0.35, wspace=0.3)

# Panel 1: UNCERTAIN verdict — all 10 terms with details
ax = fig.add_subplot(gs[0, 0])
ax.axis("off")
uncertain = df[df["verdict_clean"] == "UNCERTAIN"].copy()
text = "Terms with UNCERTAIN Reviewer Verdict\n"
text += "═" * 55 + "\n"
text += "(Detector flagged as Arabic; reviewers unsure)\n\n"
for _, row in uncertain.iterrows():
    term = str(row["norm_control"])[:25]
    etym = str(row["etymology_clean"])
    conf = row["confidence_score"]
    note = str(row["notes"])[:65] if pd.notna(row["notes"]) else "(no note)"
    text += f"▸ {term}\n"
    text += f"  Etymology: {etym} | AI conf: {conf}\n"
    text += f"  Note: {note}\n\n"
ax.text(0.02, 0.98, text, transform=ax.transAxes, fontsize=8.5,
        va="top", fontfamily="monospace", linespacing=1.25)
ax.set_title(f"UNCERTAIN Verdict ({len(uncertain)} terms)", fontsize=12, fontweight="bold")

# Panel 2: Persian / Persian-Arabic terms — why were they included?
ax = fig.add_subplot(gs[0, 1])
ax.axis("off")
persian = df[df["etymology_clean"].isin(["Persian", "Persian-Arabic"])].copy()
text = "Persian & Persian-Arabic Terms\n"
text += "═" * 55 + "\n"
text += "(Included because they entered Latin via Arabic tradition)\n\n"
for _, row in persian.iterrows():
    term = str(row["norm_control"])[:22]
    etym = str(row["etymology_clean"])
    note = str(row["notes"])[:60] if pd.notna(row["notes"]) else "(no note)"
    text += f"▸ {term:22s} [{etym}]\n"
    text += f"  {note}\n\n"
ax.text(0.02, 0.98, text, transform=ax.transAxes, fontsize=8.5,
        va="top", fontfamily="monospace", linespacing=1.25)
ax.set_title(f"Persian-Tradition Terms ({len(persian)} terms)", fontsize=12, fontweight="bold")

# Panel 3: mixed / unclear terms
ax = fig.add_subplot(gs[1, 0])
ax.axis("off")
ambiguous = df[df["etymology_clean"].isin(["mixed", "unclear"])].copy()
text = "Mixed & Unclear Etymology Terms\n"
text += "═" * 55 + "\n"
text += "(Included despite debated or uncertain origins)\n\n"
for _, row in ambiguous.iterrows():
    term = str(row["norm_control"])[:22]
    etym = str(row["etymology_clean"])
    note = str(row["notes"])[:65] if pd.notna(row["notes"]) else "(no note)"
    text += f"▸ {term:22s} [{etym}]\n"
    text += f"  {note}\n\n"
ax.text(0.02, 0.98, text, transform=ax.transAxes, fontsize=8,
        va="top", fontfamily="monospace", linespacing=1.25)
ax.set_title(f"Ambiguous Terms ({len(ambiguous)} terms)", fontsize=12, fontweight="bold")

# Panel 4: other/specific etymology (e.g., Egyptian Amun)
ax = fig.add_subplot(gs[1, 1])
ax.axis("off")
other_sp = df[df["etymology_clean"] == "other/specific"].copy()
# Also show the 66 "not reviewed" terms
not_rev = df[df["etymology_clean"] == "not reviewed"]
text = f"Other/Specific Etymologies ({len(other_sp)} terms)\n"
text += "═" * 55 + "\n\n"
for _, row in other_sp.iterrows():
    term = str(row["norm_control"])[:22]
    etym_raw = str(row["Etymology"])[:50]
    note = str(row["notes"])[:55] if pd.notna(row["notes"]) else "(no note)"
    text += f"▸ {term}: {etym_raw}\n  {note}\n\n"

text += f"\nTerms Not Yet Classified ({len(not_rev)} terms)\n"
text += "─" * 55 + "\n"
text += "These were included (verdict=ARABIC) but no\n"
text += "etymology was assigned during review.\n\n"
top_unrev = not_rev["norm_control"].value_counts().head(10)
for term, cnt in top_unrev.items():
    text += f"  {str(term):25s} ({cnt}x)\n"
text += f"  … {len(not_rev)} terms total"

ax.text(0.02, 0.98, text, transform=ax.transAxes, fontsize=8.5,
        va="top", fontfamily="monospace", linespacing=1.25)
ax.set_title("Other & Unclassified", fontsize=12, fontweight="bold")

fig.suptitle("Edge Cases: Terms Where Detection Was Not Straightforward",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "edge_cases.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ edge_cases.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 5: ETYMOLOGY PATHWAYS FROM REVIEWER NOTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 5: Etymology pathways…")

def extract_source_form(note):
    if pd.isna(note): return None
    note = str(note)
    m = re.search(r'from\s+([\w\-\']+(?:\s+[\w\-\']+)?)', note, re.IGNORECASE)
    if m: return m.group(1)
    m = re.search(r'(al-[\w]+)', note, re.IGNORECASE)
    if m: return m.group(1)
    return None

df["source_form"] = df["notes"].apply(extract_source_form)
has_source = df[df["source_form"].notna()].copy()

fig, axes = plt.subplots(1, 2, figsize=(20, 10))

# Left: source → Latin pathways
ax = axes[0]
pairs = has_source.groupby(["source_form", "norm_control"]).size().reset_index(name="count")
pairs = pairs.sort_values("count", ascending=False).head(25)
y = np.arange(len(pairs))
ax.barh(y, pairs["count"], color=PAL["teal"])
labels_f = [f'{row["source_form"]}  →  {row["norm_control"]}'
            for _, row in pairs.iterrows()]
ax.set_yticks(y)
ax.set_yticklabels(labels_f, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel("number of entries with this pathway")
ax.set_title("Etymological Pathways Documented by Reviewers\n(Arabic/Persian source → Latin term in Ruland)",
             fontsize=12)
for i, v in enumerate(pairs["count"]):
    ax.text(v + 0.2, i, str(v), va="center", fontsize=9)

# Right: intermediary languages
ax = axes[1]
intermediaries = Counter()
for note in df["notes"].dropna():
    n = str(note).lower()
    if "persian" in n: intermediaries["Persian"] += 1
    if "greek" in n: intermediaries["Greek"] += 1
    if "spanish" in n: intermediaries["Spanish"] += 1
    if "french" in n: intermediaries["French"] += 1
    if "german" in n: intermediaries["German"] += 1
    if "egyptian" in n: intermediaries["Egyptian"] += 1
    if "latin" in n and ("related" in n or "potential" in n or "but" in n):
        intermediaries["Latin (confused)"] += 1
    if "al-" in n and "persian" not in n and "greek" not in n:
        intermediaries["Arabic (direct)"] += 1

inter_s = pd.Series(intermediaries).sort_values(ascending=True)
inter_colors = {
    "Arabic (direct)": PAL["green"], "Persian": PAL["purple"],
    "Greek": PAL["teal"], "Latin (confused)": PAL["orange"],
    "German": PAL["brown"], "Spanish": PAL["pink"],
    "French": PAL["pink"], "Egyptian": PAL["gold"],
}
colors_i = [inter_colors.get(k, PAL["gray"]) for k in inter_s.index]
ax.barh(range(len(inter_s)), inter_s.values, color=colors_i)
ax.set_yticks(range(len(inter_s)))
ax.set_yticklabels(inter_s.index, fontsize=10)
ax.set_xlabel("mentions in reviewer notes")
ax.set_title("Languages Mentioned in Etymology Notes\n(transmission routes & confusion sources)", fontsize=12)
for i, v in enumerate(inter_s.values):
    ax.text(v + 0.3, i, str(v), va="center", fontsize=10)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "etymology_pathways_v2.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ etymology_pathways_v2.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 6: EXTERNAL VALIDATION — WHAT DO WIKTIONARY AND EMLAP TELL US?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 6: External validation…")

fig, axes = plt.subplots(2, 2, figsize=(18, 14))

# Panel 1: overall validation rates
ax = axes[0, 0]
wiki_yes = (df["wiki_clean"] == "yes").sum()
wiki_maybe = (df["wiki_clean"] == "maybe").sum()
wiki_no = (df["wiki_clean"] == "no").sum()
emlap_yes = (df["emlap_clean"] == "yes_corpus").sum()
emlap_no = (df["emlap_clean"] == "no").sum()

validation = pd.DataFrame({
    "source": ["Wiktionary\n(Arabic etymology)", "Wiktionary\n(Arabic etymology)",
               "Wiktionary\n(Arabic etymology)",
               "EMLAP corpus\n(term attested)", "EMLAP corpus\n(term attested)"],
    "status": ["confirmed", "maybe", "not found",
                "found in corpus", "not found"],
    "count": [wiki_yes, wiki_maybe, wiki_no, emlap_yes, emlap_no],
})
# Simple grouped bars
x_pos = [0, 1]
ax.bar([0], [100*wiki_yes/len(df)], width=0.25, color=PAL["green"], label="confirmed/found")
ax.bar([0.25], [100*wiki_maybe/len(df)], width=0.25, color=PAL["orange"], label="maybe")
ax.bar([0.5], [100*wiki_no/len(df)], width=0.25, color=PAL["red"], label="not found")
ax.bar([1.2], [100*emlap_yes/len(df)], width=0.25, color=PAL["green"])
ax.bar([1.45], [100*emlap_no/len(df)], width=0.25, color=PAL["red"])
ax.set_xticks([0.25, 1.325])
ax.set_xticklabels(["Wiktionary\n(Arabic etymology)", "EMLAP corpus\n(term attestation)"], fontsize=10)
ax.set_ylabel("% of included terms")
ax.set_title("External Validation of Included Terms\n(How many can be independently confirmed?)", fontsize=12)
ax.legend(fontsize=9)

# Panel 2: Wiktionary × EMLAP agreement
ax = axes[0, 1]
agree = pd.crosstab(df["wiki_clean"], df["emlap_clean"])
agree_r = [c for c in ["yes", "maybe", "no", "other"] if c in agree.index]
agree_c = [c for c in ["yes_corpus", "no", "other"] if c in agree.columns]
agree = agree.reindex(index=agree_r, columns=agree_c).fillna(0)
im = ax.imshow(agree.values, aspect="auto", cmap="Blues", interpolation="nearest")
ax.set_xticks(range(len(agree_c)))
ax.set_xticklabels(agree_c, fontsize=10)
ax.set_yticks(range(len(agree_r)))
ax.set_yticklabels(agree_r, fontsize=10)
for i in range(len(agree_r)):
    for j in range(len(agree_c)):
        val = int(agree.values[i, j])
        ax.text(j, i, str(val), ha="center", va="center", fontsize=12,
                fontweight="bold", color="white" if val > 50 else "black")
ax.set_xlabel("EMLAP corpus")
ax.set_ylabel("Wiktionary")
ax.set_title("Agreement Between External Sources", fontsize=12)
plt.colorbar(im, ax=ax, shrink=0.6)

# Panel 3: EMLAP depth — how widely attested?
ax = axes[1, 0]
_emlap_tmp = df[["emlap_total_occurrences", "emlap_distinct_works"]].apply(pd.to_numeric, errors="coerce").dropna()
emlap_occ = _emlap_tmp["emlap_total_occurrences"]
emlap_works = _emlap_tmp["emlap_distinct_works"]
ax.scatter(emlap_works, emlap_occ, alpha=0.4, s=20, color=PAL["blue"])
ax.set_xlabel("distinct works in EMLAP corpus")
ax.set_ylabel("total EMLAP occurrences")
ax.set_title("EMLAP Attestation Depth\n(How widely attested are these terms?)", fontsize=12)
ax.set_yscale("symlog", linthresh=1)
# Label outliers
df["_emlap_occ_num"] = pd.to_numeric(df["emlap_total_occurrences"], errors="coerce")
df["_emlap_wrk_num"] = pd.to_numeric(df["emlap_distinct_works"], errors="coerce")
for _, row in df.nlargest(8, "_emlap_occ_num").iterrows():
    occ = row["_emlap_occ_num"]
    wrk = row["_emlap_wrk_num"]
    if pd.notna(occ) and pd.notna(wrk):
        ax.annotate(str(row["norm_control"])[:15],
                    xy=(wrk, occ), fontsize=7, color=PAL["darkblue"],
                    xytext=(3, 3), textcoords="offset points")

# Panel 4: Wiktionary gap — what's missing?
ax = axes[1, 1]
ax.axis("off")
wiki_no_df = df[df["wiki_clean"] == "no"]
wiki_no_terms = wiki_no_df["norm_control"].value_counts().head(20)
text = "Terms NOT in Wiktionary as Arabic\n"
text += "═" * 50 + "\n"
text += f"({len(wiki_no_df)} of {len(df)} terms = {100*len(wiki_no_df)/len(df):.0f}% coverage gap)\n\n"
text += "Most common unconfirmed terms:\n"
for term, cnt in wiki_no_terms.items():
    etym = df[df["norm_control"] == term]["etymology_clean"].mode()
    etym_str = etym.iloc[0] if len(etym) > 0 else "?"
    emlap = (df[(df["norm_control"] == term) & (df["emlap_clean"] == "yes_corpus")]).shape[0] > 0
    emlap_str = "EMLAP:yes" if emlap else "EMLAP:no"
    text += f"  {str(term):22s} ({cnt}x) [{etym_str}] {emlap_str}\n"
text += f"\n→ Many confirmed Arabic terms lack\n  Wiktionary documentation"

ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9,
        va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title("Wiktionary Documentation Gap", fontsize=12)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "external_validation_v2.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ external_validation_v2.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 7: DETECTION QUALITY BY LETTER SECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 7: Detection quality by letter section…")

fig, axes = plt.subplots(2, 1, figsize=(20, 12))

letters_with_data = sorted(df["first_letter"].dropna().unique())

# Top: stacked bar — quality category by letter
ax = axes[0]
cat_order = ["correctly detected\n(Arabic)", "correctly detected\n(Latinised Arabic)",
             "related tradition\n(Persian/Persian-Arabic)",
             "ambiguous\n(mixed/unclear origin)", "not yet classified", "other/specific"]
cat_letter = pd.crosstab(df["first_letter"], df["quality_cat"])
cat_letter = cat_letter.reindex(index=letters_with_data).fillna(0)
col_order = [c for c in cat_order if c in cat_letter.columns]
cat_letter = cat_letter[col_order]
cat_letter_colors = [cat_colors.get(c, PAL["gray"]) for c in col_order]
cat_letter.plot(kind="bar", stacked=True, ax=ax, color=cat_letter_colors, width=0.75)
ax.set_xlabel("letter section")
ax.set_ylabel("number of included terms")
ax.set_title("Detection Quality by Letter Section\n(What is the composition of included terms in each section?)",
             fontsize=13)
ax.legend(title="detection quality", bbox_to_anchor=(1.0, 1.0), fontsize=8)
ax.set_xticklabels(letters_with_data, rotation=0)

# Bottom: proportion
ax = axes[1]
cat_letter_pct = cat_letter.div(cat_letter.sum(axis=1), axis=0) * 100
cat_letter_pct.plot(kind="bar", stacked=True, ax=ax, color=cat_letter_colors,
                     width=0.75, legend=False)
ax.set_xlabel("letter section")
ax.set_ylabel("% of terms")
ax.set_title("Detection Quality Composition (proportional)", fontsize=13)
ax.set_xticklabels(letters_with_data, rotation=0)
ax.set_ylim(0, 100)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "quality_by_letter.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ quality_by_letter.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 8: TOP TERMS — FREQUENCY, QUALITY, AND VALIDATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 8: Top terms with quality context…")

term_agg = df.groupby("norm_control").agg(
    count=("lemma", "size"),
    etymology=("etymology_clean", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else ""),
    wiki_rate=("wiki_clean", lambda x: 100 * (x == "yes").sum() / len(x)),
    emlap_rate=("emlap_clean", lambda x: 100 * (x == "yes_corpus").sum() / len(x)),
    has_notes=("notes", lambda x: x.notna().sum()),
    mean_conf=("confidence_score", "mean"),
    english=("english_translation", "first"),
).sort_values("count", ascending=False)

top30 = term_agg.head(30)

fig, ax = plt.subplots(figsize=(20, 12))
y = np.arange(len(top30))

etym_colors = {
    "Arabic": PAL["green"], "Latinised Arabic": PAL["teal"],
    "Persian-Arabic": PAL["purple"], "Persian": PAL["pink"],
    "mixed": PAL["orange"], "unclear": PAL["gray"],
    "not reviewed": PAL["lightblue"], "other/specific": PAL["brown"],
}
bar_colors = [etym_colors.get(row["etymology"], PAL["gray"]) for _, row in top30.iterrows()]
ax.barh(y, top30["count"], color=bar_colors, edgecolor="white")
ax.set_yticks(y)

labels_t = []
for term, row in top30.iterrows():
    eng = str(row["english"])[:20] if pd.notna(row["english"]) else ""
    labels_t.append(f'{term}  ("{eng}")')
ax.set_yticklabels(labels_t, fontsize=8.5)
ax.invert_yaxis()
ax.set_xlabel("number of dictionary entries containing this term")
ax.set_title("Top 30 Arabic-Tradition Terms in Ruland's Dictionary\n"
             "(bar color = reviewer etymology; annotations = validation status)",
             fontsize=13)

# Annotations
for i, (term, row) in enumerate(top30.iterrows()):
    wiki = "W✓" if row["wiki_rate"] > 0 else "W·"
    emlap = "E✓" if row["emlap_rate"] > 0 else "E·"
    note = "N✓" if row["has_notes"] > 0 else "N·"
    ax.text(row["count"] + 0.3, i,
            f'[{wiki} {emlap} {note}]  {row["etymology"]}',
            va="center", fontsize=7.5, color=PAL["darkblue"])

# Legend
handles = [mpatches.Patch(color=etym_colors[e], label=e)
           for e in ["Arabic", "Latinised Arabic", "Persian-Arabic",
                      "mixed", "unclear", "not reviewed"]
           if e in set(top30["etymology"])]
ax.legend(handles=handles, title="reviewer etymology", fontsize=9, loc="lower right")

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "top_terms_quality.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ top_terms_quality.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 9: NORMALIZED CONTROL STRINGS — SPELLING HARMONIZATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 9: Spelling harmonization…")

# How many detected_string values map to each norm_control?
detect_to_norm = df.groupby("norm_control").agg(
    n_spellings=("detected_string", "nunique"),
    spellings=("detected_string", lambda x: ", ".join(sorted(x.unique()))),
    count=("lemma", "size"),
).sort_values("n_spellings", ascending=False)

multi_spelling = detect_to_norm[detect_to_norm["n_spellings"] > 1]

fig, axes = plt.subplots(1, 2, figsize=(20, 10))

# Left: terms with most spelling variants
ax = axes[0]
top_multi = multi_spelling.head(20)
y = np.arange(len(top_multi))
ax.barh(y, top_multi["n_spellings"], color=PAL["orange"])
ax.set_yticks(y)
ax.set_yticklabels(top_multi.index, fontsize=10)
ax.invert_yaxis()
ax.set_xlabel("number of detected spelling variants")
ax.set_title("Terms with Most Spelling Variants\n(harmonized by reviewers into one control string)", fontsize=12)
for i, (term, row) in enumerate(top_multi.iterrows()):
    sp = row["spellings"][:55]
    if len(row["spellings"]) > 55: sp += "…"
    ax.text(row["n_spellings"] + 0.1, i, sp, va="center", fontsize=7,
            color=PAL["darkblue"])

# Right: distribution of variant counts
ax = axes[1]
var_dist = detect_to_norm["n_spellings"].value_counts().sort_index()
ax.bar(var_dist.index, var_dist.values, color=PAL["teal"])
ax.set_xlabel("number of spelling variants per normalized term")
ax.set_ylabel("number of terms")
ax.set_title("Distribution of Spelling Variation\n(Most terms have 1 spelling; some have 5+)", fontsize=12)
for x_val, y_val in zip(var_dist.index, var_dist.values):
    ax.text(x_val, y_val + 1, str(y_val), ha="center", fontsize=9)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "spelling_harmonization.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ spelling_harmonization.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 10: DETECTION LESSONS — WHAT CAN WE LEARN?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 10: Detection quality lessons…")

fig, axes = plt.subplots(2, 2, figsize=(18, 14))

# Panel 1: precision at different confidence thresholds
ax = axes[0, 0]
# What % of terms at each confidence level were correctly Arabic?
conf_groups = df.groupby("confidence_score").apply(
    lambda g: pd.Series({
        "n": len(g),
        "pct_arabic": 100 * g["etymology_clean"].isin(["Arabic", "Latinised Arabic"]).sum() / len(g),
        "pct_ambiguous": 100 * g["etymology_clean"].isin(["mixed", "unclear", "Persian", "Persian-Arabic"]).sum() / len(g),
        "pct_unreviewed": 100 * (g["etymology_clean"] == "not reviewed").sum() / len(g),
    })
).reset_index()

x_c = np.arange(len(conf_groups))
ax.bar(x_c, conf_groups["pct_arabic"], label="correctly Arabic", color=PAL["green"])
ax.bar(x_c, conf_groups["pct_ambiguous"], bottom=conf_groups["pct_arabic"],
       label="non-Arabic/ambiguous", color=PAL["orange"])
ax.bar(x_c, conf_groups["pct_unreviewed"],
       bottom=conf_groups["pct_arabic"] + conf_groups["pct_ambiguous"],
       label="not reviewed", color=PAL["lightblue"])
ax.set_xticks(x_c)
ax.set_xticklabels([f"{v:.2f}\n(n={int(n)})" for v, n in
                     zip(conf_groups["confidence_score"], conf_groups["n"])],
                    fontsize=8)
ax.set_xlabel("AI confidence score")
ax.set_ylabel("% of terms")
ax.set_title("Detection Precision by Confidence Score\n(What fraction at each confidence level is correctly Arabic?)",
             fontsize=12)
ax.legend(fontsize=9)
ax.set_ylim(0, 105)

# Panel 2: common false-positive patterns
ax = axes[0, 1]
ax.axis("off")
text = "Lessons from Reviewer Notes:\n"
text += "Common Detection Pitfalls\n"
text += "═" * 50 + "\n\n"
text += "1. LATIN LOOK-ALIKES\n"
text += "   sulphur → 'Latin but potentially related\n"
text += "   to Arabic al-sufr (yellow)'\n"
text += "   → The detector confused Latin words that\n"
text += "   superficially resemble Arabic roots\n\n"
text += "2. GREEK/EGYPTIAN ORIGINS MISATTRIBUTED\n"
text += "   antimonium → 'origins quite debated,\n"
text += "   possibly from Greek stimmi, or Egyptian'\n"
text += "   → Complex etymological chains mislead\n"
text += "   the detector\n\n"
text += "3. PERSONAL NAMES vs VOCABULARY\n"
text += "   Avicenna → 'an Arab author so technically\n"
text += "   yes but it's a personal name'\n"
text += "   → Detector doesn't distinguish person\n"
text += "   names from borrowed vocabulary\n\n"
text += "4. PERSIAN-ARABIC CONFLATION\n"
text += "   naphtha → 'originally Persian, naft'\n"
text += "   tutia → 'from Persian, Arabic tutiya'\n"
text += "   → Detector treats all as 'Arabic'\n\n"
text += "5. PSEUDO-ARABIC (Paracelsian)\n"
text += "   → 'Paracelsian Pseudo-Arabic most\n"
text += "   likely but probably relevant enough'"

ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9,
        va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title("Detection Pitfalls Identified by Reviewers", fontsize=12)

# Panel 3: excluded vs included — what was cut?
ax = axes[1, 0]
# Compare confidence distributions
raw_incl = raw_df.merge(df[["detected_string", "lemma"]].drop_duplicates(),
                         on=["detected_string", "lemma"], how="inner",
                         indicator=True)
# Get excluded rows (in raw but not in TSV)
# Approximate: use irrelevance_probability to characterize excluded
raw_df["irr_group"] = pd.cut(raw_df["irrelevance_probability"].fillna(0.5),
                              bins=[0, 0.15, 0.3, 0.5, 0.8, 1.0],
                              labels=["0-0.15", "0.15-0.3", "0.3-0.5", "0.5-0.8", "0.8-1.0"])
irr_dist = raw_df["irr_group"].value_counts().sort_index()
ax.bar(range(len(irr_dist)), irr_dist.values, color=PAL["blue"])
ax.set_xticks(range(len(irr_dist)))
ax.set_xticklabels(irr_dist.index, fontsize=10)
ax.set_xlabel("irrelevance probability bracket")
ax.set_ylabel("number of detections (original 928)")
ax.set_title("Original Pipeline: Irrelevance Score Distribution\n(Higher = more likely false positive)", fontsize=12)
# Mark the threshold
ax.axvline(1.5, color=PAL["red"], ls="--", lw=2, alpha=0.7)
ax.text(1.7, ax.get_ylim()[1] * 0.9, "← kept | excluded →",
        fontsize=10, color=PAL["red"])

# Panel 4: summary statistics
ax = axes[1, 1]
ax.axis("off")
n_arabic_correct = df["etymology_clean"].isin(["Arabic", "Latinised Arabic"]).sum()
n_total_reviewed = (df["etymology_clean"] != "not reviewed").sum()
precision = 100 * n_arabic_correct / n_total_reviewed if n_total_reviewed > 0 else 0

text = f"""Detection Quality Metrics
{'═' * 45}

Pipeline throughput:
  Raw detections:           928
  After filtering:          ~421 (irr ≤ 0.3)
  Human-included:           363
  Overall retention:        {100*363/928:.1f}%

Among {n_total_reviewed} reviewed terms:
  Correctly Arabic:         {n_arabic_correct} ({precision:.1f}% precision)
  Persian/Persian-Arabic:   {df['etymology_clean'].isin(['Persian','Persian-Arabic']).sum()} (related but not Arabic)
  Mixed/unclear:            {df['etymology_clean'].isin(['mixed','unclear']).sum()} (ambiguous)
  Other:                    {(df['etymology_clean']=='other/specific').sum()}

Not yet reviewed:           {(df['etymology_clean']=='not reviewed').sum()} terms

External validation:
  Wiktionary confirms:      {(df['wiki_clean']=='yes').sum()}/{len(df)} ({100*(df['wiki_clean']=='yes').sum()/len(df):.0f}%)
  EMLAP corpus attests:     {(df['emlap_clean']=='yes_corpus').sum()}/{len(df)} ({100*(df['emlap_clean']=='yes_corpus').sum()/len(df):.0f}%)
  Wiktionary gap:           {(df['wiki_clean']=='no').sum()} terms not documented

Reviewer notes:             {df['notes'].notna().sum()}/{len(df)} ({100*df['notes'].notna().sum()/len(df):.0f}%)
Unique normalized terms:    {df['norm_control'].nunique()}
"""
ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9.5,
        va="top", fontfamily="monospace", linespacing=1.35)
ax.set_title("Detection Quality Summary", fontsize=12)

plt.suptitle("What We Learned: Detection Pipeline Quality Assessment",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "detection_lessons.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ detection_lessons.png")


print(f"\nAll done. {len(os.listdir(OUTDIR))} files in {OUTDIR}")
for f in sorted(os.listdir(OUTDIR)):
    print(f"  {f}")
