#!/usr/bin/env python3
"""Regenerate both paper figures from the published aggregate result tables.

The figures in `figures/` are produced entirely from `results/context_sensitivity.csv` and
`results/transfer_retention_metrics.csv`. No restricted source data is required, so figure
reproduction is fully portable. Model re-estimation is not: see docs/reproducibility.md.

Usage:
    python src/build_figures.py [--output-dir figures]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

INK = "#17324D"
BLUE = "#2F6690"
TEAL = "#2A9D8F"
AMBER = "#D99000"
CORAL = "#D05A4E"
SLATE = "#667788"
GRID = "#D9E0E6"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 12.5,
    "axes.labelsize": 13,
    "axes.edgecolor": SLATE,
    "axes.linewidth": 0.8,
    "xtick.color": INK,
    "ytick.color": INK,
    "text.color": INK,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})


def style(ax, grid: str = "y") -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid, color=GRID, linewidth=0.7, alpha=0.85)
    ax.set_axisbelow(True)


def save(fig, stem: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for extension in ("png", "svg"):
        fig.savefig(output_dir / f"{stem}.{extension}",
                    dpi=240 if extension == "png" else None, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {stem}.png and {stem}.svg")


def figure_one(output_dir: Path) -> None:
    """Similarity retrieval against eligible coverage, across minimum-minutes thresholds."""
    table = pd.read_csv(RESULTS / "context_sensitivity.csv")
    rows = table[table.analysis.eq("minimum_minutes")].copy()
    rows["minutes"] = rows.stratum.str.extract(r"(\d+)").astype(int)
    rows = rows.sort_values("minutes")

    labels = [f"{m:,}" for m in rows.minutes]
    recall = rows.recall_at_10.tolist()
    eligible = rows.n.tolist()
    colors = [BLUE if m == 900 else SLATE for m in rows.minutes]

    fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(8.4, 6.3))
    fig.suptitle("Stricter playing-time requirements sharpen retrieval but shrink the pool",
                 x=0.045, y=0.985, ha="left", fontsize=15.5, fontweight="bold")
    fig.text(0.045, 0.918,
             "Same-player next-season retrieval at three minimum-minutes thresholds. "
             "The 900-minute rule, highlighted, is the study's operating point.",
             ha="left", va="top", fontsize=10.2, color=SLATE)

    bars = ax0.bar(labels, recall, color=colors, width=0.6)
    ax0.set_ylim(0, 0.345)
    ax0.set_ylabel("Recall@10 (higher is better)")
    ax0.set_xlabel("Minimum minutes played")
    style(ax0)
    for bar, value in zip(bars, recall):
        ax0.text(bar.get_x() + bar.get_width() / 2, value + 0.008, f"{value:.3f}",
                 ha="center", fontsize=12, fontweight="bold")

    bars = ax1.bar(labels, eligible, color=colors, width=0.6)
    ax1.set_ylim(0, 12600)
    ax1.set_ylabel("Eligible player profiles")
    ax1.set_xlabel("Minimum minutes played")
    style(ax1)
    for bar, value in zip(bars, eligible):
        ax1.text(bar.get_x() + bar.get_width() / 2, value + 260, f"{value:,}",
                 ha="center", fontsize=12, fontweight="bold")

    ax0.text(0.02, 0.97, "retrieval improves", transform=ax0.transAxes, ha="left", va="top",
             fontsize=11, color=TEAL, fontweight="bold")
    ax1.text(0.98, 0.97, "coverage falls", transform=ax1.transAxes, ha="right", va="top",
             fontsize=11, color=CORAL, fontweight="bold")

    fig.subplots_adjust(top=0.775, bottom=0.135, left=0.085, right=0.975, wspace=0.28)
    save(fig, "figure_1_similarity_exposure_tradeoff", output_dir)


def figure_two(output_dir: Path) -> None:
    """Held-out transfer error for the full model, pre-set baselines and the post-hoc reference."""
    table = pd.read_csv(RESULTS / "transfer_retention_metrics.csv").set_index("metric")
    value = lambda key: float(table.loc[key, "value"])

    rows = [
        ("No change", value("mae_baseline_no_change"), SLATE),
        ("Training median", value("mae_baseline_training_median"), SLATE),
        ("Age x minutes band", value("mae_baseline_age_minute_band_median"), SLATE),
        ("Minutes band median", value("mae_baseline_minute_band_median"), BLUE),
        ("Pre-transfer minutes only\n(added afterwards)", value("mae_exposure_only_reference"), AMBER),
        ("Full model", value("mae_full_model"), TEAL),
    ]
    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]
    colors = [r[2] for r in rows]

    lower = float(table.loc["mae_full_model", "ci_lower"])
    upper = float(table.loc["mae_full_model", "ci_upper"])
    improvement = value("improvement_pct_vs_strongest_baseline")
    improvement_lo = float(table.loc["improvement_pct_vs_strongest_baseline", "ci_lower"])
    improvement_hi = float(table.loc["improvement_pct_vs_strongest_baseline", "ci_upper"])
    beyond_exposure = value("improvement_pct_vs_exposure_only")

    fig, ax = plt.subplots(figsize=(8.8, 5.8))
    fig.suptitle("Most of the error reduction comes from pre-transfer playing time alone",
                 x=0.045, y=0.985, ha="left", fontsize=15.5, fontweight="bold")
    fig.text(0.045, 0.918,
             f"{int(value('transfers_held_out')):,} held-out transfers. Grey and blue bars are the "
             "four baselines fixed before the evaluation; the amber bar was added afterwards as a "
             "reference.",
             ha="left", va="top", fontsize=10.2, color=SLATE)

    positions = np.arange(len(rows))[::-1]
    bars = ax.barh(positions, values, color=colors, height=0.6)
    ax.set_yticks(positions)
    ax.set_yticklabels(labels, fontsize=11.5)
    ax.set_xlabel("Mean absolute error on log playing-time retention (lower is better)")
    ax.set_xlim(0, 0.66)
    style(ax, grid="x")

    ax.errorbar(values[-1], positions[-1],
                xerr=[[values[-1] - lower], [upper - values[-1]]], fmt="none",
                ecolor=INK, elinewidth=1.5, capsize=5, capthick=1.5)
    for index, (bar, value_) in enumerate(zip(bars, values)):
        offset = (upper - value_) + 0.012 if index == len(values) - 1 else 0.006
        ax.text(value_ + offset, bar.get_y() + bar.get_height() / 2, f"{value_:.3f}",
                va="center", fontsize=12, fontweight="bold")

    ax.text(1.045, 0.74,
            "Full model vs the best\nbaseline fixed beforehand:\n"
            f"{improvement:.2f}% lower error\n"
            f"(95% CI {improvement_lo:.2f}% to {improvement_hi:.2f}%)",
            transform=ax.transAxes, fontsize=11, color=INK, va="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#EEF3F7", edgecolor="none"))
    ax.text(1.045, 0.33,
            "Against pre-transfer minutes\nalone the full model gains\n"
            f"only {beyond_exposure:.2f}%",
            transform=ax.transAxes, fontsize=11, color="#A96D00", va="top", fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#FCF4E2", edgecolor="none"))

    fig.subplots_adjust(top=0.79, bottom=0.155, left=0.225, right=0.665)
    save(fig, "figure_2_transfer_retention_model_comparison", output_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default=str(ROOT / "figures"),
                        help="directory to write the figures into (default: figures/)")
    arguments = parser.parse_args()
    output_dir = Path(arguments.output_dir)
    figure_one(output_dir)
    figure_two(output_dir)


if __name__ == "__main__":
    main()
