"""Data processing and statistical aggregation (TASK 3).

Pipeline:  raw .jsonl -> warm-up filtering -> guardrail validation ->
derived metrics -> descriptive stats (median, p25/p75, p95, p99, mean+-SD,
bootstrap 95% CI) -> paired AI-vs-Conventional effects -> CSV/JSON outputs.

All randomness (bootstrap, permutation test) is driven by a fixed seed (42).

CLI:  python -m src.process_data --config configs/task3_config.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

SEED = 42
CONDITIONS = ("AI", "Conventional")
REQUIRED_FIELDS = ["participant_id", "phase", "condition", "module", "period",
                   "pre_score", "post_score", "delayed_score",
                   "study_time_min", "delayed_interval_days"]
SCORE_FIELDS = ["pre_score", "post_score", "delayed_score"]

DEFAULT_CONFIG = {
    "seed": SEED, "n_boot": 10000, "n_perm": 20000, "ci_level": 0.95,
    "max_score": 10, "max_study_minutes": 30, "required_delay_days": 7,
    "max_error_rate": 0.05,
    "raw_path": "data/raw/test_run.jsonl",
    "summary_path": "data/processed/metrics_summary.csv",
    "effects_path": "data/processed/paired_effects.csv",
    "guardrail_path": "data/processed/guardrail_report.json",
    "excluded_path": "data/processed/excluded_records.csv",
}

# metric -> (display label with unit, alternative hypothesis for paired test)
METRICS = {
    "norm_gain": ("Normalized immediate gain (unitless)", "greater"),     # RQ1 primary
    "delayed_score": ("Day-7 delayed score (points, 0-10)", "greater"),   # RQ2
    "efficiency": ("Learning efficiency (points/min)", "greater"),        # RQ3
    "study_time_min": ("Study time (min)", "two-sided"),                  # descriptive
}


# ----------------------------------------------------------------------------
# 1. Ingestion, warm-up filtering, guardrails
# ----------------------------------------------------------------------------
def load_config(path: str | Path | None = None) -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if path:
        cfg.update(json.loads(Path(path).read_text(encoding="utf-8")))
    return cfg


def load_jsonl(path: str | Path) -> pd.DataFrame:
    """Load a JSON-lines file into a DataFrame (one record per line)."""
    with Path(path).open(encoding="utf-8") as fh:
        rows = [json.loads(line) for line in fh if line.strip()]
    return pd.DataFrame(rows)


def split_warmup(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separate warm-up (familiarisation / 'cold') runs from evaluation runs."""
    warm = df[df["phase"] == "warmup"].copy()
    evaluation = df[df["phase"] == "evaluation"].copy()
    return warm, evaluation


def validate_records(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Apply guardrail rules. Invalid rows are NOT silently dropped: they are
    returned (with a reason) and counted as the *error rate* guardrail metric."""
    mx = cfg["max_score"]
    reasons: list[list[str]] = [[] for _ in range(len(df))]
    df = df.reset_index(drop=True)
    for i, row in df.iterrows():
        missing = [c for c in REQUIRED_FIELDS if c not in df.columns or pd.isna(row.get(c))]
        if missing:
            reasons[i].append("missing:" + ",".join(missing))
        for c in SCORE_FIELDS:
            v = row.get(c)
            if pd.notna(v) and not (0 <= v <= mx):
                reasons[i].append(f"{c}_out_of_range")
        t = row.get("study_time_min")
        if pd.notna(t) and not (0 < t <= cfg["max_study_minutes"]):
            reasons[i].append("study_time_out_of_bounds")
        d = row.get("delayed_interval_days")
        if pd.notna(d) and d != cfg["required_delay_days"]:
            reasons[i].append("delay_not_7_days")
        if row.get("condition") not in CONDITIONS:
            reasons[i].append("unknown_condition")
    df["error_reason"] = ["; ".join(r) for r in reasons]
    bad = df["error_reason"] != ""
    valid, invalid = df[~bad].drop(columns="error_reason"), df[bad]
    report = {
        "n_records_checked": int(len(df)),
        "n_invalid": int(bad.sum()),
        "error_rate": float(bad.mean()) if len(df) else 0.0,
        "error_rate_by_condition": {
            c: float(bad[df["condition"] == c].mean()) if (df["condition"] == c).any() else 0.0
            for c in CONDITIONS},
        "threshold": cfg["max_error_rate"],
    }
    report["guardrail_ok"] = report["error_rate"] <= cfg["max_error_rate"]
    return valid, invalid, report


def add_derived(df: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Add normalized gain, raw gain, efficiency. Pre-test at ceiling
    (pre == max) has an undefined normalized gain -> excluded by a predefined rule."""
    mx = cfg["max_score"]
    ceiling = df["pre_score"] >= mx
    kept = df[~ceiling].copy()
    kept["raw_gain"] = kept["post_score"] - kept["pre_score"]
    kept["norm_gain"] = kept["raw_gain"] / (mx - kept["pre_score"])
    kept["efficiency"] = kept["raw_gain"] / kept["study_time_min"]
    return kept, df[ceiling]


def complete_pairs(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only participants that have a valid record in BOTH conditions."""
    counts = df.groupby("participant_id")["condition"].nunique()
    ok = counts[counts == len(CONDITIONS)].index
    return df[df["participant_id"].isin(ok)].copy()


# ----------------------------------------------------------------------------
# 2. Statistics
# ----------------------------------------------------------------------------
def bootstrap_ci(x, stat: str = "mean", n_boot: int = 10000, seed: int = SEED,
                 ci: float = 0.95) -> tuple[float, float]:
    """Percentile bootstrap CI for the mean or median (resampling with replacement)."""
    x = np.asarray(x, dtype=float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    fn = np.mean if stat == "mean" else np.median
    boots = fn(x[idx], axis=1)
    a = (1 - ci) / 2
    lo, hi = np.quantile(boots, [a, 1 - a])
    return float(lo), float(hi)


def describe(x, cfg: dict) -> dict:
    x = np.asarray(x, dtype=float)
    n_boot, ci, seed = cfg["n_boot"], cfg["ci_level"], cfg["seed"]
    m_lo, m_hi = bootstrap_ci(x, "mean", n_boot, seed, ci)
    md_lo, md_hi = bootstrap_ci(x, "median", n_boot, seed, ci)
    return {
        "n": int(len(x)), "mean": x.mean(), "sd": x.std(ddof=1),
        "median": np.median(x), "p25": np.percentile(x, 25), "p75": np.percentile(x, 75),
        "p95": np.percentile(x, 95), "p99": np.percentile(x, 99),
        "mean_ci_low": m_lo, "mean_ci_high": m_hi,
        "median_ci_low": md_lo, "median_ci_high": md_hi,
    }


def summarize_by_condition(df: pd.DataFrame, cfg: dict, metrics=None) -> pd.DataFrame:
    """Long table: one row per (metric, condition) with all aggregates."""
    rows = []
    for metric in (metrics or METRICS):
        for cond in CONDITIONS:
            vals = df.loc[df["condition"] == cond, metric].dropna()
            rows.append({"metric": metric, "label": METRICS[metric][0],
                         "condition": cond, **describe(vals, cfg)})
    return pd.DataFrame(rows).round(4)


def paired_wide(df: pd.DataFrame, metric: str) -> pd.DataFrame:
    """participant x condition table for one metric (complete pairs only)."""
    return df.pivot(index="participant_id", columns="condition", values=metric).dropna()


def _perm_pvalue(d: np.ndarray, alternative: str, n_perm: int, seed: int) -> float:
    """Paired sign-flip permutation test on the mean difference."""
    rng = np.random.default_rng(seed)
    signs = rng.choice([-1.0, 1.0], size=(n_perm, len(d)))
    perm = (signs * d).mean(axis=1)
    obs = d.mean()
    if alternative == "greater":
        cnt = (perm >= obs - 1e-12).sum()
    else:
        cnt = (np.abs(perm) >= abs(obs) - 1e-12).sum()
    return float((cnt + 1) / (n_perm + 1))


def paired_effects(df: pd.DataFrame, cfg: dict, metrics=None) -> pd.DataFrame:
    """Paired difference (AI - Conventional) with bootstrap 95% CI + tests."""
    rows = []
    for metric in (metrics or METRICS):
        label, alt = METRICS[metric]
        w = paired_wide(df, metric)
        d = (w["AI"] - w["Conventional"]).to_numpy()
        lo, hi = bootstrap_ci(d, "mean", cfg["n_boot"], cfg["seed"], cfg["ci_level"])
        t_res = stats.ttest_rel(w["AI"], w["Conventional"], alternative=alt)
        try:
            w_p = stats.wilcoxon(d, alternative=alt).pvalue
        except ValueError:  # all differences zero
            w_p = np.nan
        sd = d.std(ddof=1)
        rows.append({
            "metric": metric, "label": label, "n_pairs": int(len(d)),
            "mean_diff": d.mean(), "diff_ci_low": lo, "diff_ci_high": hi,
            "median_diff": float(np.median(d)), "sd_diff": sd,
            "cohens_dz": d.mean() / sd if sd > 0 else np.nan,
            "alternative": alt, "t_stat": t_res.statistic, "p_ttest": t_res.pvalue,
            "p_permutation": _perm_pvalue(d, alt, cfg["n_perm"], cfg["seed"]),
            "p_wilcoxon": w_p,
        })
    return pd.DataFrame(rows).round(4)


def score_trajectory(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Mean score (+ bootstrap CI) at pre / post / day-7 for each condition (Fig. 1)."""
    stages = [("pre_score", "Pretest\n(day 0)"), ("post_score", "Posttest\n(day 0)"),
              ("delayed_score", "Delayed test\n(day 7)")]
    rows = []
    for cond in CONDITIONS:
        for col, lab in stages:
            v = df.loc[df["condition"] == cond, col].dropna().to_numpy()
            lo, hi = bootstrap_ci(v, "mean", cfg["n_boot"], cfg["seed"], cfg["ci_level"])
            rows.append({"condition": cond, "stage": lab, "mean": v.mean(),
                         "ci_low": lo, "ci_high": hi, "n": len(v)})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------
# 3. Formatting helpers for README tables
# ----------------------------------------------------------------------------
def fmt_mean_sd(row, nd: int = 2) -> str:
    return f"{row['mean']:.{nd}f} ± {row['sd']:.{nd}f}"


def fmt_median_iqr(row, nd: int = 2) -> str:
    return f"{row['median']:.{nd}f} ({row['p25']:.{nd}f}–{row['p75']:.{nd}f})"


# ----------------------------------------------------------------------------
# 4. End-to-end pipeline
# ----------------------------------------------------------------------------
def run_pipeline(cfg: dict, write: bool = True) -> dict:
    np.random.seed(cfg["seed"])
    raw = load_jsonl(cfg["raw_path"])
    warm, evaluation = split_warmup(raw)
    valid, invalid, guard = validate_records(evaluation, cfg)
    derived, ceiling = add_derived(valid, cfg)
    data = complete_pairs(derived)
    summary = summarize_by_condition(data, cfg)
    effects = paired_effects(data, cfg)
    guard.update({
        "n_raw_records": int(len(raw)), "n_warmup_discarded": int(len(warm)),
        "n_ceiling_excluded": int(len(ceiling)),
        "n_pairs_analysed": int(data["participant_id"].nunique()),
    })
    if write:
        for key in ("summary_path", "effects_path", "guardrail_path", "excluded_path"):
            Path(cfg[key]).parent.mkdir(parents=True, exist_ok=True)
        summary.to_csv(cfg["summary_path"], index=False)
        effects.to_csv(cfg["effects_path"], index=False)
        invalid.to_csv(cfg["excluded_path"], index=False)
        Path(cfg["guardrail_path"]).write_text(json.dumps(guard, indent=2), encoding="utf-8")
    return dict(raw=raw, warm=warm, evaluation=evaluation, valid=valid, invalid=invalid,
                data=data, summary=summary, effects=effects, guardrails=guard)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="configs/task3_config.json")
    args = ap.parse_args()
    out = run_pipeline(load_config(args.config))
    print(json.dumps(out["guardrails"], indent=2))
    print(out["summary"].to_string(index=False))
    print(out["effects"].to_string(index=False))


if __name__ == "__main__":
    main()
