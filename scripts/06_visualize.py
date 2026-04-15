"""
Phase 6: Generate all paper figures from saved results.
Run after all inference + judging + silhouette scores are complete.

Usage:
    python scripts/06_visualize.py

Output: figures/compliance_heatmap.png
        figures/compliance_delta_heatmap.png
        figures/silhouette_by_size.png
        figures/size_vs_compliance.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.stats import spearmanr

SIZES_ORDERED = ["e2b", "e4b", "12b", "27b"]
SIZE_LABELS = {"e2b": "E2B\n(~2B)", "e4b": "E4B\n(~4B)",
               "12b": "12B", "27b": "27B"}
SIZE_PARAMS = {"e2b": 2, "e4b": 4, "12b": 12, "27b": 27}
LANG_ORDER = ["en", "es", "pt", "zh", "ar", "hi"]


def load_compliance():
    path = Path("data/outputs/compliance_rates.csv")
    if not path.exists():
        print(f"Missing: {path}. Run 03_llm_judge.py --all first.")
        return None
    return pd.read_csv(path)


def load_silhouette():
    path = Path("data/outputs/silhouette_scores.csv")
    if not path.exists():
        print(f"Missing: {path}. Run 05_silhouette_scores.py first.")
        return None
    return pd.read_csv(path)


def fig_compliance_heatmap(df, condition, title, fname):
    pivot = df[df["condition"] == condition].pivot(
        index="size", columns="language", values="compliance_rate"
    )
    pivot = pivot.reindex(SIZES_ORDERED).reindex(LANG_ORDER, axis=1)

    fig, ax = plt.subplots(figsize=(9, 4))
    sns.heatmap(pivot.astype(float), annot=True, fmt=".0%",
                cmap="RdYlGn_r", vmin=0, vmax=1, ax=ax,
                linewidths=0.5, linecolor="white")
    ax.set_title(title, fontsize=13, pad=12)
    ax.set_xlabel("Language")
    ax.set_ylabel("Model Size")
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

    fig, ax = plt.subplots(figsize=(9, 4))
    sns.heatmap(pivot.astype(float), annot=True, fmt="+.0%",
                cmap="RdBu_r", center=0, vmin=-0.1, vmax=1, ax=ax,
                linewidths=0.5, linecolor="white")
    ax.set_title("Compliance Rate Increase After Abliteration (Δ = abliterated − base)",
                 fontsize=12, pad=12)
    ax.set_xlabel("Language")
    ax.set_ylabel("Model Size")
    ax.set_yticklabels([SIZE_LABELS[s] for s in pivot.index], rotation=0)
    plt.tight_layout()
    out = Path("figures/compliance_delta_heatmap.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved → {out}")


def fig_size_vs_compliance(df):
    abliterated = df[df["condition"] == "abliterated"].copy()
    avg = abliterated.groupby("size")["compliance_rate"].mean().reset_index()
    avg["params"] = avg["size"].map(SIZE_PARAMS)
    avg = avg.sort_values("params")

    rho, p = spearmanr(avg["params"], avg["compliance_rate"])

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(avg["params"], avg["compliance_rate"], "o-",
            color="#e74c3c", linewidth=2, markersize=8, zorder=3)
    for _, row in avg.iterrows():
        ax.annotate(row["size"].upper(),
                    (row["params"], row["compliance_rate"]),
                    textcoords="offset points", xytext=(8, 4), fontsize=10)
    ax.set_xlabel("Model Size (Billions of Parameters)", fontsize=11)
    ax.set_ylabel("Avg. Compliance Rate Post-Abliteration", fontsize=11)
    ax.set_title(f"Smaller Models → Higher Compliance After Abliteration\n"
                 f"Spearman ρ = {rho:.3f}, p = {p:.3f}", fontsize=12)
    ax.set_ylim(0, 1.05)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    out = Path("figures/size_vs_compliance.png")
    plt.savefig(out, dpi=150)
    plt.close()
    print(f"Saved → {out}")


def fig_silhouette_by_size(df_sil):
    pivot = df_sil.pivot(index="size", columns="language", values="silhouette_score")
    pivot = pivot.reindex(SIZES_ORDERED).reindex(LANG_ORDER, axis=1)
    pivot["mean"] = pivot.mean(axis=1)

    fig, ax = plt.subplots(figsize=(7, 5))
    x = np.arange(len(SIZES_ORDERED))
    for lang in LANG_ORDER:
        if lang in pivot.columns:
            ax.plot(x, pivot[lang], "o--", alpha=0.5, label=lang, linewidth=1)
    ax.plot(x, pivot["mean"], "o-", color="black", linewidth=2.5,
            markersize=9, label="mean", zorder=5)

    ax.set_xticks(x)
    ax.set_xticklabels([SIZE_LABELS[s] for s in SIZES_ORDERED], fontsize=10)
    ax.set_xlabel("Model Size")
    ax.set_ylabel("Silhouette Score")
    ax.set_title("Harmful/Harmless Cluster Separation by Model Size\n"
                 "(Lower = worse separation = easier to abliterate)", fontsize=12)
    ax.legend(fontsize=9, loc="upper left")
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
