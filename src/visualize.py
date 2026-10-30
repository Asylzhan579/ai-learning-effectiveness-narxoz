"""Publication-ready figures (TASK 3).

Follows the 3 core rules of scientific visualisation:
  1. Explicit axis titles with physical units.
  2. Uncertainty shown (95% bootstrap CI: bands / error bars).
  3. Colour-blind-safe palette + different line styles / markers / hatches so the
     figures stay readable in black-and-white print.
Every figure is exported as vector .pdf AND raster .png (300 DPI).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import seaborn as sns  # noqa: E402

from src.process_data import CONDITIONS, bootstrap_ci, paired_wide  # noqa: E402

PALETTE = sns.color_palette("colorblind")
COLORS = {"AI": PALETTE[0], "Conventional": PALETTE[1]}
LINESTYLES = {"AI": "-", "Conventional": "--"}
MARKERS = {"AI": "o", "Conventional": "s"}
HATCHES = {"AI": "", "Conventional": "//"}
LABELS = {"AI": "AI-assisted", "Conventional": "Conventional (no AI)"}
DPI = 300


def set_style() -> None:
    sns.set_theme(style="whitegrid", context="paper")
    plt.rcParams.update({
        "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
        "legend.fontsize": 9, "figure.dpi": 100, "savefig.dpi": DPI,
        "pdf.fonttype": 42, "ps.fonttype": 42,  # embed TrueType fonts in PDF
    })


def save_figure(fig, name: str, outdir: str | Path = "reports/figures") -> list[Path]:
    """Save as vector PDF + 300-DPI PNG. Returns the written paths."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for ext in ("pdf", "png"):
        p = outdir / f"{name}.{ext}"
        fig.savefig(p, dpi=DPI, bbox_inches="tight")
        paths.append(p)
    return paths


def fig1_latency_vs_load(traj, n_pairs: int | None = None):
    """Fig. 1 -- score trajectory (pre -> post -> day 7) per condition, mean +- 95% CI.

    File name kept as ``fig1_latency_vs_load`` (required by the TASK 3 template):
    the study analogue of 'latency vs load' is 'outcome vs measurement stage'.
    Scores span 0-10 (< 1 order of magnitude) -> a linear axis is the correct choice.
    """
    set_style()
    fig, ax = plt.subplots(figsize=(6.2, 4.2))
    stages = list(dict.fromkeys(traj["stage"]))
    x = np.arange(len(stages))
    for cond in CONDITIONS:
        d = traj[traj["condition"] == cond].set_index("stage").loc[stages]
        off = -0.03 if cond == "AI" else 0.03  # tiny horizontal dodge
        ax.fill_between(x + off, d["ci_low"], d["ci_high"], color=COLORS[cond], alpha=0.18, lw=0)
        ax.errorbar(x + off, d["mean"], yerr=[d["mean"] - d["ci_low"], d["ci_high"] - d["mean"]],
                    color=COLORS[cond], linestyle=LINESTYLES[cond], marker=MARKERS[cond],
                    markersize=7, lw=2, capsize=4, label=LABELS[cond])
    ax.set_xticks(x)
    ax.set_xticklabels(stages)
    ax.set_xlabel("Measurement point (time since study session)")
    ax.set_ylabel("Test score (points, 0–10)")
    ax.set_ylim(0, 10)
    ttl = "Mean test score by condition (shaded band / bars: 95% bootstrap CI)"
    ax.set_title(ttl + (f"\nn = {n_pairs} paired students" if n_pairs else ""), fontsize=10)
    ax.legend(loc="lower right", frameon=True)
    fig.tight_layout()
    return fig


def fig2_distribution_boxplot(data, effects=None, cfg: dict | None = None):
    """Fig. 2 -- distributions per condition for the 3 outcome metrics.

    Box = IQR + median, whiskers 1.5*IQR, dots = individual students, grey lines =
    within-student pairing, black diamond + bar = mean with 95% bootstrap CI.
    """
    set_style()
    cfg = cfg or {"n_boot": 10000, "seed": 42, "ci_level": 0.95}
    panels = [("norm_gain", "(a) Immediate learning gain", "Normalized gain (unitless, 0–1)"),
              ("delayed_score", "(b) Retention after 7 days", "Delayed test score (points, 0–10)"),
              ("efficiency", "(c) Learning efficiency", "Raw gain per study minute (points/min)")]
    fig, axes = plt.subplots(1, 3, figsize=(11, 4.2))
    rng = np.random.default_rng(cfg["seed"])
    for ax, (metric, title, ylabel) in zip(axes, panels):
        vals = [data.loc[data["condition"] == c, metric].to_numpy() for c in CONDITIONS]
        bp = ax.boxplot(vals, positions=[0, 1], widths=0.5, patch_artist=True, showfliers=False,
                        medianprops=dict(color="black", lw=1.6))
        for patch, cond in zip(bp["boxes"], CONDITIONS):
            patch.set(facecolor=COLORS[cond], alpha=0.45, hatch=HATCHES[cond], edgecolor="black")
        w = paired_wide(data, metric)  # grey pairing lines
        jit = rng.uniform(-0.06, 0.06, len(w))
        for (_, r), j in zip(w.iterrows(), jit):
            ax.plot([0 + j, 1 + j], [r["AI"], r["Conventional"]], color="grey", alpha=0.35, lw=0.7, zorder=1)
        for k, cond in enumerate(CONDITIONS):
            ax.scatter(np.full(len(w), k) + jit, w[cond], s=18, color=COLORS[cond],
                       edgecolor="black", linewidth=0.4, marker=MARKERS[cond], zorder=3)
            m = w[cond].mean()
            lo, hi = bootstrap_ci(w[cond], "mean", cfg["n_boot"], cfg["seed"], cfg["ci_level"])
            ax.errorbar(k + 0.32, m, yerr=[[m - lo], [hi - m]], fmt="D", color="black",
                        mfc="white", ms=7, capsize=4, lw=1.5, zorder=4)
        ax.set_xticks([0, 1])
        ax.set_xticklabels([LABELS["AI"], "Conventional\n(no AI)"])
        ax.set_xlim(-0.5, 1.7)
        lo_y, hi_y = ax.get_ylim()
        ax.set_ylim(lo_y, hi_y + 0.14 * (hi_y - lo_y))  # headroom for the annotation
        ax.set_ylabel(ylabel)
        ax.set_title(title, loc="left")
        if effects is not None:
            e = effects[effects["metric"] == metric].iloc[0]
            ax.text(0.5, 0.985, f"Δ(AI−Conv) = {e['mean_diff']:.2f}  [{e['diff_ci_low']:.2f}, {e['diff_ci_high']:.2f}]",
                    transform=ax.transAxes, ha="center", va="top", fontsize=8.5,
                    bbox=dict(boxstyle="round", fc="white", ec="grey", alpha=0.9))
    fig.suptitle("Outcome distributions (diamond = mean ± 95% bootstrap CI; grey lines link the same student)",                 fontsize=10.5, y=1.02)
    fig.tight_layout()
    return fig


def make_all(data, traj, effects, cfg: dict, outdir: str | Path = "reports/figures") -> list[Path]:
    paths = []
    f1 = fig1_latency_vs_load(traj, n_pairs=data["participant_id"].nunique())
    paths += save_figure(f1, "fig1_latency_vs_load", outdir)
    plt.close(f1)
    f2 = fig2_distribution_boxplot(data, effects, cfg)
    paths += save_figure(f2, "fig2_distribution_boxplot", outdir)
    plt.close(f2)
    return paths


if __name__ == "__main__":
    from src.process_data import load_config, run_pipeline, score_trajectory
    cfg = load_config("configs/task3_config.json")
    res = run_pipeline(cfg)
    for p in make_all(res["data"], score_trajectory(res["data"], cfg), res["effects"], cfg):
        print("saved", p)
