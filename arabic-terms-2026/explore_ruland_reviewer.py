#!/usr/bin/env python3
"""
Ruland 1612 – Human Reviewer Verdicts, Etymology Classifications,
               and Reviewer Notes Analysis
================================================================
Explores the TSV with 3-reviewer comparison verdicts, etymology
classifications, free-text notes, and external validation
(Wiktionary, EMLAP corpus).
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
df = pd.read_csv(TSV_PATH, sep="\t")

# Rename for convenience
df = df.rename(columns={
    "lemma /headword": "lemma",
    "3 human reviewer comparison verdict": "verdict",
    "Include (controled vocab, y/n)": "include",
    "normalized control string (harmonized) ": "norm_control",
})

# Normalize verdict (various capitalizations of ARABIC)
df["verdict_clean"] = df["verdict"].str.strip().str.upper()
# Normalize Etymology
df["etymology_clean"] = df["Etymology"].str.strip().str.lower().fillna("not specified")
df.loc[df["etymology_clean"] == "arabic", "etymology_clean"] = "Arabic"
df.loc[df["etymology_clean"] == "latinised arabic", "etymology_clean"] = "Latinised Arabic"
df.loc[df["etymology_clean"] == "persian-arabic", "etymology_clean"] = "Persian-Arabic"
df.loc[df["etymology_clean"] == "persian", "etymology_clean"] = "Persian"
df.loc[df["etymology_clean"] == "unclear", "etymology_clean"] = "unclear"
df.loc[df["etymology_clean"] == "mixed", "etymology_clean"] = "mixed"
# Fix remaining
df.loc[df["etymology_clean"].str.contains("egyptian", na=False), "etymology_clean"] = "mixed"

# Add first_letter
df["first_letter"] = df["lemma"].dropna().str.strip().str[0].str.upper()

# Normalize wiki_match_flag
df["wiki_clean"] = df["wiki_match_flag"].astype(str).str.strip().str.lower()
df.loc[~df["wiki_clean"].isin(["yes", "no", "maybe"]), "wiki_clean"] = "other/missing"

# Normalize emlap_match_flag
df["emlap_clean"] = df["emlap_match_flag"].astype(str).str.strip().str.lower()
df.loc[~df["emlap_clean"].isin(["yes_corpus", "no"]), "emlap_clean"] = "other"

print(f"  TSV: {len(df)} rows, {df['lemma'].nunique()} unique lemmas")
print(f"  Verdict distribution: {df['verdict_clean'].value_counts().to_dict()}")
print(f"  Etymology distribution: {df['etymology_clean'].value_counts().to_dict()}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 1: OVERVIEW — VERDICT, ETYMOLOGY, EXTERNAL VALIDATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 1: Overview dashboard…")

fig = plt.figure(figsize=(20, 12))
gs = gridspec.GridSpec(2, 3, hspace=0.35, wspace=0.35)

# Panel 1: Verdict distribution
ax = fig.add_subplot(gs[0, 0])
verdict_counts = df["verdict_clean"].value_counts()
colors_v = [PAL["green"] if "ARABIC" in v else PAL["orange"] for v in verdict_counts.index]
bars = ax.barh(range(len(verdict_counts)), verdict_counts.values, color=colors_v)
ax.set_yticks(range(len(verdict_counts)))
ax.set_yticklabels(verdict_counts.index, fontsize=10)
ax.set_xlabel("number of terms")
ax.set_title("3-Reviewer Comparison Verdict", fontsize=12, fontweight="bold")
for i, v in enumerate(verdict_counts.values):
    ax.text(v + 1, i, f"{v} ({100*v/len(df):.1f}%)", va="center", fontsize=9)

# Panel 2: Etymology classification
ax = fig.add_subplot(gs[0, 1])
etym_counts = df["etymology_clean"].value_counts()
etym_colors = {
    "Arabic": PAL["green"], "Latinised Arabic": PAL["teal"],
    "Persian-Arabic": PAL["purple"], "Persian": PAL["pink"],
    "mixed": PAL["orange"], "unclear": PAL["gray"],
    "not specified": PAL["lightblue"],
}
colors_e = [etym_colors.get(e, PAL["gray"]) for e in etym_counts.index]
ax.barh(range(len(etym_counts)), etym_counts.values, color=colors_e)
ax.set_yticks(range(len(etym_counts)))
ax.set_yticklabels(etym_counts.index, fontsize=10)
ax.set_xlabel("number of terms")
ax.set_title("Etymology Classification\n(human-assigned)", fontsize=12, fontweight="bold")
for i, v in enumerate(etym_counts.values):
    ax.text(v + 1, i, f"{v} ({100*v/len(df):.1f}%)", va="center", fontsize=9)

# Panel 3: Wiktionary match
ax = fig.add_subplot(gs[0, 2])
wiki_counts = df["wiki_clean"].value_counts()
wiki_colors = {"yes": PAL["green"], "no": PAL["red"], "maybe": PAL["orange"],
               "other/missing": PAL["gray"]}
ax.pie(wiki_counts.values,
       labels=[f"{k}\n({v})" for k, v in wiki_counts.items()],
       colors=[wiki_colors.get(k, PAL["gray"]) for k in wiki_counts.index],
       autopct="%1.1f%%", startangle=90, textprops={"fontsize": 10})
ax.set_title("Wiktionary Arabic\nEtymology Match", fontsize=12, fontweight="bold")

# Panel 4: EMLAP corpus match
ax = fig.add_subplot(gs[1, 0])
emlap_counts = df["emlap_clean"].value_counts()
emlap_colors = {"yes_corpus": PAL["green"], "no": PAL["red"], "other": PAL["gray"]}
ax.pie(emlap_counts.values,
       labels=[f"{k}\n({v})" for k, v in emlap_counts.items()],
       colors=[emlap_colors.get(k, PAL["gray"]) for k in emlap_counts.index],
       autopct="%1.1f%%", startangle=90, textprops={"fontsize": 10})
ax.set_title("EMLAP Corpus Match\n(found in early modern Latin corpus)", fontsize=12, fontweight="bold")

# Panel 5: Confidence score distribution
ax = fig.add_subplot(gs[1, 1])
conf_counts = df["confidence_score"].value_counts().sort_index()
ax.bar(range(len(conf_counts)), conf_counts.values, color=PAL["blue"])
ax.set_xticks(range(len(conf_counts)))
ax.set_xticklabels([f"{v:.2f}" for v in conf_counts.index], rotation=45)
ax.set_xlabel("confidence score")
ax.set_ylabel("count")
ax.set_title("Confidence Score Distribution\n(AI extraction confidence)", fontsize=12, fontweight="bold")

# Panel 6: summary stats text
ax = fig.add_subplot(gs[1, 2])
ax.axis("off")
n_arabic_verdict = (df["verdict_clean"] == "ARABIC").sum()
n_uncertain = (df["verdict_clean"] == "UNCERTAIN").sum()
n_arabic_etym = (df["etymology_clean"] == "Arabic").sum()
n_wiki_yes = (df["wiki_clean"] == "yes").sum()
n_emlap_yes = (df["emlap_clean"] == "yes_corpus").sum()
n_with_notes = df["notes"].notna().sum()
summary = f"""Dataset Summary
{'─' * 40}
Total terms:              {len(df)}
All included (y/n):       {(df['include'] == 'yes').sum()} yes

Reviewer verdict:
  ARABIC:                 {n_arabic_verdict} ({100*n_arabic_verdict/len(df):.1f}%)
  UNCERTAIN:              {n_uncertain} ({100*n_uncertain/len(df):.1f}%)

Etymology:
  Arabic:                 {n_arabic_etym} ({100*n_arabic_etym/len(df):.1f}%)
  Persian-Arabic:         {(df['etymology_clean']=='Persian-Arabic').sum()}
  Latinised Arabic:       {(df['etymology_clean']=='Latinised Arabic').sum()}
  Persian:                {(df['etymology_clean']=='Persian').sum()}
  mixed / unclear:        {(df['etymology_clean'].isin(['mixed','unclear'])).sum()}

External validation:
  Wiktionary match:       {n_wiki_yes} ({100*n_wiki_yes/len(df):.1f}%)
  EMLAP corpus match:     {n_emlap_yes} ({100*n_emlap_yes/len(df):.1f}%)

Notes provided:           {n_with_notes} ({100*n_with_notes/len(df):.1f}%)
Unique norm. terms:       {df['norm_control'].nunique()}
"""
ax.text(0.05, 0.95, summary, transform=ax.transAxes, fontsize=10,
        va="top", fontfamily="monospace", linespacing=1.4)
ax.set_title("Summary", fontsize=12, fontweight="bold")

fig.suptitle("Human Reviewer Analysis: Arabic Terms in Ruland's Lexicon Alchemiae",
             fontsize=15, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "overview_dashboard.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ overview_dashboard.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 2: ETYMOLOGY × VERDICT — DO REVIEWERS AND ETYMOLOGY AGREE?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 2: Etymology × verdict cross-tab…")

fig, axes = plt.subplots(1, 2, figsize=(18, 8))

# Left: heatmap
ax = axes[0]
cross = pd.crosstab(df["etymology_clean"], df["verdict_clean"])
etym_order = ["Arabic", "Latinised Arabic", "Persian-Arabic", "Persian",
              "mixed", "unclear", "not specified"]
etym_order = [e for e in etym_order if e in cross.index]
verdict_order = ["ARABIC", "UNCERTAIN"]
verdict_order = [v for v in verdict_order if v in cross.columns]
cross = cross.reindex(index=etym_order, columns=verdict_order).fillna(0)

im = ax.imshow(cross.values, aspect="auto", cmap="YlGn", interpolation="nearest")
ax.set_xticks(range(len(verdict_order)))
ax.set_xticklabels(verdict_order, fontsize=11)
ax.set_yticks(range(len(etym_order)))
ax.set_yticklabels(etym_order, fontsize=11)
for i in range(len(etym_order)):
    for j in range(len(verdict_order)):
        val = int(cross.values[i, j])
        ax.text(j, i, str(val), ha="center", va="center",
                fontsize=12, fontweight="bold",
                color="white" if val > 30 else "black")
ax.set_xlabel("3-reviewer verdict")
ax.set_ylabel("etymology classification")
ax.set_title("Etymology × Reviewer Verdict\n(Do classifications agree?)", fontsize=12)
plt.colorbar(im, ax=ax, shrink=0.6)

# Right: proportion of each etymology that is ARABIC vs UNCERTAIN
ax = axes[1]
total_per_etym = cross.sum(axis=1)
pct_arabic = 100 * cross.get("ARABIC", 0) / total_per_etym
pct_uncertain = 100 * cross.get("UNCERTAIN", 0) / total_per_etym

y = np.arange(len(etym_order))
ax.barh(y - 0.15, pct_arabic.values, 0.3, label="ARABIC verdict",
        color=PAL["green"])
ax.barh(y + 0.15, pct_uncertain.values, 0.3, label="UNCERTAIN verdict",
        color=PAL["orange"])
ax.set_yticks(y)
ax.set_yticklabels(etym_order, fontsize=11)
ax.set_xlabel("% of terms")
ax.set_title("Reviewer Verdict by Etymology Type\n(% that reviewers called ARABIC vs UNCERTAIN)", fontsize=12)
ax.legend(fontsize=10)
ax.set_xlim(0, 110)
for i, (a, u) in enumerate(zip(pct_arabic.values, pct_uncertain.values)):
    if a > 0:
        ax.text(a + 1, i - 0.15, f"{a:.0f}%", va="center", fontsize=9)
    if u > 0:
        ax.text(u + 1, i + 0.15, f"{u:.0f}%", va="center", fontsize=9)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "etymology_verdict_crosstab.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ etymology_verdict_crosstab.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 3: REVIEWER NOTES — WHAT DID REVIEWERS SAY?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 3: Reviewer notes analysis…")

notes_df = df[df["notes"].notna()].copy()
note_counts = notes_df["notes"].value_counts()

# Categorize notes by theme
def categorize_note(note):
    n = str(note).lower()
    if "al-" in n or "from al" in n:
        return "Arabic al- etymology"
    if "from " in n and ("arabic" in n or "persian" in n):
        return "Arabic/Persian etymology"
    if "debated" in n or "unclear" in n or "origins" in n:
        return "debated/unclear origin"
    if "personal name" in n or "avicenna" in n or "author" in n:
        return "personal name"
    if "latin" in n or "greek" in n or "egyptian" in n:
        return "cross-linguistic note"
    if "lemmatiz" in n:
        return "lemmatization issue"
    if "paracels" in n or "pseudo" in n:
        return "Pseudo-Arabic"
    if "edge case" in n or "kind of" in n or "likely" in n or "probably" in n:
        return "hedged judgment"
    return "specific etymology"

notes_df["note_category"] = notes_df["notes"].apply(categorize_note)

fig, axes = plt.subplots(1, 3, figsize=(22, 9))

# Panel 1: note categories
ax = axes[0]
cat_counts = notes_df["note_category"].value_counts()
cat_colors = [PAL["blue"], PAL["green"], PAL["orange"], PAL["purple"],
              PAL["teal"], PAL["red"], PAL["brown"], PAL["pink"],
              PAL["gray"]][:len(cat_counts)]
ax.barh(range(len(cat_counts)), cat_counts.values, color=cat_colors)
ax.set_yticks(range(len(cat_counts)))
ax.set_yticklabels(cat_counts.index, fontsize=10)
ax.set_xlabel("number of notes")
ax.set_title("Reviewer Note Categories\n(thematic grouping of free-text notes)", fontsize=12)
for i, v in enumerate(cat_counts.values):
    ax.text(v + 0.5, i, str(v), va="center", fontsize=9)

# Panel 2: most common specific notes
ax = axes[1]
top_notes = note_counts.head(18)
y = np.arange(len(top_notes))
ax.barh(y, top_notes.values, color=PAL["teal"])
ax.set_yticks(y)
# Wrap long notes
labels_n = []
for note in top_notes.index:
    wrapped = textwrap.fill(str(note), width=45)
    if len(wrapped) > 90:
        wrapped = wrapped[:87] + "…"
    labels_n.append(wrapped)
ax.set_yticklabels(labels_n, fontsize=7.5)
ax.invert_yaxis()
ax.set_xlabel("count")
ax.set_title("Most Common Reviewer Notes\n(exact note text)", fontsize=12)
for i, v in enumerate(top_notes.values):
    ax.text(v + 0.2, i, str(v), va="center", fontsize=8)

# Panel 3: notes vs no notes — do noted terms differ?
ax = axes[2]
df["has_notes"] = df["notes"].notna()
# Compare: etymology distribution for noted vs un-noted terms
noted_etym = df[df["has_notes"]]["etymology_clean"].value_counts(normalize=True) * 100
unnoted_etym = df[~df["has_notes"]]["etymology_clean"].value_counts(normalize=True) * 100
compare_df = pd.DataFrame({"with notes": noted_etym, "without notes": unnoted_etym}).fillna(0)
compare_df = compare_df.reindex([e for e in etym_order if e in compare_df.index])

y2 = np.arange(len(compare_df))
ax.barh(y2 - 0.15, compare_df["with notes"], 0.3, label="with notes",
        color=PAL["orange"])
ax.barh(y2 + 0.15, compare_df["without notes"], 0.3, label="without notes",
        color=PAL["lightblue"])
ax.set_yticks(y2)
ax.set_yticklabels(compare_df.index, fontsize=10)
ax.set_xlabel("% of group")
ax.set_title("Etymology Distribution:\nNoted vs Un-Noted Terms", fontsize=12)
ax.legend(fontsize=10)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "reviewer_notes_analysis.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ reviewer_notes_analysis.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 4: ETYMOLOGY BY LETTER SECTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 4: Etymology by letter section…")

fig, axes = plt.subplots(2, 1, figsize=(20, 12))

letters_with_data = sorted(df["first_letter"].dropna().unique())

# Top: stacked bar — etymology by letter
ax = axes[0]
etym_letter = pd.crosstab(df["first_letter"], df["etymology_clean"])
etym_letter = etym_letter.reindex(index=letters_with_data).fillna(0)
col_order = [c for c in ["Arabic", "Latinised Arabic", "Persian-Arabic",
                          "Persian", "mixed", "unclear", "not specified"]
             if c in etym_letter.columns]
etym_letter = etym_letter[col_order]
etym_letter_colors = [etym_colors.get(c, PAL["gray"]) for c in col_order]
etym_letter.plot(kind="bar", stacked=True, ax=ax, color=etym_letter_colors, width=0.75)
ax.set_xlabel("letter section")
ax.set_ylabel("number of terms")
ax.set_title("Human-Assigned Etymology Classification by Letter Section", fontsize=13)
ax.legend(title="etymology", bbox_to_anchor=(1.0, 1.0), fontsize=9)
ax.set_xticklabels(letters_with_data, rotation=0)
# Annotate totals
for i, letter in enumerate(letters_with_data):
    total = etym_letter.loc[letter].sum() if letter in etym_letter.index else 0
    if total > 0:
        ax.text(i, total + 0.5, str(int(total)), ha="center", fontsize=8, fontweight="bold")

# Bottom: percentage view
ax = axes[1]
etym_letter_pct = etym_letter.div(etym_letter.sum(axis=1), axis=0) * 100
etym_letter_pct.plot(kind="bar", stacked=True, ax=ax, color=etym_letter_colors, width=0.75,
                      legend=False)
ax.set_xlabel("letter section")
ax.set_ylabel("% of terms")
ax.set_title("Etymology Distribution by Letter Section (proportional)", fontsize=13)
ax.set_xticklabels(letters_with_data, rotation=0)
ax.set_ylim(0, 100)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "etymology_by_letter_human.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ etymology_by_letter_human.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 5: EXTERNAL VALIDATION — WIKTIONARY × EMLAP × ETYMOLOGY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 5: External validation…")

fig, axes = plt.subplots(2, 2, figsize=(18, 14))

# Panel 1: Wiktionary match by etymology
ax = axes[0, 0]
wiki_etym = pd.crosstab(df["etymology_clean"], df["wiki_clean"])
wiki_etym = wiki_etym.reindex(index=[e for e in etym_order if e in wiki_etym.index])
wiki_col_order = [c for c in ["yes", "maybe", "no", "other/missing"] if c in wiki_etym.columns]
wiki_etym = wiki_etym[wiki_col_order]
wiki_etym.plot(kind="barh", stacked=True, ax=ax,
               color=[PAL["green"], PAL["orange"], PAL["red"], PAL["gray"]],
               width=0.6)
ax.set_xlabel("number of terms")
ax.set_title("Wiktionary Arabic Etymology Match\nby Human Etymology Classification", fontsize=12)
ax.legend(title="Wiktionary match", fontsize=9)

# Panel 2: EMLAP match by etymology
ax = axes[0, 1]
emlap_etym = pd.crosstab(df["etymology_clean"], df["emlap_clean"])
emlap_etym = emlap_etym.reindex(index=[e for e in etym_order if e in emlap_etym.index])
emlap_col_order = [c for c in ["yes_corpus", "no", "other"] if c in emlap_etym.columns]
emlap_etym = emlap_etym[emlap_col_order]
emlap_etym.plot(kind="barh", stacked=True, ax=ax,
                color=[PAL["green"], PAL["red"], PAL["gray"]],
                width=0.6)
ax.set_xlabel("number of terms")
ax.set_title("EMLAP Corpus Match\nby Human Etymology Classification", fontsize=12)
ax.legend(title="EMLAP match", fontsize=9)

# Panel 3: agreement matrix — wiki × emlap
ax = axes[1, 0]
agree = pd.crosstab(df["wiki_clean"], df["emlap_clean"])
agree_order_r = [c for c in ["yes", "maybe", "no", "other/missing"] if c in agree.index]
agree_order_c = [c for c in ["yes_corpus", "no", "other"] if c in agree.columns]
agree = agree.reindex(index=agree_order_r, columns=agree_order_c).fillna(0)

im = ax.imshow(agree.values, aspect="auto", cmap="Blues", interpolation="nearest")
ax.set_xticks(range(len(agree_order_c)))
ax.set_xticklabels(agree_order_c, fontsize=10)
ax.set_yticks(range(len(agree_order_r)))
ax.set_yticklabels(agree_order_r, fontsize=10)
for i in range(len(agree_order_r)):
    for j in range(len(agree_order_c)):
        val = int(agree.values[i, j])
        ax.text(j, i, str(val), ha="center", va="center", fontsize=12,
                fontweight="bold", color="white" if val > 50 else "black")
ax.set_xlabel("EMLAP corpus")
ax.set_ylabel("Wiktionary")
ax.set_title("Wiktionary × EMLAP Agreement\n(Do external sources agree?)", fontsize=12)
plt.colorbar(im, ax=ax, shrink=0.6)

# Panel 4: terms NOT in Wiktionary but in EMLAP (and vice versa)
ax = axes[1, 1]
ax.axis("off")
# Wiki=no but EMLAP=yes
wiki_no_emlap_yes = df[(df["wiki_clean"] == "no") & (df["emlap_clean"] == "yes_corpus")]
# Wiki=yes but EMLAP=no
wiki_yes_emlap_no = df[(df["wiki_clean"] == "yes") & (df["emlap_clean"] == "no")]

text = "Terms in EMLAP corpus but NOT in Wiktionary:\n"
text += "─" * 50 + "\n"
terms1 = wiki_no_emlap_yes["norm_control"].value_counts().head(12)
for t, c in terms1.items():
    text += f"  {str(t):25s} ({c}x)\n"
text += f"\n  … {len(wiki_no_emlap_yes)} terms total\n\n"

text += "Terms in Wiktionary but NOT in EMLAP corpus:\n"
text += "─" * 50 + "\n"
terms2 = wiki_yes_emlap_no["norm_control"].value_counts().head(8)
for t, c in terms2.items():
    text += f"  {str(t):25s} ({c}x)\n"
text += f"\n  … {len(wiki_yes_emlap_no)} terms total"

ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9.5,
        va="top", fontfamily="monospace", linespacing=1.4)
ax.set_title("Discrepancies Between External Sources", fontsize=12)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "external_validation.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ external_validation.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 6: NORMALIZED CONTROL TERMS — TOP TERMS WITH FULL CONTEXT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 6: Top normalized terms with context…")

term_agg = df.groupby("norm_control").agg(
    count=("lemma", "size"),
    n_entries=("lemma", "nunique"),
    etymology=("etymology_clean", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else ""),
    verdict=("verdict_clean", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else ""),
    wiki=("wiki_clean", lambda x: (x == "yes").sum()),
    emlap=("emlap_clean", lambda x: (x == "yes_corpus").sum()),
    has_notes=("notes", lambda x: x.notna().sum()),
    arabic=("arabic_script", "first"),
    english=("english_translation", "first"),
).sort_values("count", ascending=False)

top30 = term_agg.head(30)

fig, axes = plt.subplots(1, 2, figsize=(22, 12))

# Left: bar chart with color by etymology
ax = axes[0]
y = np.arange(len(top30))
bar_colors = [etym_colors.get(row["etymology"], PAL["gray"]) for _, row in top30.iterrows()]
ax.barh(y, top30["count"], color=bar_colors, edgecolor="white")
ax.set_yticks(y)

labels_terms = []
for term, row in top30.iterrows():
    eng = str(row["english"])[:25] if pd.notna(row["english"]) else ""
    labels_terms.append(f'{term}  ("{eng}")')
ax.set_yticklabels(labels_terms, fontsize=8.5)
ax.invert_yaxis()
ax.set_xlabel("number of occurrences")
ax.set_title("Top 30 Normalized Arabic Terms\n(color = human etymology classification)", fontsize=12)

# Legend for etymology colors
handles = [mpatches.Patch(color=etym_colors[e], label=e)
           for e in ["Arabic", "Latinised Arabic", "Persian-Arabic", "Persian",
                      "mixed", "unclear", "not specified"]
           if e in [r["etymology"] for _, r in top30.iterrows()]]
ax.legend(handles=handles, title="etymology", fontsize=8, loc="lower right")

# Annotate with validation info
for i, (term, row) in enumerate(top30.iterrows()):
    wiki_str = "W" if row["wiki"] > 0 else "·"
    emlap_str = "E" if row["emlap"] > 0 else "·"
    note_str = "N" if row["has_notes"] > 0 else "·"
    ax.text(row["count"] + 0.3, i,
            f'[{wiki_str}{emlap_str}{note_str}]  {row["verdict"]}',
            va="center", fontsize=7.5, color=PAL["darkblue"])

# Right: detailed table
ax = axes[1]
ax.axis("off")
header = f"{'Term':20s} {'Etym':16s} {'Wiki':5s} {'EMLAP':6s} {'Note':4s}\n"
header += "─" * 55 + "\n"
table_lines = []
for term, row in top30.head(25).iterrows():
    t = str(term)[:20]
    e = str(row["etymology"])[:16]
    w = "yes" if row["wiki"] > 0 else "no"
    em = "yes" if row["emlap"] > 0 else "no"
    n = "yes" if row["has_notes"] > 0 else "no"
    table_lines.append(f"{t:20s} {e:16s} {w:5s} {em:6s} {n:4s}")

ax.text(0.02, 0.95, header + "\n".join(table_lines),
        transform=ax.transAxes, fontsize=9, va="top",
        fontfamily="monospace", linespacing=1.3)
ax.set_title("Top 25 Terms: Validation Summary\n(W=Wiktionary, E=EMLAP, N=has reviewer notes)", fontsize=12)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "top_terms_context.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ top_terms_context.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 7: THE UNCERTAIN & DEBATED — CLOSE-UP ON EDGE CASES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 7: Uncertain and debated terms…")

fig, axes = plt.subplots(1, 3, figsize=(22, 9))

# Panel 1: uncertain verdict terms
ax = axes[0]
uncertain = df[df["verdict_clean"] == "UNCERTAIN"].copy()
ax.axis("off")
text = "Terms with UNCERTAIN Reviewer Verdict\n"
text += "═" * 50 + "\n\n"
for _, row in uncertain.iterrows():
    term = str(row["norm_control"])[:25]
    etym = str(row["etymology_clean"])[:20]
    note = str(row["notes"])[:60] if pd.notna(row["notes"]) else "(no note)"
    text += f"▸ {term}\n  Etymology: {etym}\n  Note: {note}\n\n"
ax.text(0.02, 0.98, text, transform=ax.transAxes, fontsize=8.5,
        va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title(f"UNCERTAIN Verdict ({len(uncertain)} terms)", fontsize=12, fontweight="bold")

# Panel 2: terms with "debated" or "unclear" in notes
ax = axes[1]
debated = df[df["notes"].str.contains("debated|unclear|edge case|origins.*debated",
                                        case=False, na=False)].copy()
ax.axis("off")
text = "Terms with Debated Origins (per notes)\n"
text += "═" * 50 + "\n\n"
for _, row in debated.iterrows():
    term = str(row["norm_control"])[:25]
    note = str(row["notes"])[:75] if pd.notna(row["notes"]) else ""
    etym = str(row["etymology_clean"])[:15]
    text += f"▸ {term} [{etym}]\n  {note}\n\n"
ax.text(0.02, 0.98, text, transform=ax.transAxes, fontsize=8,
        va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title(f"Debated/Unclear Origins ({len(debated)} terms)", fontsize=12, fontweight="bold")

# Panel 3: terms classified as mixed, unclear, or Persian
ax = axes[2]
non_arabic = df[df["etymology_clean"].isin(["mixed", "unclear", "Persian", "Persian-Arabic"])].copy()
etym_dist = non_arabic["etymology_clean"].value_counts()
colors_na = [etym_colors.get(e, PAL["gray"]) for e in etym_dist.index]
ax.pie(etym_dist.values, labels=etym_dist.index, colors=colors_na,
       autopct=lambda p: f"{p:.0f}%\n({int(p*len(non_arabic)/100)})",
       startangle=90, textprops={"fontsize": 10})
ax.set_title(f"Non-Pure-Arabic Etymologies\n({len(non_arabic)} terms)", fontsize=12, fontweight="bold")

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "uncertain_debated.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ uncertain_debated.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 8: ETYMOLOGY PATHWAYS — FROM ARABIC TO RULAND VIA NOTES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 8: Etymology pathways from notes…")

# Parse "from X" patterns in notes
def extract_source_form(note):
    """Extract the Arabic/Persian source form from a note like 'from al-kuhl'."""
    if pd.isna(note):
        return None
    note = str(note)
    m = re.search(r'from\s+([\w\-\']+(?:\s+[\w\-\']+)?)', note, re.IGNORECASE)
    if m:
        return m.group(1)
    m = re.search(r'(al-[\w]+)', note, re.IGNORECASE)
    if m:
        return m.group(1)
    return None

df["source_form"] = df["notes"].apply(extract_source_form)
has_source = df[df["source_form"].notna()].copy()

fig, axes = plt.subplots(1, 2, figsize=(20, 10))

# Left: flow diagram — source form → normalized Latin
ax = axes[0]
# Group by (source_form, norm_control) pairs
pairs = has_source.groupby(["source_form", "norm_control"]).size().reset_index(name="count")
pairs = pairs.sort_values("count", ascending=False).head(25)

y = np.arange(len(pairs))
ax.barh(y, pairs["count"], color=PAL["teal"])
labels_flow = [f'{row["source_form"]}  →  {row["norm_control"]}'
               for _, row in pairs.iterrows()]
ax.set_yticks(y)
ax.set_yticklabels(labels_flow, fontsize=9)
ax.invert_yaxis()
ax.set_xlabel("number of entries with this pathway")
ax.set_title("Arabic Source → Latin Term\n(etymological pathways documented in reviewer notes)",
             fontsize=12)
for i, v in enumerate(pairs["count"]):
    ax.text(v + 0.2, i, str(v), va="center", fontsize=9)

# Right: intermediary languages mentioned in notes
ax = axes[1]
intermediaries = {
    "Arabic direct": 0,
    "via Persian": 0,
    "via Greek": 0,
    "via Spanish": 0,
    "via French": 0,
    "via Latin adaptation": 0,
    "via German": 0,
}
for note in df["notes"].dropna():
    n = str(note).lower()
    if "persian" in n:
        intermediaries["via Persian"] += 1
    if "greek" in n:
        intermediaries["via Greek"] += 1
    if "spanish" in n:
        intermediaries["via Spanish"] += 1
    if "french" in n:
        intermediaries["via French"] += 1
    if "german" in n:
        intermediaries["via German"] += 1
    if "latin" in n and ("related" in n or "potential" in n):
        intermediaries["via Latin adaptation"] += 1
    if "al-" in n and "persian" not in n and "greek" not in n:
        intermediaries["Arabic direct"] += 1

inter_s = pd.Series(intermediaries).sort_values(ascending=True)
inter_s = inter_s[inter_s > 0]
colors_inter = [PAL["green"], PAL["purple"], PAL["teal"], PAL["orange"],
                PAL["pink"], PAL["brown"], PAL["blue"]][:len(inter_s)]
ax.barh(range(len(inter_s)), inter_s.values, color=colors_inter)
ax.set_yticks(range(len(inter_s)))
ax.set_yticklabels(inter_s.index, fontsize=10)
ax.set_xlabel("mentions in reviewer notes")
ax.set_title("Intermediary Languages in Etymology Notes\n(languages mentioned as transmission routes)",
             fontsize=12)
for i, v in enumerate(inter_s.values):
    ax.text(v + 0.3, i, str(v), va="center", fontsize=10)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "etymology_pathways.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ etymology_pathways.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 9: TERM FREQUENCY × VALIDATION CONCORDANCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 9: Validation concordance scatter…")

# For each normalized term: count, wiki match rate, emlap match rate
term_val = df.groupby("norm_control").agg(
    count=("lemma", "size"),
    wiki_pct=("wiki_clean", lambda x: 100 * (x == "yes").sum() / len(x)),
    emlap_pct=("emlap_clean", lambda x: 100 * (x == "yes_corpus").sum() / len(x)),
    etymology=("etymology_clean", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else ""),
    has_notes=("notes", lambda x: x.notna().any()),
).reset_index()

fig, ax = plt.subplots(figsize=(14, 10))

# Scatter: x = wiki match %, y = emlap match %, size = count, color = etymology
for etym_type in ["Arabic", "Latinised Arabic", "Persian-Arabic", "Persian",
                   "mixed", "unclear", "not specified"]:
    subset = term_val[term_val["etymology"] == etym_type]
    if len(subset) == 0:
        continue
    ax.scatter(subset["wiki_pct"], subset["emlap_pct"],
               s=subset["count"] * 25, alpha=0.6,
               color=etym_colors.get(etym_type, PAL["gray"]),
               edgecolors="white", linewidths=0.5,
               label=etym_type)

# Label top terms
for _, row in term_val.nlargest(15, "count").iterrows():
    ax.annotate(row["norm_control"],
                xy=(row["wiki_pct"], row["emlap_pct"]),
                fontsize=7.5, color=PAL["darkblue"],
                xytext=(5, 5), textcoords="offset points")

ax.set_xlabel("Wiktionary Arabic match rate (%)", fontsize=12)
ax.set_ylabel("EMLAP corpus match rate (%)", fontsize=12)
ax.set_title("External Validation Concordance\n(bubble size = frequency; color = etymology)",
             fontsize=13)
ax.legend(title="etymology", fontsize=9, scatterpoints=1)
ax.set_xlim(-5, 105)
ax.set_ylim(-5, 105)

# Quadrant labels
ax.text(75, 5, "In Wiktionary\nbut not EMLAP", fontsize=9, color=PAL["gray"],
        ha="center", style="italic")
ax.text(5, 75, "In EMLAP\nbut not Wiktionary", fontsize=9, color=PAL["gray"],
        ha="center", style="italic")
ax.text(75, 90, "Both sources\nconfirm", fontsize=9, color=PAL["darkgreen"],
        ha="center", style="italic")
ax.text(5, 5, "Neither source\nconfirms", fontsize=9, color=PAL["red"],
        ha="center", style="italic")

# Quadrant lines
ax.axhline(50, ls=":", color=PAL["gray"], alpha=0.3)
ax.axvline(50, ls=":", color=PAL["gray"], alpha=0.3)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "validation_concordance.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ validation_concordance.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 10: EMLAP CORPUS DEPTH — HOW WIDELY ATTESTED ARE THESE TERMS?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 10: EMLAP corpus depth…")

fig, axes = plt.subplots(1, 3, figsize=(20, 8))

# Panel 1: distribution of total occurrences
ax = axes[0]
emlap_occ = pd.to_numeric(df["emlap_total_occurrences"], errors="coerce").dropna()
bins_e = [0, 1, 5, 10, 25, 50, 100, 500, 5000]
labels_e = ["0", "1-4", "5-9", "10-24", "25-49", "50-99", "100-499", "500+"]
emlap_binned = pd.cut(emlap_occ, bins=bins_e, labels=labels_e, right=False)
bin_counts = emlap_binned.value_counts().reindex(labels_e)
ax.bar(range(len(bin_counts)), bin_counts.values, color=PAL["blue"])
ax.set_xticks(range(len(bin_counts)))
ax.set_xticklabels(labels_e, rotation=45, fontsize=9)
ax.set_xlabel("total occurrences in EMLAP corpus")
ax.set_ylabel("number of terms")
ax.set_title("EMLAP Corpus: How Often\nDo These Terms Appear?", fontsize=12)
for i, v in enumerate(bin_counts.values):
    if v > 0:
        ax.text(i, v + 1, str(int(v)), ha="center", fontsize=8)

# Panel 2: distinct works
ax = axes[1]
emlap_works = pd.to_numeric(df["emlap_distinct_works"], errors="coerce").dropna()
works_vc = emlap_works.value_counts().sort_index()
ax.bar(works_vc.index.astype(int), works_vc.values, color=PAL["teal"])
ax.set_xlabel("number of distinct works containing the term")
ax.set_ylabel("number of terms")
ax.set_title("EMLAP: In How Many\nDistinct Works?", fontsize=12)

# Panel 3: Ruland-specific occurrences
ax = axes[2]
emlap_ruland = pd.to_numeric(df["emlap_ruland_occurrences"], errors="coerce").dropna()
ruland_vc = emlap_ruland.value_counts().sort_index()
ax.bar(ruland_vc.index.astype(int), ruland_vc.values, color=PAL["orange"])
ax.set_xlabel("occurrences in Ruland specifically")
ax.set_ylabel("number of terms")
ax.set_title("EMLAP: Occurrences\nin Ruland's Text", fontsize=12)

plt.suptitle("EMLAP Early Modern Latin Corpus: Attestation Depth for Arabic-Origin Terms",
             fontsize=14, y=1.02, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "emlap_depth.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ emlap_depth.png")


print(f"\nAll done. {len(os.listdir(OUTDIR))} files in {OUTDIR}")
for f in sorted(os.listdir(OUTDIR)):
    print(f"  {f}")
