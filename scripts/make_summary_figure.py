"""Summary figure for the README: the 15 final candidates across every scoring axis.

Reads data/processed/depmap_tnbc_final_ranked_targets.csv and writes
results/summary_figure.png. Cells show each gene's rank (1 = best of 15) on the
three evidence axes that make up the composite score; safety and druggability
are annotations beside the score, not part of it.

Run: python scripts/make_summary_figure.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent
CASE_STUDY = {"IFI6", "LY6E", "HPRT1", "KIF2C"}

# Reference palette: surface/ink tokens and the blue sequential ramp (step 650 -> 100)
SURFACE, INK, INK_2, INK_MUTED = "#fcfcfb", "#0b0b0b", "#52514e", "#8a8985"
RAMP = ["#104281", "#184f95", "#1c5cab", "#256abf", "#2a78d6", "#3987e5", "#5598e7",
        "#6da7ec", "#86b6ef", "#9ec5f4", "#b7d3f6", "#cde2fb"]

df = pd.read_csv(ROOT / "data/processed/depmap_tnbc_final_ranked_targets.csv")
df = df.sort_values("composite_rank", kind="stable").reset_index(drop=True)
n = len(df)
df["composite_pos"] = df["composite_rank"].rank(method="min").astype(int)


def shade(rank):
    """Rank 1 -> darkest step, rank 15 -> lightest, one-hue sequential."""
    return RAMP[round((rank - 1) / (n - 1) * (len(RAMP) - 1))]


def ink_on(hex_color):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#ffffff" if (0.299 * r + 0.587 * g + 0.114 * b) < 150 else INK


axes_cols = [
    ("rank_essentiality", "Essentiality\n(TNBC vs.\nother lines)"),
    ("rank_tumor_selectivity", "Tumor\nselectivity\n(vs. normal)"),
    ("rank_survival", "Survival\n(adjusted\nCox)"),
]
CELL_W, CELL_H, GAP = 1.45, 0.62, 0.08

fig, ax = plt.subplots(figsize=(11, 8.2), dpi=200)
fig.patch.set_facecolor(SURFACE)
ax.set_facecolor(SURFACE)
ax.set_xlim(-2.0, 11.6)
ax.set_ylim(n + 1.55, -2.65)
ax.axis("off")

col_x = {c: i * (CELL_W + GAP) for i, (c, _) in enumerate(axes_cols)}
comp_x = 3 * (CELL_W + GAP) + 0.3
safety_x = comp_x + CELL_W + 0.85
loc_x = safety_x + 1.75

ax.text(-2.0, -2.35, "Final ranking of 15 TNBC target candidates", fontsize=15,
        fontweight="bold", color=INK, va="center")
ax.text(-2.0, -1.85, "Each cell is the gene's rank on that axis (1 = best of 15). "
        "Darker = better rank.", fontsize=9.5, color=INK_2, va="center")

for c, label in axes_cols:
    ax.text(col_x[c] + CELL_W / 2, -0.75, label, ha="center", va="center",
            fontsize=8.6, color=INK_2, linespacing=1.25)
ax.text(comp_x + CELL_W / 2, -0.75, "Composite\n(mean of\n3 ranks)", ha="center",
        va="center", fontsize=8.6, color=INK, fontweight="bold", linespacing=1.25)
ax.text(safety_x, -0.65, "Safety flag\n(GTEx)", ha="left", va="center",
        fontsize=8.6, color=INK_2, linespacing=1.25)
ax.text(loc_x, -0.65, "Protein location\n(HPA)", ha="left", va="center",
        fontsize=8.6, color=INK_2)
ax.text(safety_x, -1.35, "Annotations, not in the score", fontsize=8, color=INK_MUTED,
        va="center", style="italic")
ax.plot([safety_x - 0.3, safety_x - 0.3], [-1.45, n - 0.35], color="#dcdbd6", lw=0.8)

for i, row in df.iterrows():
    y = i
    is_case = row["gene"] in CASE_STUDY
    ax.text(-0.15, y + CELL_H / 2, row["gene"], ha="right", va="center", fontsize=10.5,
            color=INK, fontweight="bold" if is_case else "normal")
    for c, _ in axes_cols:
        r = int(row[c])
        fc = shade(r)
        ax.add_patch(FancyBboxPatch((col_x[c], y),
                                    CELL_W, CELL_H, boxstyle="round,pad=0,rounding_size=0.06",
                                    fc=fc, ec="none", mutation_aspect=1))
        label = str(r) + ("*" if c == "rank_survival" and row["cox_q_adj"] < 0.05 else "")
        ax.text(col_x[c] + CELL_W / 2, y + CELL_H / 2, label, ha="center", va="center",
                fontsize=9.5, color=ink_on(fc), fontweight="bold" if label.endswith("*") else "normal")
    fc = shade(row["composite_pos"])
    ax.add_patch(FancyBboxPatch((comp_x, y), CELL_W, CELL_H, boxstyle="round,pad=0,rounding_size=0.06",
                                fc=fc, ec="none"))
    ax.text(comp_x + CELL_W / 2, y + CELL_H / 2, f"{row['composite_rank']:.1f}", ha="center",
            va="center", fontsize=9.5, color=ink_on(fc), fontweight="bold")
    ax.text(safety_x, y + CELL_H / 2, row["safety_flag"], ha="left", va="center", fontsize=9.5,
            color=INK)
    loc = row["Subcellular main location"]
    if pd.isna(loc):
        loc = "Membrane (HPA class only)" if "membrane" in str(row["Protein class"]) else "n/a"
    ax.text(loc_x, y + CELL_H / 2, loc if len(loc) < 34 else loc[:31] + "...", ha="left",
            va="center", fontsize=9, color=INK_2)

for i, row in df.iterrows():
    if row["gene"] in CASE_STUDY:
        ax.plot([-1.95, -1.95], [i + 0.06, i + CELL_H - 0.06], color=RAMP[4], lw=3,
                solid_capstyle="round")

foot = ("Bold gene + left bar = case-study target.   * = survival result significant after FDR correction "
        "(LY6E, q = 0.036); every other survival rank is a non-significant ordering.\n"
        "Safety = highest expression in heart, liver or whole blood (GTEx): low < 5 TPM, moderate 5-20, high > 20.  "
        "High flags on IFI6/LY6E likely reflect blood immune-cell expression.")
ax.text(-2.0, n + 0.55, foot, fontsize=7.8, color=INK_2, va="top", linespacing=1.5)

out = ROOT / "results" / "summary_figure.png"
out.parent.mkdir(exist_ok=True)
fig.savefig(out, facecolor=SURFACE, bbox_inches="tight", pad_inches=0.3)
print(f"wrote {out}")
