#!/usr/bin/env python3
"""
Ruland 1612 – EMLAP Corpus Exploration v2 (with metadata)
==========================================================
Now using EMLAP metadata (author, title, date, place, genre) to make
the corpus evidence interpretable. Also includes automated score vs
human verdict analysis.

EMLAP = Early Modern Latin Alchemical Prints — 100 texts (1515–1648)
from the century before and around Ruland's 1612 dictionary.
"""

import os, re, textwrap, json
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
META_PATH = "/Users/slang/Downloads/emlap_metadata.csv"
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
etym_colors = {
    "Arabic": PAL["green"], "Latinised Arabic": PAL["teal"],
    "Persian-Arabic": PAL["purple"], "Persian": PAL["pink"],
    "mixed": PAL["orange"], "unclear": PAL["gray"],
    "not reviewed": PAL["lightblue"], "other/specific": PAL["brown"],
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

# EMLAP metadata
meta = pd.read_csv(META_PATH, sep=";")
meta_lookup = {}
for _, row in meta.iterrows():
    wid = row["no."]
    author = str(row["author_name"]) if pd.notna(row["author_name"]) else "Anon."
    if author == "nan":
        author = "Anon."
    # Shorten author to surname
    surname = author.split(",")[0].strip() if "," in author else author.split()[-1] if " " in author else author
    meta_lookup[wid] = {
        "author": author,
        "surname": surname,
        "title": str(row["title_short"]) if pd.notna(row["title_short"]) else "untitled",
        "date": int(row["date_publication"]) if pd.notna(row["date_publication"]) else None,
        "place": str(row["place_publication"]) if pd.notna(row["place_publication"]) else "unknown",
        "genre": str(row["genre"]) if pd.notna(row["genre"]) else "",
        "subject": str(row["subject"]) if pd.notna(row["subject"]) else "",
        "tokens": int(row["tokens_N"]) if pd.notna(row["tokens_N"]) else 0,
        "is_compendium": bool(row["is_compendium"]) if pd.notna(row["is_compendium"]) else False,
        "working_title": str(row["working_title"]) if pd.notna(row["working_title"]) else "",
    }

def work_label(wid, short=False):
    """Human-readable label for an EMLAP work."""
    m = meta_lookup.get(wid, {})
    if not m:
        return f"Work {wid}"
    if short:
        return f"{m['surname']} ({m['date']})"
    return f"{m['surname']}, {m['title'][:30]} ({m['date']}, {m['place']})"

# Raw CSV
raw_df = pd.read_csv(CSV_RAW)
raw_df = raw_df.loc[:, ~raw_df.columns.str.startswith("Unnamed")]
for col in ["confidence_score", "irrelevance_probability"]:
    raw_df[col] = pd.to_numeric(raw_df[col], errors="coerce")

# ── Parse EMLAP evidence blocks ──────────────────────────────────
def parse_evidence(ev_str):
    if pd.isna(ev_str):
        return []
    matches = re.findall(r'\[(\d+):(\d+)\]\s*([^\[]*)', str(ev_str))
    return [(int(m[0]), int(m[1]), m[2].strip().rstrip("- ")) for m in matches]

df["_evidence"] = df["emlap_evidence_block"].apply(parse_evidence)
df["_n_snippets"] = df["_evidence"].apply(len)

# Aggregate evidence by work
work_term_map = defaultdict(set)
term_work_map = defaultdict(set)
all_snippets = []

for _, row in df.iterrows():
    for wid, pos, snippet in row["_evidence"]:
        work_term_map[wid].add(row["norm_control"])
        term_work_map[row["norm_control"]].add(wid)
        all_snippets.append({
            "work_id": wid, "position": pos, "snippet": snippet,
            "term": row["norm_control"], "etymology": row["etymology_clean"],
        })

snippets_df = pd.DataFrame(all_snippets) if all_snippets else pd.DataFrame()

print(f"  TSV: {len(df)} terms, EMLAP metadata: {len(meta)} works")
print(f"  EMLAP evidence: {len(work_term_map)} works referenced, {len(snippets_df)} snippets")
print(f"  Terms with EMLAP evidence: {df['_n_snippets'].gt(0).sum()}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 1: WHICH PRE-RULAND TEXTS CONTAIN ARABIC VOCABULARY?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 1: EMLAP works with Arabic vocabulary…")

fig, axes = plt.subplots(2, 2, figsize=(22, 16))

# Panel 1: Top 25 works by number of distinct Arabic terms
ax = axes[0, 0]
work_richness = pd.Series({wid: len(terms) for wid, terms in work_term_map.items()})
work_richness = work_richness.sort_values(ascending=False).head(25)
y = np.arange(len(work_richness))
# Color by date
dates_w = [meta_lookup.get(wid, {}).get("date", 1580) for wid in work_richness.index]
date_norm = plt.Normalize(1510, 1650)
cmap = plt.cm.RdYlGn_r  # early=green, late=red
colors_w = [cmap(date_norm(d)) for d in dates_w]
bars = ax.barh(y, work_richness.values, color=colors_w)
ax.set_yticks(y)
labels_w = [work_label(wid) for wid in work_richness.index]
ax.set_yticklabels(labels_w, fontsize=8)
ax.invert_yaxis()
ax.set_xlabel("distinct Arabic-tradition terms found")
ax.set_title("Top 25 EMLAP Works by Arabic Vocabulary Richness\n(color = publication date: green=early, red=late)",
             fontsize=11)
for i, (wid, v) in enumerate(work_richness.items()):
    m = meta_lookup.get(wid, {})
    genre = m.get("genre", "")[:15]
    ax.text(v + 0.3, i, f"{v} terms [{genre}]", va="center", fontsize=7.5)
# Colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=date_norm)
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, shrink=0.5, pad=0.02)
cbar.set_label("publication date", fontsize=9)

# Panel 2: EMLAP works on a timeline — when were these texts published?
ax = axes[0, 1]
# All 100 EMLAP works as dots; those containing Arabic terms highlighted
all_dates = meta["date_publication"].values
all_tokens = meta["tokens_N"].values
has_arabic = [wid in work_term_map for wid in meta["no."]]
n_arabic_terms = [len(work_term_map.get(wid, set())) for wid in meta["no."]]

ax.scatter(all_dates[~np.array(has_arabic)],
           all_tokens[~np.array(has_arabic)] / 1000,
           c=PAL["gray"], alpha=0.4, s=30, label="no Arabic terms found")
scatter = ax.scatter(np.array(all_dates)[has_arabic],
                     np.array(all_tokens)[has_arabic] / 1000,
                     c=np.array(n_arabic_terms)[has_arabic],
                     cmap="YlOrRd", alpha=0.7, s=60, edgecolors="black",
                     linewidth=0.5, label="contains Arabic terms",
                     vmin=1, vmax=50)
ax.set_xlabel("publication date")
ax.set_ylabel("text size (thousands of tokens)")
ax.set_title("EMLAP Corpus Timeline\n(bubble color = number of Arabic terms found)", fontsize=11)
ax.legend(fontsize=9, loc="upper left")
plt.colorbar(scatter, ax=ax, shrink=0.5, label="Arabic terms")
# Label top works
for wid in work_richness.index[:5]:
    m = meta_lookup.get(wid, {})
    idx = list(meta["no."]).index(wid)
    ax.annotate(f"{m['surname']}\n({m['date']})",
                xy=(m["date"], m["tokens"] / 1000),
                fontsize=7, color=PAL["darkblue"],
                xytext=(5, 5), textcoords="offset points")

# Panel 3: Publication places of EMLAP works containing Arabic terms
ax = axes[1, 0]
places = [meta_lookup.get(wid, {}).get("place", "unknown") for wid in work_term_map.keys()]
place_counts = Counter(places)
place_s = pd.Series(place_counts).sort_values(ascending=True)
# Also count Arabic terms per place
place_terms = defaultdict(set)
for wid, terms in work_term_map.items():
    place = meta_lookup.get(wid, {}).get("place", "unknown")
    place_terms[place].update(terms)
place_n_terms = pd.Series({p: len(t) for p, t in place_terms.items()})

y_p = np.arange(len(place_s))
ax.barh(y_p, place_s.values, color=PAL["blue"], height=0.4, label="works")
ax.barh(y_p + 0.4, [place_n_terms.get(p, 0) for p in place_s.index],
        color=PAL["orange"], height=0.4, label="distinct Arabic terms")
ax.set_yticks(y_p + 0.2)
ax.set_yticklabels(place_s.index, fontsize=9)
ax.set_xlabel("count")
ax.set_title("Publication Places of Arabic-Containing EMLAP Works\n(Where was Arabic alchemical vocabulary circulating?)",
             fontsize=11)
ax.legend(fontsize=9)

# Panel 4: Genre breakdown of Arabic-containing works
ax = axes[1, 1]
genres = [meta_lookup.get(wid, {}).get("genre", "unknown") for wid in work_term_map.keys()]
# Simplify genres
genre_simple = []
for g in genres:
    if "compendium" in g:
        genre_simple.append("compendium")
    elif "recipe" in g:
        genre_simple.append("recipes")
    elif "dialogue" in g:
        genre_simple.append("dialogue")
    elif "poem" in g:
        genre_simple.append("poem")
    elif "letter" in g:
        genre_simple.append("letters")
    elif "treatise" in g:
        genre_simple.append("treatise")
    else:
        genre_simple.append("other")

genre_counts = Counter(genre_simple)
genre_s = pd.Series(genre_counts).sort_values()
# Also: mean Arabic terms per genre
genre_terms = defaultdict(list)
for wid, terms in work_term_map.items():
    g = meta_lookup.get(wid, {}).get("genre", "unknown")
    gs = "treatise"
    if "compendium" in g: gs = "compendium"
    elif "recipe" in g: gs = "recipes"
    elif "dialogue" in g: gs = "dialogue"
    elif "poem" in g: gs = "poem"
    elif "letter" in g: gs = "letters"
    genre_terms[gs].append(len(terms))

genre_colors = {
    "treatise": PAL["blue"], "compendium": PAL["orange"],
    "recipes": PAL["teal"], "dialogue": PAL["purple"],
    "poem": PAL["pink"], "letters": PAL["brown"], "other": PAL["gray"],
}
colors_g = [genre_colors.get(g, PAL["gray"]) for g in genre_s.index]
ax.barh(range(len(genre_s)), genre_s.values, color=colors_g)
ax.set_yticks(range(len(genre_s)))
ax.set_yticklabels(genre_s.index, fontsize=10)
ax.set_xlabel("number of EMLAP works")
ax.set_title("Genres of Arabic-Containing EMLAP Works", fontsize=11)
for i, (g, v) in enumerate(genre_s.items()):
    mean_t = np.mean(genre_terms.get(g, [0]))
    ax.text(v + 0.2, i, f"{v} works (mean {mean_t:.0f} Arabic terms)",
            va="center", fontsize=8.5)

plt.suptitle("The EMLAP Corpus: Pre-Ruland Alchemical Texts Containing Arabic Vocabulary",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "emlap_works_identified.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ emlap_works_identified.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 2: WHICH TERMS APPEAR IN WHICH WORKS? (HEATMAP)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 2: Term × work heatmap…")

# Top 25 terms by EMLAP breadth, top 20 works by Arabic richness
top_terms = sorted(term_work_map.keys(),
                   key=lambda t: len(term_work_map[t]), reverse=True)[:25]
top_works = list(work_richness.index[:20])

# Build presence/absence matrix
matrix = pd.DataFrame(0, index=top_terms,
                       columns=[work_label(w, short=True) for w in top_works])
for t in top_terms:
    for wid in term_work_map[t]:
        if wid in top_works:
            col = work_label(wid, short=True)
            matrix.loc[t, col] = 1

fig, ax = plt.subplots(figsize=(20, 14))
sns.heatmap(matrix, cmap=["white", PAL["green"]], linewidths=0.5,
            linecolor="#EEEEEE", ax=ax, cbar=False,
            xticklabels=True, yticklabels=True)
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9)
ax.set_yticklabels(ax.get_yticklabels(), fontsize=9)
ax.set_title("Arabic Terms × EMLAP Works: Presence/Absence Matrix\n"
             "(Top 25 terms by corpus breadth × Top 20 works by Arabic vocabulary)",
             fontsize=13)
ax.set_xlabel("EMLAP work (author, date)")
ax.set_ylabel("Arabic-tradition term")

# Add row sums (number of works) and column sums (number of terms)
for i, t in enumerate(top_terms):
    n = matrix.iloc[i].sum()
    ax.text(len(top_works) + 0.1, i + 0.5, f"{n} works", va="center", fontsize=7.5)
for j, wid in enumerate(top_works):
    n = matrix.iloc[:, j].sum()
    ax.text(j + 0.5, len(top_terms) + 0.1, str(n), ha="center", fontsize=7.5)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "emlap_term_work_matrix.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ emlap_term_work_matrix.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 3: TEMPORAL ANALYSIS — WHEN DO ARABIC TERMS FIRST APPEAR?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 3: Temporal analysis…")

fig, axes = plt.subplots(2, 2, figsize=(20, 16))

# For each term, find earliest EMLAP attestation date
term_earliest = {}
term_all_dates = defaultdict(list)
for term, work_ids in term_work_map.items():
    dates = [meta_lookup.get(wid, {}).get("date", 9999) for wid in work_ids]
    dates = [d for d in dates if d and d < 9999]
    if dates:
        term_earliest[term] = min(dates)
        term_all_dates[term] = sorted(dates)

# Panel 1: earliest attestation date distribution
ax = axes[0, 0]
earliest = pd.Series(term_earliest)
bins_d = range(1510, 1660, 10)
ax.hist(earliest, bins=bins_d, color=PAL["teal"], edgecolor="white", alpha=0.85)
ax.set_xlabel("earliest EMLAP attestation (decade)")
ax.set_ylabel("number of Arabic terms")
ax.set_title("When Do Arabic Terms First Appear in EMLAP?\n(Earliest attestation date per term)", fontsize=12)
ax.axvline(1612, color=PAL["red"], ls="--", lw=2, label="Ruland 1612")
ax.legend(fontsize=10)

# Panel 2: cumulative discovery curve
ax = axes[0, 1]
# How many unique Arabic terms are attested by each date?
all_emlap_dates = sorted(meta["date_publication"].unique())
cumulative = []
seen_terms = set()
for date in all_emlap_dates:
    # Which works were published by this date?
    works_by_date = set(meta[meta["date_publication"] <= date]["no."])
    terms_by_date = set()
    for wid in works_by_date:
        terms_by_date.update(work_term_map.get(wid, set()))
    cumulative.append({"date": date, "n_terms": len(terms_by_date)})

cum_df = pd.DataFrame(cumulative)
ax.plot(cum_df["date"], cum_df["n_terms"], "o-", color=PAL["green"], lw=2, markersize=3)
ax.fill_between(cum_df["date"], cum_df["n_terms"], alpha=0.15, color=PAL["green"])
ax.set_xlabel("publication date")
ax.set_ylabel("cumulative unique Arabic terms attested")
ax.set_title("Cumulative Arabic Vocabulary in EMLAP\n(How fast did the documented vocabulary grow?)", fontsize=12)
ax.axvline(1612, color=PAL["red"], ls="--", lw=2, label="Ruland 1612")
ax.legend(fontsize=10)
# Annotate key dates
for date, label in [(1518, "Pseudo-Lull &\nPantheus"), (1561, "Verae\nAlchemiae"),
                     (1597, "Libavius")]:
    idx = cum_df[cum_df["date"] == date]
    if len(idx) > 0:
        ax.annotate(label, xy=(date, idx.iloc[0]["n_terms"]),
                    fontsize=7.5, color=PAL["darkblue"],
                    xytext=(5, 10), textcoords="offset points")

# Panel 3: which terms appear earliest vs latest?
ax = axes[1, 0]
earliest_sorted = earliest.sort_values()
# Show the 15 earliest and 10 latest
n_early = 15
n_late = 10
early_terms = earliest_sorted.head(n_early)
late_terms = earliest_sorted.tail(n_late)
show_terms = pd.concat([early_terms, late_terms])
y_t = np.arange(len(show_terms))
colors_t = [PAL["green"] if i < n_early else PAL["orange"]
            for i in range(len(show_terms))]
ax.barh(y_t, show_terms.values, color=colors_t, height=0.6)
ax.set_yticks(y_t)
ax.set_yticklabels(show_terms.index, fontsize=8.5)
ax.invert_yaxis()
ax.set_xlabel("earliest EMLAP attestation date")
ax.set_title(f"Earliest ({n_early}, green) and Latest ({n_late}, orange)\n"
             "Arabic Terms by First EMLAP Appearance", fontsize=12)
ax.axvline(1612, color=PAL["red"], ls="--", lw=1.5, alpha=0.6)
# Annotate with the work
for i, (term, date) in enumerate(show_terms.items()):
    # Find the work
    wids_for_term = term_work_map[term]
    earliest_wid = min(wids_for_term,
                       key=lambda w: meta_lookup.get(w, {}).get("date", 9999))
    m = meta_lookup.get(earliest_wid, {})
    ax.text(date + 1, i, f"← {m.get('surname', '?')}, {m.get('title', '?')[:20]}",
            va="center", fontsize=6.5, color=PAL["darkblue"])

# Panel 4: decades heatmap — terms × decades
ax = axes[1, 1]
decades = list(range(1510, 1660, 10))
decade_labels = [f"{d}s" for d in decades]
# For top 20 terms, show which decades they appear in
top20 = list(earliest.sort_values().head(20).index)
dec_matrix = pd.DataFrame(0, index=top20, columns=decade_labels)
for term in top20:
    for d in term_all_dates.get(term, []):
        dec = (d // 10) * 10
        dec_label = f"{dec}s"
        if dec_label in dec_matrix.columns:
            dec_matrix.loc[term, dec_label] += 1

sns.heatmap(dec_matrix, cmap="YlGn", linewidths=0.5, ax=ax, annot=True,
            fmt="d", annot_kws={"fontsize": 7}, cbar_kws={"label": "works in decade"})
ax.set_title("Arabic Terms Across Decades\n(When does each term appear in the EMLAP corpus?)", fontsize=12)
ax.set_xlabel("decade")

plt.suptitle("Temporal Dimension: Arabic Vocabulary in European Alchemical Printing (1515–1648)",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "emlap_temporal.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ emlap_temporal.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 4: KEY TEXTS — DEEP DIVE INTO THE MOST ARABIC-RICH WORKS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 4: Key texts deep dive…")

fig = plt.figure(figsize=(24, 18))
gs = gridspec.GridSpec(3, 2, hspace=0.35, wspace=0.3)

top6_works = list(work_richness.index[:6])

for idx, wid in enumerate(top6_works):
    ax = fig.add_subplot(gs[idx // 2, idx % 2])
    ax.axis("off")

    m = meta_lookup.get(wid, {})
    terms = sorted(work_term_map[wid])
    n_terms = len(terms)

    text = f"{m['author']} ({m['date']}, {m['place']})\n"
    text += f"{m['title'][:60]}\n"
    text += f"Genre: {m['genre']} | Subject: {m['subject']}\n"
    text += f"Size: {m['tokens']:,} tokens | Compendium: {'yes' if m['is_compendium'] else 'no'}\n"
    text += "═" * 60 + "\n"
    text += f"\n{n_terms} Arabic-tradition terms found:\n\n"

    # Group terms by etymology
    term_etymologies = {}
    for t in terms:
        rows = df[df["norm_control"] == t]
        if len(rows) > 0:
            etym = rows["etymology_clean"].mode().iloc[0] if len(rows["etymology_clean"].mode()) > 0 else "?"
        else:
            etym = "?"
        term_etymologies[t] = etym

    by_etym = defaultdict(list)
    for t, e in term_etymologies.items():
        by_etym[e].append(t)

    for etym in ["Arabic", "Latinised Arabic", "Persian-Arabic", "Persian",
                  "mixed", "unclear", "not reviewed", "other/specific"]:
        if etym in by_etym:
            terms_str = ", ".join(sorted(by_etym[etym]))
            if len(terms_str) > 80:
                terms_str = terms_str[:77] + "…"
            text += f"  [{etym}] {terms_str}\n"

    # Show 2 sample snippets
    text += "\nSample evidence snippets:\n"
    ev_for_work = [(s["term"], s["snippet"]) for s in all_snippets
                   if s["work_id"] == wid]
    seen_terms_in_snip = set()
    count = 0
    for term, snip in ev_for_work:
        if term in seen_terms_in_snip:
            continue
        seen_terms_in_snip.add(term)
        snip_clean = snip.replace("\n", " ").strip()[:90]
        text += f'  "{snip_clean}…" [{term}]\n'
        count += 1
        if count >= 3:
            break

    ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=8,
            va="top", fontfamily="monospace", linespacing=1.2,
            bbox=dict(boxstyle="round,pad=0.3", facecolor=PAL["lightblue"], alpha=0.15))
    ax.set_title(f"{m['surname']}, {m['title'][:35]} ({m['date']})", fontsize=11, fontweight="bold")

fig.suptitle("The 6 Most Arabic-Rich Texts in the EMLAP Corpus",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "emlap_key_texts.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ emlap_key_texts.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 5: TERM CO-OCCURRENCE IN CONTEXT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 5: Term co-occurrence with context…")

fig, axes = plt.subplots(1, 2, figsize=(22, 12))

# Left: co-occurrence heatmap with work labels
top_terms_co = sorted(term_work_map.keys(),
                      key=lambda t: len(term_work_map[t]), reverse=True)[:20]
cooc = pd.DataFrame(0, index=top_terms_co, columns=top_terms_co)
for wid, terms in work_term_map.items():
    present = [t for t in top_terms_co if t in terms]
    for i, t1 in enumerate(present):
        for t2 in present[i+1:]:
            cooc.loc[t1, t2] += 1
            cooc.loc[t2, t1] += 1

ax = axes[0]
mask = np.triu(np.ones_like(cooc, dtype=bool), k=0)
sns.heatmap(cooc, mask=mask, cmap="YlOrRd", ax=ax, linewidths=0.5,
            annot=True, fmt="d", annot_kws={"fontsize": 7},
            cbar_kws={"label": "shared EMLAP works"})
ax.set_title("Term Co-Occurrence in EMLAP Works\n(How often do Arabic terms appear in the same text?)", fontsize=12)
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=8)

# Right: interpretation — which clusters emerge?
ax = axes[1]
ax.axis("off")
# Identify highly co-occurring pairs
pairs = []
for i, t1 in enumerate(top_terms_co):
    for t2 in top_terms_co[i+1:]:
        v = cooc.loc[t1, t2]
        if v >= 3:
            pairs.append((t1, t2, v))
pairs.sort(key=lambda x: -x[2])

text = "Term Co-Occurrence Clusters\n"
text += "═" * 55 + "\n\n"
text += "Pairs appearing in 3+ shared EMLAP works:\n\n"
for t1, t2, v in pairs[:20]:
    # Find shared works
    shared = term_work_map[t1] & term_work_map[t2]
    shared_labels = [work_label(w, short=True) for w in sorted(shared)[:3]]
    shared_str = ", ".join(shared_labels)
    if len(shared) > 3:
        shared_str += f" +{len(shared)-3}"
    text += f"  {t1:15s} × {t2:15s} ({v} works)\n"
    text += f"    in: {shared_str}\n\n"

text += "\nInterpretation:\n"
text += "These clusters reflect how Arabic\n"
text += "vocabulary traveled in 'packages':\n"
text += "  • Mineral terms (arsenicum, borax,\n"
text += "    sulphur, antimonium, marcasita)\n"
text += "    appear together in metallurgical texts\n"
text += "  • Apparatus terms (alembicus, athanor)\n"
text += "    co-occur in procedural texts\n"
text += "  • Substance terms (elixir, alkali,\n"
text += "    alcohol) bridge both clusters"

ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=8.5,
        va="top", fontfamily="monospace", linespacing=1.25)
ax.set_title("Co-Occurrence Interpretation", fontsize=12)

plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "emlap_cooccurrence_v2.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ emlap_cooccurrence_v2.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 6: AUTOMATED SCORES vs HUMAN VERDICT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 6: Automated scores vs human verdict…")

fig, axes = plt.subplots(2, 3, figsize=(22, 14))

arabic_conf = df[df["verdict_clean"] == "ARABIC"]["confidence_score"].dropna()
uncertain_conf = df[df["verdict_clean"] == "UNCERTAIN"]["confidence_score"].dropna()
arabic_irr = df[df["verdict_clean"] == "ARABIC"]["irrelevance_probability"].dropna()
uncertain_irr = df[df["verdict_clean"] == "UNCERTAIN"]["irrelevance_probability"].dropna()
bins_c = np.arange(0.55, 1.05, 0.05)
bins_i = np.arange(-0.025, 1.05, 0.05)

# Panel 1: confidence by verdict
ax = axes[0, 0]
ax.hist(arabic_conf, bins=bins_c, alpha=0.7, color=PAL["green"],
        label=f"ARABIC (n={len(arabic_conf)})", edgecolor="white")
ax.hist(uncertain_conf, bins=bins_c, alpha=0.8, color=PAL["red"],
        label=f"UNCERTAIN (n={len(uncertain_conf)})", edgecolor="white")
ax.set_xlabel("confidence score")
ax.set_ylabel("count")
ax.set_title("Confidence Score by Verdict", fontsize=12)
ax.legend(fontsize=9)

# Panel 2: irrelevance by verdict
ax = axes[0, 1]
ax.hist(arabic_irr, bins=bins_i, alpha=0.7, color=PAL["green"],
        label=f"ARABIC", edgecolor="white")
ax.hist(uncertain_irr, bins=bins_i, alpha=0.8, color=PAL["red"],
        label=f"UNCERTAIN", edgecolor="white")
ax.set_xlabel("irrelevance probability")
ax.set_ylabel("count")
ax.set_title("Irrelevance Score by Verdict", fontsize=12)
ax.legend(fontsize=9)

# Panel 3: summary
ax = axes[0, 2]
ax.axis("off")
text = "Automated Scores vs Human Verdict\n"
text += "═" * 45 + "\n\n"
text += "                  ARABIC     UNCERTAIN\n"
text += f"  n               {len(arabic_conf):>5d}        {len(uncertain_conf):>5d}\n\n"
text += f"  conf mean       {arabic_conf.mean():>5.3f}        {uncertain_conf.mean():>5.3f}\n"
text += f"  conf median     {arabic_conf.median():>5.3f}        {uncertain_conf.median():>5.3f}\n\n"
text += f"  irr mean        {arabic_irr.mean():>5.3f}        {uncertain_irr.mean():>5.3f}\n"
text += f"  irr median      {arabic_irr.median():>5.3f}        {uncertain_irr.median():>5.3f}\n\n"
text += "Key finding:\n"
text += f"  UNCERTAIN terms have LOWER conf\n"
text += f"  ({uncertain_conf.mean():.3f} vs {arabic_conf.mean():.3f})\n"
text += f"  and HIGHER irrelevance\n"
text += f"  ({uncertain_irr.mean():.3f} vs {arabic_irr.mean():.3f})\n\n"
text += "  → The AI's uncertainty signals\n"
text += "    partially predict human disagreement\n\n"

# Also compare all 928 vs included 363
raw_conf = raw_df["confidence_score"].dropna()
raw_irr = raw_df["irrelevance_probability"].dropna()
text += "All 928 vs Included 363:\n"
text += f"  All:  conf={raw_conf.mean():.3f} irr={raw_irr.mean():.3f}\n"
text += f"  Incl: conf={df['confidence_score'].mean():.3f} irr={df['irrelevance_probability'].mean():.3f}\n"
text += f"  → Included terms have higher conf,\n"
text += f"    lower irrelevance"
ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9,
        va="top", fontfamily="monospace", linespacing=1.3)

# Panel 4: 2D scatter by verdict
ax = axes[1, 0]
for v, color, label in [("ARABIC", PAL["green"], "ARABIC"),
                         ("UNCERTAIN", PAL["red"], "UNCERTAIN")]:
    sub = df[df["verdict_clean"] == v]
    ax.scatter(sub["confidence_score"], sub["irrelevance_probability"],
               c=color, alpha=0.5, s=25, label=label, edgecolors="white", linewidth=0.3)
ax.set_xlabel("confidence score")
ax.set_ylabel("irrelevance probability")
ax.set_title("Confidence × Irrelevance by Verdict", fontsize=12)
ax.legend(fontsize=9)

# Panel 5: 2D scatter by etymology
ax = axes[1, 1]
for etym in ["Arabic", "Latinised Arabic", "Persian-Arabic", "mixed", "unclear", "not reviewed"]:
    sub = df[df["etymology_clean"] == etym]
    if len(sub) > 0:
        ax.scatter(sub["confidence_score"], sub["irrelevance_probability"],
                   c=etym_colors.get(etym, PAL["gray"]), alpha=0.5, s=25,
                   label=etym, edgecolors="white", linewidth=0.3)
ax.set_xlabel("confidence score")
ax.set_ylabel("irrelevance probability")
ax.set_title("Confidence × Irrelevance by Etymology", fontsize=12)
ax.legend(fontsize=8, loc="upper left")

# Panel 6: score distributions — all 928 vs included 363
ax = axes[1, 2]
all_raw_conf = raw_df["confidence_score"].dropna()
incl_conf = df["confidence_score"].dropna()
bins_c2 = np.arange(0.05, 1.05, 0.05)
ax.hist(all_raw_conf, bins=bins_c2, alpha=0.5, color=PAL["blue"],
        label=f"All 928 detections", density=True, edgecolor="white")
ax.hist(incl_conf, bins=bins_c2, alpha=0.6, color=PAL["green"],
        label=f"Included 363", density=True, edgecolor="white")
ax.set_xlabel("confidence score")
ax.set_ylabel("density")
ax.set_title("All Detections vs Included:\nConfidence Distribution", fontsize=12)
ax.legend(fontsize=9)

plt.suptitle("Do Automated Scores Predict Human Decisions?",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "scores_vs_verdict_v2.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ scores_vs_verdict_v2.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 7: TERMS NOT IN EMLAP — RULAND INNOVATIONS OR SEARCH FAILURES?
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 7: Terms not in EMLAP…")

fig, axes = plt.subplots(1, 2, figsize=(22, 10))

# Terms with EMLAP evidence vs without
term_emlap = df.groupby("norm_control").agg(
    has_emlap=("emlap_flag", lambda x: (x == "yes_corpus").any()),
    count=("lemma", "size"),
    etymology=("etymology_clean", lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else "?"),
    confidence=("confidence_score", "mean"),
    wiki_match=("wiki_match_flag", lambda x: "yes" if x.astype(str).str.lower().str.strip().eq("yes").any() else "no"),
).sort_values("count", ascending=False)

no_emlap = term_emlap[~term_emlap["has_emlap"]]
yes_emlap = term_emlap[term_emlap["has_emlap"]]

# Left panel: the missing terms
ax = axes[0]
if len(no_emlap) > 0:
    show_n = min(30, len(no_emlap))
    ne = no_emlap.head(show_n)
    y_ne = np.arange(show_n)
    colors_ne = [etym_colors.get(e, PAL["gray"]) for e in ne["etymology"]]
    ax.barh(y_ne, ne["count"], color=colors_ne)
    ax.set_yticks(y_ne)
    ax.set_yticklabels(ne.index, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("entries in Ruland's dictionary")
    ax.set_title(f"Arabic Terms NOT in EMLAP ({len(no_emlap)} terms)\n"
                 "(bar color = etymology; could be search failures)", fontsize=12)
    for i, (term, row) in enumerate(ne.iterrows()):
        wiki = "W✓" if row["wiki_match"] == "yes" else "W·"
        ax.text(row["count"] + 0.1, i,
                f"[{row['etymology']}] {wiki} conf={row['confidence']:.2f}",
                va="center", fontsize=7.5)

# Right panel: comparison
ax = axes[1]
ax.axis("off")
text = f"EMLAP Coverage Summary\n"
text += "═" * 50 + "\n\n"
text += f"In EMLAP:     {len(yes_emlap):3d} unique terms ({100*len(yes_emlap)/len(term_emlap):.0f}%)\n"
text += f"Not in EMLAP: {len(no_emlap):3d} unique terms ({100*len(no_emlap)/len(term_emlap):.0f}%)\n\n"

# Compare characteristics
text += "Characteristics comparison:\n\n"
text += f"                     In EMLAP    Not in EMLAP\n"
text += f"  mean Ruland entries {yes_emlap['count'].mean():>6.1f}       {no_emlap['count'].mean():>6.1f}\n"
text += f"  mean AI confidence  {yes_emlap['confidence'].mean():>6.3f}       {no_emlap['confidence'].mean():>6.3f}\n"
text += f"  Wiktionary match    {100*(yes_emlap['wiki_match']=='yes').sum()/len(yes_emlap):>5.0f}%        {100*(no_emlap['wiki_match']=='yes').sum()/len(no_emlap) if len(no_emlap)>0 else 0:>5.0f}%\n\n"

text += "Etymology of missing terms:\n"
ne_etym = no_emlap["etymology"].value_counts()
for e, c in ne_etym.items():
    text += f"  {e:20s} {c:3d} ({100*c/len(no_emlap):.0f}%)\n"

text += "\nPossible reasons for absence:\n"
text += "  • Spelling too variable for search\n"
text += "  • Lemmatization failure on Arabic forms\n"
text += "  • Genuinely rare or Ruland-specific\n"
text += "  • Terms entered Latin after EMLAP cutoff\n"
text += "  • Terms used in manuscripts, not print"

ax.text(0.02, 0.95, text, transform=ax.transAxes, fontsize=9.5,
        va="top", fontfamily="monospace", linespacing=1.3)
ax.set_title("Coverage Analysis", fontsize=12)

plt.suptitle("What's Missing from EMLAP? Arabic Terms Without Pre-Ruland Attestation",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "emlap_gaps.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ emlap_gaps.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# FIG 8: EMLAP DATA QUALITY — SEARCH CAPS AND ARTIFACTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print("\nFig 8: EMLAP data quality…")

fig, axes = plt.subplots(1, 3, figsize=(22, 8))

# Panel 1: occurrence count distribution with cap annotation
ax = axes[0]
occ_vals = df.groupby("norm_control")["emlap_total_occurrences"].max().dropna()
occ_hist = occ_vals.value_counts().sort_index()
ax.bar(occ_hist.index, occ_hist.values, color=PAL["teal"], width=0.8)
if 15 in occ_hist.index:
    ax.bar([15], [occ_hist[15]], color=PAL["red"], width=0.8)
    ax.annotate(f"n={occ_hist[15]}: likely\nsearch cap at 15",
                xy=(15, occ_hist[15]), xytext=(22, occ_hist[15]),
                arrowprops=dict(arrowstyle="->", color=PAL["red"]),
                fontsize=9, color=PAL["red"])
ax.set_xlabel("EMLAP occurrence count")
ax.set_ylabel("number of terms")
ax.set_title("Distribution of EMLAP Counts\n(Spike at 15 = probable search cap)", fontsize=12)

# Panel 2: distinct works is more reliable
ax = axes[1]
works_vals = df.groupby("norm_control")["emlap_distinct_works"].max().dropna()
works_hist = works_vals.value_counts().sort_index()
ax.bar(works_hist.index, works_hist.values, color=PAL["green"], width=0.8)
ax.set_xlabel("distinct EMLAP works containing term")
ax.set_ylabel("number of terms")
ax.set_title("Distribution of Distinct Works\n(More reliable than occurrence count — no cap)", fontsize=12)

# Panel 3: text sizes of EMLAP works
ax = axes[2]
tokens = []
for wid in work_term_map:
    m = meta_lookup.get(wid, {})
    tokens.append(m.get("tokens", 0) / 1000)
ax.hist(tokens, bins=20, color=PAL["blue"], edgecolor="white", alpha=0.8)
ax.set_xlabel("text size (thousands of tokens)")
ax.set_ylabel("number of EMLAP works with Arabic terms")
ax.set_title("Size of Arabic-Containing EMLAP Works\n(Larger texts have more chance of containing terms)", fontsize=12)
ax.axvline(np.median(tokens), color=PAL["red"], ls="--",
           label=f"median = {np.median(tokens):.0f}k tokens")
ax.legend(fontsize=9)

plt.suptitle("EMLAP Data Quality: Understanding the Limitations",
             fontsize=14, y=1.01, fontweight="bold")
plt.tight_layout()
fig.savefig(os.path.join(OUTDIR, "emlap_data_quality.png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print("  ✓ emlap_data_quality.png")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DONE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
print(f"\nAll done. Files in {OUTDIR}")
for f in sorted(os.listdir(OUTDIR)):
    print(f"  {f}")
