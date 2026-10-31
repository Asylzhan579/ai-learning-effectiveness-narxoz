"""Generate the SYNTHETIC placeholder dataset ``data/raw/test_run.jsonl``.

IMPORTANT: this is *simulated* data used to verify the pipeline end-to-end
before/while real participant data are collected. It contains no real students
and its results must NOT be reported as scientific findings.

Replace ``data/raw/test_run.jsonl`` with the real (pseudonymised) records using
the same schema and re-run the notebook -- nothing else has to change.

Usage:  python -m src.generate_sample_data
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

SEED = 42
N_PARTICIPANTS = 20
SEQUENCES = {
    "AI-A>Conv-B": [("AI", "A"), ("Conventional", "B")],
    "AI-B>Conv-A": [("AI", "B"), ("Conventional", "A")],
    "Conv-A>AI-B": [("Conventional", "A"), ("AI", "B")],
    "Conv-B>AI-A": [("Conventional", "B"), ("AI", "A")],
}


def _half(x: float) -> float:
    """Round to the nearest 0.5 point (marking rubric granularity)."""
    return float(np.round(x * 2) / 2)


def generate(seed: int = SEED) -> list[dict]:
    rng = np.random.default_rng(seed)
    rows: list[dict] = []
    seq_names = list(SEQUENCES)
    rid = 0
    for i in range(N_PARTICIPANTS):
        pid = f"P{i + 1:02d}"
        seq = seq_names[i % 4]
        ability = rng.normal(0, 1)

        for cond in ("AI", "Conventional"):
            pre = float(np.clip(_half(rng.normal(3.8 + 0.5 * ability, 1.2)), 0, 7))
            g = float(np.clip(rng.normal(0.28, 0.12), 0.0, 0.9))
            post = min(10.0, _half(pre + g * (10 - pre)))
            t = float(np.clip(rng.normal(34, 4), 25, 45))
            rid += 1
            rows.append(dict(record_id=rid, participant_id=pid, phase="warmup",
                             condition=cond, module="P", period=0, sequence=seq,
                             pre_score=pre, post_score=post, delayed_score=None,
                             study_time_min=round(t, 1), delayed_interval_days=None))

        for period, (cond, module) in enumerate(SEQUENCES[seq], start=1):
            base = 0.62 if cond == "AI" else 0.52
            module_eff = -0.03 if module == "B" else 0.0
            period_eff = 0.03 if period == 2 else 0.0
            pre = float(np.clip(_half(rng.normal(4.0 + 0.5 * ability, 1.2)), 0, 7))
            g = float(np.clip(base + module_eff + period_eff + 0.06 * ability
                              + rng.normal(0, 0.10), 0.05, 0.98))
            post = min(10.0, _half(pre + g * (10 - pre)))
            decay = max(0.0, rng.normal(1.3 if cond == "AI" else 1.1, 0.6))
            delayed = float(np.clip(_half(post - decay), 0, 10))
            t = float(np.clip(rng.normal(24 if cond == "AI" else 27, 2.2), 12, 30))
            rid += 1
            rows.append(dict(record_id=rid, participant_id=pid, phase="evaluation",
                             condition=cond, module=module, period=period,
                             sequence=seq, pre_score=pre, post_score=post,
                             delayed_score=delayed, study_time_min=round(t, 1),
                             delayed_interval_days=7))

    for r in rows:
        if r["participant_id"] == "P17" and r["phase"] == "evaluation" and r["condition"] == "AI":
            r["post_score"] = 11.0
    return rows


def main(out: str = "data/raw/test_run.jsonl") -> None:
    rows = generate()
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} synthetic records -> {path}")


if __name__ == "__main__":
    main()
