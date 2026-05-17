"""
Phase 6: Generate all paper figures from saved results.
Run after all inference + judging + silhouette scores are complete.

Scope: 3 Dense sizes (E2B, E4B, 31B) × 7 languages.
26B-A4B (MoE) is out of scope here — the rendering code skips any rows that
sneak in from a future-work run so the principal figures stay clean. See
FUTURE_WORK.md if you want to plot the MoE sub-question separately.

Usage:
    python scripts/06_visualize.py

Output: figures/compliance_base_heatmap.png
        figures/compliance_abliterated_heatmap.png
        figures/compliance_delta_heatmap.png
        figures/silhouette_by_size.png
        figures/size_vs_compliance.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D
from scipy.stats import spearmanr

# Principal experiment: 3 Dense sizes only.
SIZES_ORDERED = ["e2b", "e4b", "31b"]
SIZE_LABELS = {"e2b": "E2B\n(~2B)", "e4b": "E4B\n(~4B)", "31b": "31B"}
SIZE_PARAMS = {"e2b": 2, "e4b": 4, "31b": 31}

# 7 languages, fixed display order (control language first, then the rest by
# resource tier so the heatmaps read left-to-right as we describe them in text).
LANG_ORDER = ["en", "es", "pt", "de", "zh", "ar", "hi"]


def load_compliance():
    path = Path("data/outputs/compliance_rates.csv")
    if not path.exists():
        print(f"Missing: {path}. Run 03_llm_judge.py --all first.")
        return None
    df = pd.read_csv(path)
    return df[df["size"].isin(SIZES_ORDERED)].copy()


def load_silhouette():
    path = Path("data/outputs/silhouette_scores.csv")
    if not path.exists():
        print(f"Missing: {path}. Run 05_silhouette_scores.py first.")
        return None
    df = pd.read_csv(path)
    return df[df["size"].isin(SIZES_ORDERED)].copy()


def fig_compliance_heatmap(df, condition, title, fname):
    pivot = df[df["condition"] == condition].pivot(
        index="size", columns="language", values="compliance_rate"
    )
    pivot = pivot.reindex(SIZES_ORDERED).reindex(LANG_ORDER, axis=1)

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.heatmap(pivot.astype(float), annot=True, fmt=".0%",
                cmap="RdYlGn_r", vmin=0, vmax=1, ax=ax,
                linewidths=0.5, linecolor="white")
    ax.set_title(title, fontsize=13, pad=12)
    ax.set_xlabel("Language")
    ax.set_ylabel("Model Size (Dense)")
    ax.set_yticklabels([SIZE_LABELS[s] for s in pivot.index], rotation=0)
    plt.tight_layout()
    out = Path("figures") / fname
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved → {out}")


def fig_compliance_delta(df):
    base = df[df["condition"] == "base"].set_index(["size", "language"])["compliance_rate"]
    abliterated = df[df["condition"] == "abliterated"].set_index(["size", "language"])["compliance_rate"]
    delta = (abliterated - base).reset_index()
    delta.columns = ["size", "language", "delta"]

    pivot = delta.pivot(index="size", columns="language", values="delta")
    pivot = pivot.reindex(SIZES_ORDERED).reindex(LANG_ORDER, axis=1)

    fig, ax = plt.subplots(figsize=(10, 4))
    sns.heatmap(pivot.astype(float), annot=True, fmt="+.0%",
                cmap="RdBu_r", center=0, vmin=-0.1, vmax=1, ax=ax,
                linewidths=0.5, linecolor="white")
    ax.set_title("Compliance Rate Increase After Abliteration (Δ = abliterated − base)",
                 fontsize=12, pad=12)
    ax.set_xlabel("Language")
    ax.set_ylabel("Model Size (Dense)")
    ax.set_yticklabels([SIZE_LABELS[s] for s in pivot.index], rotation=0)
    plt.tight_layout()
    out = Path("figures/compliance_delta_heatmap.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved → {out}")


def fig_size_vs_compliance(df):
    # Design tokens — light theme from web/src/styles/global.css
    BG, PLOT_BG, PANEL_BG = "#FAF7F1", "#F3EFE6", "#E3DCC9"
    BORDER, BORDER_SUB = "#D8CFBC", "#E8E2D2"
    TEXT_PRI, TEXT_SEC, TEXT_TER = "#11182A", "#3E4560", "#6E7791"
    AMBER, AMBER_DARK = "#B87826", "#8F5C1D"
    TERRA, TERRA_DARK = "#C67B5C", "#A55A3D"

    means = (df.groupby(["size", "condition"])["compliance_rate"]
               .mean().unstack().reindex(SIZES_ORDERED))
    params_x = [SIZE_PARAMS[s] for s in SIZES_ORDERED]
    base_y = (means["base"] * 100).tolist()
    abl_y = (means["abliterated"] * 100).tolist()
    labels = [s.upper() for s in SIZES_ORDERED]
    peak_idx = labels.index("E4B")
    jump = abl_y[peak_idx] - abl_y[0]
    drop = abl_y[2] - abl_y[peak_idx]

    fig, ax = plt.subplots(figsize=(11, 6.5), dpi=200)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(PLOT_BG)

    # Dashed vertical guide at the peak
    ax.axvline(params_x[peak_idx], color=TERRA_DARK, linewidth=1,
               linestyle=(0, (3, 5)), alpha=0.5, zorder=1)

    # Lines — abliterated thicker; base secondary
    ax.plot(params_x, base_y, "-", color=AMBER, linewidth=2.5,
            zorder=3, solid_capstyle="round")
    ax.plot(params_x, abl_y, "-", color=TERRA, linewidth=4,
            zorder=4, solid_capstyle="round")

    # Base markers (halo + dot + label above — keeps clear of X-axis labels)
    for x, y in zip(params_x, base_y):
        ax.plot(x, y, "o", markersize=12, markerfacecolor=PLOT_BG,
                markeredgecolor=AMBER, markeredgewidth=2, zorder=5)
        ax.plot(x, y, "o", markersize=6, color=AMBER, zorder=6)
        ax.text(x, y + 5.5, f"{y:.1f}%", ha="center", va="bottom",
                fontsize=10, color=AMBER_DARK, fontweight="bold")

    # Abliterated markers (peak gets glow + bigger dot + label above)
    for i, (x, y) in enumerate(zip(params_x, abl_y)):
        is_peak = i == peak_idx
        if is_peak:
            ax.plot(x, y, "o", markersize=34, color=TERRA, alpha=0.16, zorder=4)
            ax.plot(x, y, "o", markersize=22, color=TERRA, alpha=0.22, zorder=4)
        ax.plot(x, y, "o", markersize=16 if is_peak else 13,
                markerfacecolor=PLOT_BG, markeredgecolor=TERRA,
                markeredgewidth=2.5, zorder=6)
        ax.plot(x, y, "o", markersize=9 if is_peak else 7,
                color=TERRA, zorder=7)
        ax.text(x, y + 5.5, f"{y:.1f}%", ha="center", va="bottom",
                fontsize=11 if is_peak else 10,
                color=TERRA_DARK, fontweight="bold")

    # Peak annotation badge
    ax.annotate(
        f"PEAK VULNERABILITY\n"
        f"+{jump:.1f} pp vs E2B   ·   {drop:+.1f} pp vs 31B",
        xy=(params_x[peak_idx], abl_y[peak_idx]),
        xytext=(params_x[peak_idx] * 1.8, abl_y[peak_idx] + 16),
        fontsize=10, color=TEXT_PRI, ha="left", va="center",
        bbox=dict(boxstyle="round,pad=0.7", facecolor=PANEL_BG,
                  edgecolor=TERRA_DARK, linewidth=1.25),
        arrowprops=dict(arrowstyle="-", color=TERRA_DARK,
                        linewidth=1.5, linestyle=(0, (2, 3))),
    )

    # Axes
    ax.set_xscale("log")
    ax.set_xticks(params_x)
    ax.set_xticklabels([f"{lab}\n~{p}B params" for lab, p in zip(labels, params_x)],
                       fontsize=11, color=TEXT_PRI)
    ax.minorticks_off()
    ax.set_ylim(0, 100)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    ax.set_yticklabels([f"{v}%" for v in [0, 20, 40, 60, 80, 100]],
                       fontsize=10, color=TEXT_TER)
    ax.set_xlabel("MODEL SIZE  ·  LOGARITHMIC SCALE", fontsize=10,
                  color=TEXT_SEC, labelpad=14, fontweight="bold")
    ax.set_ylabel("MEAN COMPLIANCE (%)", fontsize=10,
                  color=TEXT_SEC, labelpad=14, fontweight="bold")

    ax.grid(True, axis="y", linestyle=(0, (2, 4)), color=BORDER_SUB,
            linewidth=1, zorder=0)
    ax.grid(False, axis="x")
    for side in ["top", "right"]:
        ax.spines[side].set_visible(False)
    for side in ["left", "bottom"]:
        ax.spines[side].set_color(BORDER)
        ax.spines[side].set_linewidth(1.5)

    # Title + subtitle (figure-level so they sit cleanly above the plot)
    fig.suptitle("Mean post-abliteration compliance is not monotonic in size",
                 fontsize=18, fontweight="bold", color=TEXT_PRI,
                 x=0.05, y=0.97, ha="left", fontfamily="serif")
    fig.text(0.05, 0.915,
             "Gemma 4 Dense  ·  7 languages  ·  100 harmful prompts per language  ·  "
             "base vs abliterated (single-vector)",
             fontsize=11, color=TEXT_TER, ha="left", fontfamily="monospace")

    # Legend
    legend_handles = [
        Line2D([0], [0], color=TERRA, linewidth=4, marker="o",
               markersize=8, markerfacecolor=TERRA,
               label="Abliterated (single-vector)"),
        Line2D([0], [0], color=AMBER, linewidth=2.5, marker="o",
               markersize=6, markerfacecolor=AMBER,
               label="Base (intact filter)"),
    ]
    leg = ax.legend(handles=legend_handles, loc="upper right",
                    framealpha=0.96, fancybox=True, fontsize=10,
                    edgecolor=BORDER, facecolor=PLOT_BG)
    leg.get_frame().set_linewidth(1)
    for text in leg.get_texts():
        text.set_color(TEXT_SEC)

    plt.tight_layout(rect=[0, 0, 1, 0.88])
    out = Path("figures/size_vs_compliance.png")
    plt.savefig(out, dpi=200, facecolor=BG, bbox_inches="tight")
    plt.close()
    print(f"Saved → {out}")


def fig_silhouette_by_size(df_sil):
    pivot = df_sil.pivot(index="size", columns="language", values="silhouette_score")
    pivot = pivot.reindex(SIZES_ORDERED).reindex(LANG_ORDER, axis=1)
    pivot["mean"] = pivot[[c for c in LANG_ORDER if c in pivot.columns]].mean(axis=1)

    fig, ax = plt.subplots(figsize=(8, 5))
    x = np.arange(len(SIZES_ORDERED))
    palette = sns.color_palette("husl", len(LANG_ORDER))
    for lang, color in zip(LANG_ORDER, palette):
        if lang in pivot.columns:
            ax.plot(x, pivot[lang], "o--", alpha=0.55, label=lang, linewidth=1, color=color)
    ax.plot(x, pivot["mean"], "o-", color="black", linewidth=2.5,
            markersize=10, label="mean", zorder=5)

    ax.set_xticks(x)
    ax.set_xticklabels([SIZE_LABELS[s] for s in SIZES_ORDERED], fontsize=10)
    ax.set_xlabel("Model Size (Dense)")
    ax.set_ylabel("Silhouette Score")
    ax.set_title("Harmful/Harmless Cluster Separation by Model Size\n"
                 "(Lower = worse separation = easier to abliterate)", fontsize=12)
    ax.legend(fontsize=9, loc="best", ncol=2)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = Path("figures/silhouette_by_size.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved → {out}")


def main():
    Path("figures").mkdir(exist_ok=True)
    df_comp = load_compliance()
    df_sil = load_silhouette()

    if df_comp is not None:
        fig_compliance_heatmap(df_comp, "base",
            "Baseline Compliance Rate (Pre-Abliteration)",
            "compliance_base_heatmap.png")
        fig_compliance_heatmap(df_comp, "abliterated",
            "Post-Abliteration Compliance Rate Across Languages and Model Sizes",
            "compliance_abliterated_heatmap.png")
        fig_compliance_delta(df_comp)
        fig_size_vs_compliance(df_comp)

    if df_sil is not None:
        fig_silhouette_by_size(df_sil)

    print("\nAll figures saved to figures/")


if __name__ == "__main__":
    main()
