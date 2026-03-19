#!/usr/bin/env python3
"""
Ruland 1612 – EMLAP Corpus Exploration & Automated Score vs Human Verdict
==========================================================================
Two analysis threads:

1. EMLAP EXPLORATION: The EMLAP corpus contains alchemical texts printed in
   the century before Ruland (pre-1612). Where these Arabic-tradition terms
   also appear in EMLAP, we can trace their earlier textual life. Caveat:
   Arabic-tradition terms may cause search errors due to automatic
   processing/lemmatization issues in the corpus.

2. SCORE vs VERDICT: Do the automated scores (confidence_score,
   irrelevance_probability) predict what humans decided? Compare scores
   for ARABIC vs UNCERTAIN verdicts, and for included (363) vs excluded
   (565) terms.
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
from collections import Counter, defaultdict

# ── paths ───────────────────────────────────────────────────────────
TSV_PATH = "/Users/slang/Downloads/Final Single Sheet - 2026-01-27_reviewerCopy_reducedFinalSingleSheet.tsv"
CSV_RAW = "/Users/slang/Downloads/schreibProjekte-slides/narrowingdown/output_4ofixed_reviewed_with_entries.csv"
OUTDIR = "/Users/slang/claude/ruland_exploration/08_emlap_and_scores"
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
df = df.rename(columns={
    "lemma /headword": "lemma",
    "3 human reviewer comparison verdict": "verdict",
    "Include (controled vocab, y/n)": "include",
    "normalized control string (harmonized) ": "norm_control",
})
for col in ["confidence_score", "irrelevance_probability",
            "emlap_total_occurrences", "emlap_distinct_works",
            "emlap_ruland_occurrences"]:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df["verdict_clean"] = df["verdict"].str.strip().str.upper()
df["etymology_clean"] = df["Etymology"].fillna("not reviewed").str.strip()
etym_map = {
    "Arabic": "Arabic", "arabic": "Arabic",
    "Latinised Arabic": "Latinised Arabic",
    "Persian-Arabic": "Persian-Arabic",
    "Persian": "Persian", "unclear": "unclear", "mixed": "mixed",
    "not reviewed": "not reviewed",
}
df["etymology_clean"] = df["etymology_clean"].map(
    lambda x: etym_map.get(x, "other/specific"))

df["emlap_flag"] = df["emlap_match_flag"].astype(str).str.strip().str.lower()
df.loc[~df["emlap_flag"].isin(["yes_corpus", "no"]), "emlap_flag"] = "other"
df["wiki_flag"] = df["wiki_match_flag"].astype(str).str.strip().str.lower()
df.loc[~df["wiki_flag"].isin(["yes", "no", "maybe"]), "wiki_flag"] = "other"

# Raw CSV (928 rows, pre-review)
raw_df = pd.read_csv(CSV_RAW)
raw_df = raw_df.loc[:, ~raw_df.columns.str.startswith("Unnamed")]
for col in ["confidence_score", "irrelevance_probability"]:
    raw_df[col] = pd.to_numeric(raw_df[col], errors="coerce")

# The raw CSV (928 rows) and TSV (363 rows) come from different pipeline
# stages and cannot be cleanly matched row-by-row (different detected_string
# values). For the score comparison, we treat them as two populations:
# - raw_df: ALL 928 AI detections (pre-review)
# - df: the 363 that survived human review
# The ~565 excluded terms are characterized by the difference in distributions.

print(f"  TSV (included): {len(df)} terms")
print(f"  Raw CSV (all detections): {len(raw_df)}")
print(f"  Excluded (by difference): {len(raw_df) - len(df)}")

# ── Parse EMLAP evidence blocks ──────────────────────────────────
def parse_evidence(ev_str):
    """Parse EMLAP evidence block into list of (work_id, position, snippet)."""
    if pd.isna(ev_str):
        return []
    matches = re.findall(r'\[(\d+):(\d+)\]\s*([^\[]*)', str(ev_str))
    return [(int(m[0]), int(m[1]), m[2].strip().rstrip("- ")) for m in matches]

df["_evidence"] = df["emlap_evidence_block"].apply(parse_evidence)
df["_n_snippets"] = df["_evidence"].apply(len)

# Aggregate evidence by work
work_term_map = defaultdict(set)  # work_id -> set of norm_control terms
term_work_map = defaultdict(set)  # norm_control -> set of work_ids
all_snippets = []

for _, row in df.iterrows():
    for wid, pos, snippet in row["_evidence"]:
        work_term_map[wid].add(row["norm_control"])
        term_work_map[row["norm_control"]].add(wid)
        all_snippets.append({
            "work_id": wid, "position": pos, "snippet": snippet,
            "term": row["norm_control"],
            "etymology": row["etymology_clean"],
        })

snippets_df = pd.DataFrame(all_snippets) if all_snippets else pd.DataFrame()

print(f"  EMLAP: {len(work_term_map)} unique works, {len(snippets_df)} total snippets")
print(f"  Terms with EMLAP evidence: {df['_n_snippets'].gt(0).sum()}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 1: EMLAP CORPUS OVERVIEW — WHICH TERMS, WHICH WORKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 1: EMLAP corpus overview…")

fig, axes = plt.subplots(2, 2, figsize=(20, 16))

# Panel 1: Top terms by EMLAP attestation
ax = axes[0, 0]
term_occ = df.groupby("norm_control").agg(
    total_occ=("emlap_total_occurrences", "max"),
    distinct_works=("emlap_distinct_works", "max"),
    etymology=("etymology_clean", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else ""),
).dropna(subset=["total_occ"]).sort_values("total_occ", ascending=False).head(30)

etym_colors = {
    "Arabic": PAL["green"], "Latinised Arabic": PAL["teal"],
    "Persian-Arabic": PAL["purple"], "Persian": PAL["pink"],
    "mixed": PAL["orange"], "unclear": PAL["gray"],
    "not reviewed": PAL["lightblue"], "other/specific": PAL["brown"],
}
y = np.arange(len(term_occ))
colors = [etym_colors.get(e, PAL["gray"]) for e in term_occ["etymology"]]
ax.barh(y, term_occ["total_occ"], color=colors)
ax.set_yticks(y)
ax.set_yticklabels(term_occ.index, fontsize=8.5)
ax.invert_yaxis()
ax.set_xlabel("total EMLAP occurrences")
ax.set_title("Top 30 Terms by EMLAP Corpus Attestation\n(bar color = reviewer etymology)", fontsize=12)
for i, (term, row) in enumerate(term_occ.iterrows()):
    ax.text(row["total_occ"] + 0.3, i,
            f'{int(row["total_occ"])} occ, {int(row["distinct_works"])} works',
            va="center", fontsize=7.5, color=PAL["darkblue"])

# Panel 2: Distribution of distinct works per term
ax = axes[0, 1]
works_dist = df.groupby("norm_control")["emlap_distinct_works"].max().dropna()
ax.hist(works_dist, bins=range(0, int(works_dist.max()) + 2), color=PAL["teal"],
        edgecolor="white", alpha=0.85)
ax.axvline(works_dist.median(), color=PAL["red"], ls="--", lw=2,
           label=f"median = {works_dist.median():.0f} works")
ax.set_xlabel("number of distinct EMLAP works containing the term")
ax.set_ylabel("number of Arabic-tradition terms")
ax.set_title("How Widely Attested Are Arabic Terms\nin Pre-Ruland Alchemical Texts?", fontsize=12)
ax.legend(fontsize=10)
# Annotate
n_zero = (works_dist == 0).sum()
n_one = (works_dist == 1).sum()
n_many = (works_dist >= 5).sum()
ax.text(0.95, 0.95,
        f"Not in EMLAP: {n_zero} terms\n"
        f"In 1 work only: {n_one} terms\n"
        f"In 5+ works: {n_many} terms (widely attested)",
        transform=ax.transAxes, ha="right", va="top", fontsize=9,
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

# Panel 3: Top EMLAP works — which texts contain the most Arabic terms
ax = axes[1, 0]
work_richness = pd.Series({wid: len(terms) for wid, terms in work_term_map.items()})
work_richness = work_richness.sort_values(ascending=False).head(20)
y_w = np.arange(len(work_richness))
ax.barh(y_w, work_richness.values, color=PAL["blue"])
ax.set_yticks(y_w)
ax.set_yticklabels([f"Work {wid}" for wid in work_richness.index], fontsize=9)
ax.invert_yaxis()
ax.set_xlabel("number of distinct Arabic-tradition terms found")
ax.set_title("EMLAP Works with Most Arabic-Tradition Terms\n(Which pre-Ruland texts use the most Arabic vocabulary?)",
             fontsize=12)
for i, v in enumerate(work_richness.values):
    ax.text(v + 0.3, i, str(v), va="center", fontsize=9)

# Panel 4: EMLAP match rate by etymology
ax = axes[1, 1]
etym_order = ["Arabic", "Latinised Arabic", "Persian-Arabic", "Persian",
              "mixed", "unclear", "not reviewed"]
etym_order = [e for e in etym_order if e in df["etymology_clean"].values]
emlap_rates = []
counts = []
for e in etym_order:
    sub = df[df["etymology_clean"] == e]
    rate = 100 * (sub["emlap_flag"] == "yes_corpus").sum() / len(sub)
    emlap_rates.append(rate)
    counts.append(len(sub))

y_e = np.arange(len(etym_order))
colors_e = [etym_colors.get(e, PAL["gray"]) for e in etym_order]
ax.barh(y_e, emlap_rates, color=colors_e, height=0.5)
ax.set_yticks(y_e)
ax.set_yticklabels([f"{e}\n(n={c})" for e, c in zip(etym_order, counts)], fontsize=9)
ax.set_xlabel("% of terms found in EMLAP corpus")
ax.set_title("EMLAP Match Rate by Etymology\n(Are correctly-detected Arabic terms better attested?)", fontsize=12)
for i, v in enumerate(emlap_rates):
    ax.text(v + 0.5, i, f"{v:.0f}%", va="center", fontsize=10)
ax.set_xlim(0, 105)

plt.suptitle("EMLAP Corpus: Arabic-Tradition Terms in Pre-Ruland Alchemical Texts",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "emlap_overview.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ emlap_overview.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 2: EMLAP EVIDENCE — TERM CO-OCCURRENCE NETWORK
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 2: Term co-occurrence in EMLAP works…")

fig, axes = plt.subplots(1, 2, figsize=(22, 11))

# Left: which terms co-occur in the same EMLAP works?
# Build co-occurrence matrix for top terms
top_terms = list(term_occ.index[:20])
cooc = pd.DataFrame(0, index=top_terms, columns=top_terms)
for wid, terms in work_term_map.items():
    present = [t for t in top_terms if t in terms]
    for i, t1 in enumerate(present):
        for t2 in present[i+1:]:
            cooc.loc[t1, t2] += 1
            cooc.loc[t2, t1] += 1

ax = axes[0]
mask = np.triu(np.ones_like(cooc, dtype=bool), k=0)
sns.heatmap(cooc, mask=mask, cmap="YlOrRd", ax=ax, linewidths=0.5,
            annot=True, fmt="d", annot_kws={"fontsize": 7},
            cbar_kws={"label": "number of shared EMLAP works"})
ax.set_title("Term Co-Occurrence in EMLAP Works\n(How often do Arabic terms appear together?)", fontsize=12)
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=8)

# Right: which works are most "Arabic-rich" — show terms per work as treemap-like
ax = axes[1]
ax.axis("off")
# Table: top 15 works, what Arabic terms they contain
text = "Top 15 EMLAP Works by Arabic-Tradition Term Count\n"
text += "═" * 60 + "\n\n"
text += "These are pre-Ruland alchemical texts (printed before\n"
text += "1612) that contain the most Arabic-tradition vocabulary.\n"
text += "NB: search may miss terms due to lemmatization issues.\n\n"
for wid in work_richness.index[:15]:
    terms = sorted(work_term_map[wid])
    n = len(terms)
    term_str = ", ".join(terms[:8])
    if n > 8:
        term_str += f", … (+{n-8} more)"
    text += f"Work {wid}: {n} terms\n"
    text += f"  {term_str}\n\n"

ax.text(0.02, 0.98, text, transform=ax.transAxes, fontsize=9,
        va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title("Arabic Vocabulary in Individual EMLAP Works", fontsize=12)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "emlap_cooccurrence.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ emlap_cooccurrence.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 3: EMLAP EVIDENCE SNIPPETS — WHAT CONTEXTS DO THESE TERMS APPEAR IN?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 3: EMLAP evidence contexts…")

fig = plt.figure(figsize=(24, 16))

# Show sample evidence snippets for key terms
key_terms = ["alkali", "elixir", "borax", "alcohol", "alembicus",
             "arsenicum", "sal ammoniac", "tutia", "naphtha", "marcasita",
             "mumia", "colcothar"]
key_terms = [t for t in key_terms if t in term_work_map]

n_terms = len(key_terms)
gs = gridspec.GridSpec(4, 3, hspace=0.4, wspace=0.3)

for idx, term in enumerate(key_terms):
    if idx >= 12:
        break
    ax = fig.add_subplot(gs[idx // 3, idx % 3])
    ax.axis("off")

    term_rows = df[df["norm_control"] == term]
    # Collect all evidence for this term
    all_ev = []
    for _, row in term_rows.iterrows():
        all_ev.extend(row["_evidence"])

    # Deduplicate by work_id + position
    seen = set()
    unique_ev = []
    for wid, pos, snip in all_ev:
        key = (wid, pos)
        if key not in seen:
            seen.add(key)
            unique_ev.append((wid, pos, snip))

    n_works = len(set(wid for wid, _, _ in unique_ev))
    n_occ = len(unique_ev)
    etym = term_rows["etymology_clean"].mode().iloc[0] if len(term_rows) > 0 else "?"

    text = f"{term.upper()} [{etym}]\n"
    text += f"{n_occ} occurrences in {n_works} EMLAP works\n"
    text += "─" * 45 + "\n"

    # Show up to 5 snippets from different works
    shown_works = set()
    count = 0
    for wid, pos, snip in sorted(unique_ev, key=lambda x: x[0]):
        if wid in shown_works:
            continue
        shown_works.add(wid)
        # Truncate snippet
        snip_clean = snip.replace("\n", " ").strip()
        if len(snip_clean) > 120:
            snip_clean = snip_clean[:117] + "…"
        text += f"\n[{wid}] {snip_clean}\n"
        count += 1
        if count >= 4:
            remaining = n_works - count
            if remaining > 0:
                text += f"\n  … +{remaining} more works"
            break

    color = etym_colors.get(etym, PAL["gray"])
    ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=7.5,
            va="top", fontfamily="monospace", linespacing=1.2,
            bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.15))

fig.suptitle("EMLAP Evidence Snippets: Arabic Terms in Pre-Ruland Alchemical Texts\n"
             "(sample contexts from the century before Ruland's 1612 dictionary)",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "emlap_evidence_snippets.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ emlap_evidence_snippets.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 4: EMLAP ATTESTATION DEPTH vs DICTIONARY PROMINENCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 4: EMLAP attestation vs Ruland prominence…")

fig, axes = plt.subplots(1, 3, figsize=(22, 9))

# Aggregate per normalized term
term_stats = df.groupby("norm_control").agg(
    ruland_entries=("lemma", "size"),
    emlap_occ=("emlap_total_occurrences", "max"),
    emlap_works=("emlap_distinct_works", "max"),
    etymology=("etymology_clean", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else ""),
    emlap_flag=("emlap_flag", lambda x: "yes_corpus" if (x == "yes_corpus").any() else "no"),
).dropna(subset=["emlap_occ"])

# Panel 1: scatter — Ruland entries vs EMLAP occurrences
ax = axes[0]
colors_s = [etym_colors.get(e, PAL["gray"]) for e in term_stats["etymology"]]
ax.scatter(term_stats["ruland_entries"], term_stats["emlap_occ"],
           c=colors_s, alpha=0.6, s=40, edgecolors="white", linewidth=0.5)
ax.set_xlabel("entries in Ruland's dictionary containing this term")
ax.set_ylabel("total EMLAP occurrences (pre-Ruland corpus)")
ax.set_title("Dictionary Prominence vs Corpus Attestation\n(Do frequently-used terms have deeper roots?)", fontsize=12)
# Label outliers
for _, row in term_stats.nlargest(8, "ruland_entries").iterrows():
    ax.annotate(row.name, xy=(row["ruland_entries"], row["emlap_occ"]),
                fontsize=7, color=PAL["darkblue"],
                xytext=(4, 4), textcoords="offset points")
for _, row in term_stats.nlargest(5, "emlap_occ").iterrows():
    if row.name not in term_stats.nlargest(8, "ruland_entries").index:
        ax.annotate(row.name, xy=(row["ruland_entries"], row["emlap_occ"]),
                    fontsize=7, color=PAL["darkblue"],
                    xytext=(4, 4), textcoords="offset points")

# Panel 2: terms in Ruland but NOT in EMLAP
ax = axes[1]
not_in_emlap = term_stats[term_stats["emlap_occ"] == 0].sort_values("ruland_entries", ascending=False)
if len(not_in_emlap) > 0:
    show_n = min(25, len(not_in_emlap))
    y_ne = np.arange(show_n)
    ne_subset = not_in_emlap.head(show_n)
    colors_ne = [etym_colors.get(e, PAL["gray"]) for e in ne_subset["etymology"]]
    ax.barh(y_ne, ne_subset["ruland_entries"], color=colors_ne)
    ax.set_yticks(y_ne)
    labels_ne = [f"{t} [{ne_subset.loc[t, 'etymology']}]" for t in ne_subset.index]
    ax.set_yticklabels(labels_ne, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel("entries in Ruland's dictionary")
    ax.set_title(f"Terms in Ruland but NOT in EMLAP ({len(not_in_emlap)} terms)\n"
                 "(Ruland-specific or search failures?)", fontsize=12)
    ax.text(0.95, 0.95,
            "These terms appear in Ruland's\n"
            "dictionary but were not found\n"
            "in the pre-Ruland EMLAP corpus.\n\n"
            "Possible reasons:\n"
            "• Genuinely new to Ruland\n"
            "• Spelling too variable for\n"
            "  automated search to match\n"
            "• Lemmatization issues with\n"
            "  Arabic-tradition terms",
            transform=ax.transAxes, ha="right", va="top", fontsize=8,
            bbox=dict(boxstyle="round", facecolor=PAL["lightblue"], alpha=0.3))
else:
    ax.axis("off")
    ax.text(0.5, 0.5, "All terms found in EMLAP", transform=ax.transAxes,
            ha="center", va="center", fontsize=14)

# Panel 3: terms in EMLAP but appearing in only 1 work
ax = axes[2]
single_work = term_stats[(term_stats["emlap_works"] == 1) & (term_stats["emlap_occ"] > 0)]
single_work = single_work.sort_values("emlap_occ", ascending=False)
if len(single_work) > 0:
    show_n = min(25, len(single_work))
    sw_subset = single_work.head(show_n)
    y_sw = np.arange(show_n)
    colors_sw = [etym_colors.get(e, PAL["gray"]) for e in sw_subset["etymology"]]
    ax.barh(y_sw, sw_subset["emlap_occ"], color=colors_sw)
    ax.set_yticks(y_sw)
    labels_sw = [f"{t} [{sw_subset.loc[t, 'etymology']}]" for t in sw_subset.index]
    ax.set_yticklabels(labels_sw, fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel("total EMLAP occurrences (all from 1 work)")
    ax.set_title(f"Terms Found in Only 1 EMLAP Work ({len(single_work)} terms)\n"
                 "(Narrowly attested — single-source evidence)", fontsize=12)
else:
    ax.axis("off")

plt.suptitle("EMLAP Attestation Depth vs Ruland's Dictionary",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "emlap_vs_ruland.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ emlap_vs_ruland.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 5: EMLAP TERMS WITH POSSIBLE SEARCH ISSUES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 5: EMLAP search quality issues…")

fig, axes = plt.subplots(2, 2, figsize=(20, 16))

# Panel 1: EMLAP occurrences distribution — the suspicious "15" spike
ax = axes[0, 0]
occ_vals = df.groupby("norm_control")["emlap_total_occurrences"].max().dropna()
occ_hist = occ_vals.value_counts().sort_index()
ax.bar(occ_hist.index, occ_hist.values, color=PAL["teal"], width=0.8)
ax.set_xlabel("total EMLAP occurrences")
ax.set_ylabel("number of terms with this count")
ax.set_title("Distribution of EMLAP Occurrence Counts\n(Note the spike at 15 — possible search cap?)", fontsize=12)
# Highlight the 15 spike
if 15 in occ_hist.index:
    ax.bar([15], [occ_hist[15]], color=PAL["red"], width=0.8)
    ax.annotate(f"n={occ_hist[15]} terms\nat exactly 15",
                xy=(15, occ_hist[15]), xytext=(20, occ_hist[15] + 2),
                arrowprops=dict(arrowstyle="->", color=PAL["red"]),
                fontsize=10, color=PAL["red"])
# Also check 30, 45 (multiples of 15)
for val in [30, 45]:
    if val in occ_hist.index and occ_hist[val] > 2:
        ax.bar([val], [occ_hist[val]], color=PAL["orange"], width=0.8)

ax.text(0.95, 0.7,
        "If many terms have exactly 15\n"
        "occurrences, this likely reflects\n"
        "a search result cap (max 15\n"
        "results returned per query)\n"
        "rather than a true count.\n\n"
        "Terms at 30 or 45 may have\n"
        "multiple spelling variants,\n"
        "each capped at 15.",
        transform=ax.transAxes, ha="right", va="top", fontsize=8.5,
        bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8))

# Panel 2: Do terms with more spelling variants get more EMLAP hits?
ax = axes[0, 1]
variant_counts = df.groupby("norm_control").agg(
    n_spellings=("detected_string", "nunique"),
    emlap_occ=("emlap_total_occurrences", "max"),
    emlap_works=("emlap_distinct_works", "max"),
).dropna()
ax.scatter(variant_counts["n_spellings"], variant_counts["emlap_occ"],
           alpha=0.5, s=30, color=PAL["blue"])
ax.set_xlabel("number of spelling variants in Ruland")
ax.set_ylabel("total EMLAP occurrences")
ax.set_title("Spelling Variants vs EMLAP Attestation\n(More spellings = more EMLAP hits? Or just more chances to match?)",
             fontsize=12)
# Label outliers
for _, row in variant_counts.nlargest(5, "n_spellings").iterrows():
    ax.annotate(row.name, xy=(row["n_spellings"], row["emlap_occ"]),
                fontsize=7, color=PAL["darkblue"],
                xytext=(4, 4), textcoords="offset points")

# Panel 3: EMLAP ruland_occurrences — are any of these terms in Ruland within EMLAP?
ax = axes[1, 0]
rul_occ = df.groupby("norm_control")["emlap_ruland_occurrences"].max().dropna()
has_ruland = rul_occ[rul_occ > 0]
ax.axis("off")
text = "Terms Also Found in Ruland Within EMLAP\n"
text += "═" * 50 + "\n\n"
if len(has_ruland) > 0:
    text += "The EMLAP corpus includes Ruland's dictionary\n"
    text += "itself. These terms were found in the Ruland\n"
    text += "portion of EMLAP:\n\n"
    for term, cnt in has_ruland.sort_values(ascending=False).items():
        text += f"  {str(term):25s} {int(cnt)} Ruland occurrences\n"
    text += f"\nBut {len(rul_occ) - len(has_ruland)} of {len(rul_occ)} terms have\n"
    text += "0 Ruland-in-EMLAP occurrences, meaning most\n"
    text += "EMLAP evidence comes from OTHER texts.\n"
else:
    text += f"All {len(rul_occ)} terms show 0 Ruland occurrences\n"
    text += "in EMLAP, or nearly all — meaning EMLAP evidence\n"
    text += "comes from texts OTHER than Ruland's dictionary.\n\n"
    text += "This confirms EMLAP provides genuinely\n"
    text += "independent attestation from pre-Ruland sources.\n\n"
    text += "(However, note that 'ruland_occurrences=0' for\n"
    text += " almost all terms may also mean Ruland was not\n"
    text += " included in this version of the EMLAP corpus,\n"
    text += " or that the search did not match Ruland's\n"
    text += " specific spellings.)"
ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9.5,
        va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title("Ruland Within EMLAP", fontsize=12)

# Panel 4: terms NOT in EMLAP — are these data quality issues?
ax = axes[1, 1]
no_emlap = df[df["emlap_flag"] != "yes_corpus"].copy()
no_emlap_terms = no_emlap.groupby("norm_control").agg(
    count=("lemma", "size"),
    etymology=("etymology_clean", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else ""),
    confidence=("confidence_score", "mean"),
    wiki_match=("wiki_flag", lambda x: "yes" if (x == "yes").any() else "no"),
).sort_values("count", ascending=False)

if len(no_emlap_terms) > 0:
    text2 = f"Terms NOT Found in EMLAP ({len(no_emlap_terms)} unique terms)\n"
    text2 += "═" * 55 + "\n\n"
    text2 += "Could be: genuinely absent, spelling mismatch,\n"
    text2 += "or lemmatization failure for Arabic forms.\n\n"
    for term, row in no_emlap_terms.head(20).iterrows():
        wiki = "W✓" if row["wiki_match"] == "yes" else "W·"
        text2 += f"  {str(term):22s} [{row['etymology']:15s}] {wiki} conf={row['confidence']:.2f}\n"
    if len(no_emlap_terms) > 20:
        text2 += f"\n  … +{len(no_emlap_terms)-20} more terms"
    ax.axis("off")
    ax.text(0.02, 0.95, text2, transform=ax.transAxes, fontsize=8.5,
            va="top", fontfamily="monospace", linespacing=1.2)
    ax.set_title("EMLAP Search Gaps", fontsize=12)
else:
    ax.axis("off")
    ax.text(0.5, 0.5, "All terms found in EMLAP", transform=ax.transAxes,
            ha="center", va="center")

plt.suptitle("EMLAP Data Quality: Search Caps, Spelling Issues & Gaps",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "emlap_quality.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ emlap_quality.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 6: AUTOMATED SCORES vs HUMAN VERDICT — INCLUDED TERMS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 6: Automated scores vs human verdict (included terms)…")

fig, axes = plt.subplots(2, 3, figsize=(22, 14))

# Panel 1: Confidence score distribution by verdict
ax = axes[0, 0]
arabic_conf = df[df["verdict_clean"] == "ARABIC"]["confidence_score"].dropna()
uncertain_conf = df[df["verdict_clean"] == "UNCERTAIN"]["confidence_score"].dropna()
bins_c = np.arange(0.55, 1.05, 0.05)
ax.hist(arabic_conf, bins=bins_c, alpha=0.7, color=PAL["green"], label=f"ARABIC (n={len(arabic_conf)})",
        edgecolor="white")
ax.hist(uncertain_conf, bins=bins_c, alpha=0.8, color=PAL["red"], label=f"UNCERTAIN (n={len(uncertain_conf)})",
        edgecolor="white")
ax.set_xlabel("confidence score")
ax.set_ylabel("count")
ax.set_title("Confidence Score by Verdict\n(ARABIC vs UNCERTAIN)", fontsize=12)
ax.legend(fontsize=9)
ax.axvline(arabic_conf.median(), color=PAL["green"], ls="--", lw=1.5, alpha=0.7)
ax.axvline(uncertain_conf.median(), color=PAL["red"], ls="--", lw=1.5, alpha=0.7)

# Panel 2: Irrelevance probability by verdict
ax = axes[0, 1]
arabic_irr = df[df["verdict_clean"] == "ARABIC"]["irrelevance_probability"].dropna()
uncertain_irr = df[df["verdict_clean"] == "UNCERTAIN"]["irrelevance_probability"].dropna()
bins_i = np.arange(-0.025, 1.05, 0.05)
ax.hist(arabic_irr, bins=bins_i, alpha=0.7, color=PAL["green"], label=f"ARABIC (n={len(arabic_irr)})",
        edgecolor="white")
ax.hist(uncertain_irr, bins=bins_i, alpha=0.8, color=PAL["red"], label=f"UNCERTAIN (n={len(uncertain_irr)})",
        edgecolor="white")
ax.set_xlabel("irrelevance probability")
ax.set_ylabel("count")
ax.set_title("Irrelevance Score by Verdict\n(ARABIC vs UNCERTAIN)", fontsize=12)
ax.legend(fontsize=9)

# Panel 3: summary statistics
ax = axes[0, 2]
ax.axis("off")
text = "Automated Scores vs Human Verdict\n"
text += "═" * 50 + "\n\n"
text += "                    ARABIC       UNCERTAIN\n"
text += f"  n                 {len(arabic_conf):>5d}          {len(uncertain_conf):>5d}\n"
text += f"  conf mean         {arabic_conf.mean():>5.3f}          {uncertain_conf.mean():>5.3f}\n"
text += f"  conf median       {arabic_conf.median():>5.3f}          {uncertain_conf.median():>5.3f}\n"
text += f"  conf std          {arabic_conf.std():>5.3f}          {uncertain_conf.std():>5.3f}\n"
text += f"  conf min          {arabic_conf.min():>5.3f}          {uncertain_conf.min():>5.3f}\n\n"
text += f"  irr mean          {arabic_irr.mean():>5.3f}          {uncertain_irr.mean():>5.3f}\n"
text += f"  irr median        {arabic_irr.median():>5.3f}          {uncertain_irr.median():>5.3f}\n"
text += f"  irr std           {arabic_irr.std():>5.3f}          {uncertain_irr.std():>5.3f}\n\n"
text += "Key finding:\n"
text += "  UNCERTAIN terms have LOWER confidence\n"
text += f"  (mean {uncertain_conf.mean():.3f} vs {arabic_conf.mean():.3f})\n"
text += "  and HIGHER irrelevance scores\n"
text += f"  (mean {uncertain_irr.mean():.3f} vs {arabic_irr.mean():.3f})\n\n"
text += "  → The AI's own uncertainty signals\n"
text += "    partially predict human disagreement."
ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9.5,
        va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title("Summary", fontsize=12)

# Panel 4: 2D scatter — confidence vs irrelevance, colored by verdict
ax = axes[1, 0]
for v, color, label in [("ARABIC", PAL["green"], "ARABIC"),
                         ("UNCERTAIN", PAL["red"], "UNCERTAIN")]:
    sub = df[df["verdict_clean"] == v]
    ax.scatter(sub["confidence_score"], sub["irrelevance_probability"],
               c=color, alpha=0.5, s=25, label=label, edgecolors="white", linewidth=0.3)
ax.set_xlabel("confidence score")
ax.set_ylabel("irrelevance probability")
ax.set_title("Confidence × Irrelevance by Verdict\n(Can the two scores together predict the verdict?)", fontsize=12)
ax.legend(fontsize=9)
# Draw "danger zone" box
ax.axhline(0.5, color=PAL["gray"], ls=":", alpha=0.5)
ax.axvline(0.75, color=PAL["gray"], ls=":", alpha=0.5)
ax.text(0.62, 0.92, "low conf +\nhigh irr →\nmore likely\nUNCERTAIN",
        fontsize=7.5, color=PAL["red"], ha="center",
        transform=ax.transAxes)

# Panel 5: Confidence vs irrelevance colored by etymology
ax = axes[1, 1]
for etym in ["Arabic", "Latinised Arabic", "Persian-Arabic", "mixed", "unclear", "not reviewed"]:
    sub = df[df["etymology_clean"] == etym]
    if len(sub) > 0:
        ax.scatter(sub["confidence_score"], sub["irrelevance_probability"],
                   c=etym_colors.get(etym, PAL["gray"]), alpha=0.5, s=25,
                   label=etym, edgecolors="white", linewidth=0.3)
ax.set_xlabel("confidence score")
ax.set_ylabel("irrelevance probability")
ax.set_title("Confidence × Irrelevance by Etymology\n(Do non-Arabic terms cluster differently?)", fontsize=12)
ax.legend(fontsize=8, loc="upper left")

# Panel 6: ROC-like analysis — at what thresholds would you catch UNCERTAIN?
ax = axes[1, 2]
# For different confidence thresholds, what % of UNCERTAIN would you flag?
thresholds_c = np.arange(0.5, 1.01, 0.05)
uncertain_flagged_c = [100 * (uncertain_conf <= t).sum() / len(uncertain_conf) for t in thresholds_c]
arabic_flagged_c = [100 * (arabic_conf <= t).sum() / len(arabic_conf) for t in thresholds_c]
ax.plot(thresholds_c, uncertain_flagged_c, 'o-', color=PAL["red"],
        label="% UNCERTAIN caught", lw=2)
ax.plot(thresholds_c, arabic_flagged_c, 's-', color=PAL["green"],
        label="% ARABIC also caught (false alarms)", lw=2)
ax.set_xlabel("confidence threshold (flag if ≤ threshold)")
ax.set_ylabel("% of terms flagged")
ax.set_title("Threshold Analysis: Catching UNCERTAIN Verdicts\n"
             "(At what confidence cutoff do you catch uncertain cases?)", fontsize=12)
ax.legend(fontsize=9)
ax.set_ylim(0, 105)

plt.suptitle("Do Automated Scores Predict Human Verdicts?",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "scores_vs_verdict.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ scores_vs_verdict.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 7: AUTOMATED SCORES — INCLUDED vs EXCLUDED (928 → 363)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 7: Included vs excluded scores…")

fig, axes = plt.subplots(2, 2, figsize=(18, 14))

# Compare two POPULATIONS: all 928 raw detections vs the 363 included
# (we cannot match rows 1-to-1 due to different pipeline stages)
all_raw = raw_df
included = df  # the 363 included terms

# Panel 1: confidence distribution — all raw vs included
ax = axes[0, 0]
bins_c2 = np.arange(0.05, 1.05, 0.05)
ax.hist(all_raw["confidence_score"].dropna(), bins=bins_c2, alpha=0.5,
        color=PAL["blue"], label=f"All detections (n={len(all_raw)})", density=True, edgecolor="white")
ax.hist(included["confidence_score"].dropna(), bins=bins_c2, alpha=0.6,
        color=PAL["green"], label=f"Included after review (n={len(included)})", density=True, edgecolor="white")
ax.set_xlabel("confidence score")
ax.set_ylabel("density")
ax.set_title("Confidence Score: All Detections vs Included\n(Does confidence predict human inclusion?)", fontsize=12)
ax.legend(fontsize=10)
# Mark means
ax.axvline(all_raw["confidence_score"].mean(), color=PAL["blue"], ls="--", lw=1.5, alpha=0.7)
ax.axvline(included["confidence_score"].mean(), color=PAL["green"], ls="--", lw=1.5, alpha=0.7)

# Panel 2: irrelevance distribution — all raw vs included
ax = axes[0, 1]
ax.hist(all_raw["irrelevance_probability"].dropna(), bins=bins_i, alpha=0.5,
        color=PAL["blue"], label="All detections", density=True, edgecolor="white")
ax.hist(included["irrelevance_probability"].dropna(), bins=bins_i, alpha=0.6,
        color=PAL["green"], label="Included", density=True, edgecolor="white")
ax.set_xlabel("irrelevance probability")
ax.set_ylabel("density")
ax.set_title("Irrelevance Score: All Detections vs Included\n(Does irrelevance predict human exclusion?)", fontsize=12)
ax.legend(fontsize=10)

# Panel 3: 2D scatter — all raw (blue) with included overlay (green)
ax = axes[1, 0]
ax.scatter(all_raw["confidence_score"], all_raw["irrelevance_probability"],
           c=PAL["blue"], alpha=0.2, s=12, label=f"All 928 detections")
ax.scatter(included["confidence_score"], included["irrelevance_probability"],
           c=PAL["green"], alpha=0.4, s=18, label=f"363 included",
           edgecolors="white", linewidth=0.3)
ax.set_xlabel("confidence score")
ax.set_ylabel("irrelevance probability")
ax.set_title("Confidence × Irrelevance: All vs Included\n(Where in score-space do included terms cluster?)", fontsize=12)
ax.legend(fontsize=9)

# Panel 4: summary comparison
ax = axes[1, 1]
ax.axis("off")
raw_conf = all_raw["confidence_score"].dropna()
raw_irr = all_raw["irrelevance_probability"].dropna()
incl_conf = included["confidence_score"].dropna()
incl_irr = included["irrelevance_probability"].dropna()

text = "Score Comparison: All Detections vs Included\n"
text += "═" * 50 + "\n\n"
text += "                      All 928     Included 363\n"
text += f"  conf mean           {raw_conf.mean():>6.3f}       {incl_conf.mean():>6.3f}\n"
text += f"  conf median         {raw_conf.median():>6.3f}       {incl_conf.median():>6.3f}\n"
text += f"  conf std            {raw_conf.std():>6.3f}       {incl_conf.std():>6.3f}\n"
text += f"  conf min            {raw_conf.min():>6.3f}       {incl_conf.min():>6.3f}\n\n"
text += f"  irr mean            {raw_irr.mean():>6.3f}       {incl_irr.mean():>6.3f}\n"
text += f"  irr median          {raw_irr.median():>6.3f}       {incl_irr.median():>6.3f}\n"
text += f"  irr std             {raw_irr.std():>6.3f}       {incl_irr.std():>6.3f}\n\n"
text += "Key findings:\n"
if incl_conf.mean() > raw_conf.mean():
    text += f"  • Included terms have HIGHER confidence\n"
    text += f"    ({incl_conf.mean():.3f} vs {raw_conf.mean():.3f})\n"
else:
    text += f"  • Included terms have LOWER confidence\n"
    text += f"    ({incl_conf.mean():.3f} vs {raw_conf.mean():.3f})\n"
if incl_irr.mean() < raw_irr.mean():
    text += f"  • Included terms have LOWER irrelevance\n"
    text += f"    ({incl_irr.mean():.3f} vs {raw_irr.mean():.3f})\n"
else:
    text += f"  • Included terms have HIGHER irrelevance\n"
    text += f"    ({incl_irr.mean():.3f} vs {raw_irr.mean():.3f})\n"
text += "\nNote: The raw CSV and TSV come from\n"
text += "different pipeline stages, so this is\n"
text += "a population comparison, not row-level\n"
text += "matching. The excluded ~565 terms are\n"
text += "characterized by the difference."
ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9.5,
        va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title("Summary", fontsize=12)

plt.suptitle("Automated Scores vs Human Inclusion Decision (928 → 363)",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "scores_vs_inclusion.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ scores_vs_inclusion.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 8: COMBINED VIEW — SCORES, VERDICT, ETYMOLOGY, EMLAP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 8: Combined score-verdict-EMLAP view…")

fig, axes = plt.subplots(2, 2, figsize=(20, 16))

# Panel 1: Does EMLAP attestation correlate with human confidence in the verdict?
ax = axes[0, 0]
df["_has_emlap"] = df["emlap_flag"] == "yes_corpus"
df["_has_wiki"] = df["wiki_flag"] == "yes"

for flag_val, color, label, offset in [
    (True, PAL["green"], "In EMLAP", -0.15),
    (False, PAL["red"], "Not in EMLAP", 0.15),
]:
    sub = df[df["_has_emlap"] == flag_val]
    by_verdict = sub["verdict_clean"].value_counts()
    by_verdict = by_verdict.reindex(["ARABIC", "UNCERTAIN"]).fillna(0)
    x = np.arange(len(by_verdict))
    ax.bar(x + offset, by_verdict.values, 0.3, color=color, label=label)
    for i, v in enumerate(by_verdict.values):
        ax.text(i + offset, v + 1, str(int(v)), ha="center", fontsize=9)

ax.set_xticks(range(2))
ax.set_xticklabels(["ARABIC", "UNCERTAIN"], fontsize=11)
ax.set_ylabel("number of terms")
ax.set_title("EMLAP Attestation × Human Verdict\n(Are externally-attested terms more likely ARABIC?)", fontsize=12)
ax.legend(fontsize=10)

# Panel 2: EMLAP attestation × confidence score
ax = axes[0, 1]
for flag_val, color, label in [
    (True, PAL["green"], "In EMLAP"),
    (False, PAL["red"], "Not in EMLAP"),
]:
    sub = df[df["_has_emlap"] == flag_val]
    ax.hist(sub["confidence_score"].dropna(), bins=bins_c, alpha=0.6,
            color=color, label=f"{label} (n={len(sub)})", edgecolor="white")
ax.set_xlabel("confidence score")
ax.set_ylabel("count")
ax.set_title("Confidence Score × EMLAP Attestation\n(Do externally-attested terms have higher confidence?)", fontsize=12)
ax.legend(fontsize=9)

# Panel 3: score quadrants — categorize all 363 terms
ax = axes[1, 0]
# Define quadrants: high conf + low irr = good; low conf + high irr = bad
df["_conf_high"] = df["confidence_score"] >= 0.85
df["_irr_low"] = df["irrelevance_probability"] <= 0.3
quadrant_labels = {
    (True, True): "High conf, Low irr\n(strong signal)",
    (True, False): "High conf, High irr\n(mixed signal)",
    (False, True): "Low conf, Low irr\n(weak but not irrelevant)",
    (False, False): "Low conf, High irr\n(weak signal)",
}
df["_quadrant"] = df.apply(lambda r: quadrant_labels.get(
    (r["_conf_high"], r["_irr_low"]), "unknown"), axis=1)
quad_counts = df["_quadrant"].value_counts()
quad_colors = {
    "High conf, Low irr\n(strong signal)": PAL["green"],
    "High conf, High irr\n(mixed signal)": PAL["orange"],
    "Low conf, Low irr\n(weak but not irrelevant)": PAL["teal"],
    "Low conf, High irr\n(weak signal)": PAL["red"],
}
colors_qd = [quad_colors.get(q, PAL["gray"]) for q in quad_counts.index]
ax.barh(range(len(quad_counts)), quad_counts.values, color=colors_qd, height=0.5)
ax.set_yticks(range(len(quad_counts)))
ax.set_yticklabels(quad_counts.index, fontsize=10)
ax.set_xlabel("number of included terms")
ax.set_title("Score Quadrants Among Included Terms\n(conf ≥ 0.85 = 'high'; irr ≤ 0.3 = 'low')", fontsize=12)
for i, v in enumerate(quad_counts.values):
    # Also show % Arabic verdict in this quadrant
    qname = quad_counts.index[i]
    sub = df[df["_quadrant"] == qname]
    pct_arabic = 100 * (sub["verdict_clean"] == "ARABIC").sum() / len(sub)
    ax.text(v + 1, i, f"{v} ({pct_arabic:.0f}% ARABIC)", va="center", fontsize=9)

# Panel 4: summary — what have we learned about score-verdict relationship?
ax = axes[1, 1]
ax.axis("off")
text = "Summary: Do Automated Scores Predict Human Decisions?\n"
text += "═" * 55 + "\n\n"

# Compute some stats
all_conf_mean = raw_df["confidence_score"].mean()
incl_conf_mean = df["confidence_score"].mean()
all_irr_mean = raw_df["irrelevance_probability"].mean()
incl_irr_mean = df["irrelevance_probability"].mean()

text += "1. INCLUSION (928 → 363):\n"
text += f"   All 928:  conf={all_conf_mean:.3f}, irr={all_irr_mean:.3f}\n"
text += f"   Incl 363: conf={incl_conf_mean:.3f}, irr={incl_irr_mean:.3f}\n"
text += f"   → Included terms have {'HIGHER' if incl_conf_mean > all_conf_mean else 'LOWER'} confidence\n"
text += f"     and {'LOWER' if incl_irr_mean < all_irr_mean else 'HIGHER'} irrelevance\n"
text += f"   → Scores ARE partially predictive of inclusion\n\n"

text += "2. VERDICT (ARABIC vs UNCERTAIN):\n"
text += f"   ARABIC:    conf={arabic_conf.mean():.3f}, irr={arabic_irr.mean():.3f}\n"
text += f"   UNCERTAIN: conf={uncertain_conf.mean():.3f}, irr={uncertain_irr.mean():.3f}\n"
text += f"   → UNCERTAIN terms have notably LOWER confidence\n"
text += f"     and HIGHER irrelevance — the AI 'knows'\n"
text += f"     when humans will disagree\n\n"

text += "3. EMLAP ATTESTATION:\n"
emlap_yes_conf = df[df["_has_emlap"]]["confidence_score"].mean()
emlap_no_conf = df[~df["_has_emlap"]]["confidence_score"].mean()
text += f"   In EMLAP:     conf={emlap_yes_conf:.3f}\n"
text += f"   Not in EMLAP: conf={emlap_no_conf:.3f}\n"
text += f"   → EMLAP-attested terms have slightly\n"
text += f"     {'higher' if emlap_yes_conf > emlap_no_conf else 'lower'} confidence\n\n"

text += "4. PRACTICAL IMPLICATION:\n"
text += "   The irrelevance score is the strongest\n"
text += "   predictor. A threshold of irr > 0.5 would\n"
n_uncertain_caught = (uncertain_irr > 0.5).sum()
n_arabic_caught = (arabic_irr > 0.5).sum()
text += f"   catch {n_uncertain_caught}/{len(uncertain_irr)} UNCERTAIN terms\n"
text += f"   but also flag {n_arabic_caught}/{len(arabic_irr)} ARABIC terms\n"
text += f"   ({100*n_arabic_caught/len(arabic_irr):.0f}% false alarm rate)"

ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9,
        va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title("Overall Assessment", fontsize=12)

plt.suptitle("Automated Scores, Human Verdicts, and External Validation",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "combined_assessment.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ combined_assessment.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DONE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print(f"\nAll done. Files in {OUTDIR}")
for f in sorted(os.listdir(OUTDIR)):
    print(f"  {f}")
