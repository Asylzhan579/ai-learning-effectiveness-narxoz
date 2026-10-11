#!/usr/bin/env python3
"""Transparent research measurement scaffold; Python standard library only."""
import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, stdev

REQUIRED = {"participant_id", "module_id", "order", "condition", "pre_score",
            "post_score", "delayed_score", "time_minutes", "delay_days"}

def run(config_path):
    config_file = Path(config_path).resolve()
    root = config_file.parent.parent
    cfg = json.loads(config_file.read_text(encoding="utf-8"))
    input_path = root / cfg["dataset_path"]
    output_path = root / cfg["output_path"]
    with input_path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing CSV fields: {sorted(REQUIRED - set(reader.fieldnames or []))}")
        raw = list(reader)
    if len(raw) < cfg["minimum_rows"]:
        raise ValueError("Insufficient rows")
    seen = set()
    rows = []
    for rec in raw:
        ident = rec["participant_id"].strip()
        condition = rec["condition"].strip()
        if not ident or condition not in cfg["expected_conditions"]:
            raise ValueError("Invalid participant id or condition")
        if (ident, condition) in seen:
            raise ValueError("Duplicate participant-condition pair")
        seen.add((ident, condition))
        pre, post, delayed, minutes, delay = (float(rec[k]) for k in
            ("pre_score", "post_score", "delayed_score", "time_minutes", "delay_days"))
        limit = float(cfg["max_score"])
        if not all(math.isfinite(x) for x in (pre, post, delayed, minutes, delay)):
            raise ValueError("Nonfinite numeric value")
        if not all(cfg["min_score"] <= x <= limit for x in (pre, post, delayed)):
            raise ValueError("Scores outside configured range")
        if pre >= limit:
            raise ValueError("Cannot calculate normalized gain when pre_score=max_score")
        if not (0 < minutes <= cfg["max_time_minutes"]):
            raise ValueError("Time outside configured guardrail")
        if delay != cfg["test_delay_days"]:
            raise ValueError("Delay differs from the specified protocol")
        rows.append({"participant_id": ident, "module_id": rec["module_id"],
                     "order": rec["order"], "condition": condition,
                     "gain": post-pre, "normalized_gain": (post-pre)/(limit-pre),
                     "delayed_score": delayed, "gain_per_minute": (post-pre)/minutes,
                     "time_minutes": minutes})
    grouped = {}
    for row in rows:
        grouped.setdefault(row["participant_id"], {})[row["condition"]] = row
    if any(set(v) != set(cfg["expected_conditions"]) for v in grouped.values()):
        raise ValueError("Each participant must have both crossover conditions")
    paired_ids = sorted(grouped)
    diffs = [grouped[p]["ai"]["normalized_gain"] - grouped[p]["conventional"]["normalized_gain"]
             for p in paired_ids]
    def means(key):
        return {c: round(mean(grouped[p][c][key] for p in paired_ids), 6)
                for c in cfg["expected_conditions"]}
    output = {
      "status": "pipeline_smoke_test_complete", "data_kind": "synthetic_example_not_research_evidence",
      "n_participants": len(paired_ids), "n_rows": len(rows),
      "primary_metric": cfg["primary_metric"],
      "primary_effect_ai_minus_conventional": round(mean(diffs), 6),
      "paired_difference_sd": round(stdev(diffs), 6) if len(diffs)>1 else None,
      "mean_normalized_learning_gain": means("normalized_gain"),
      "mean_delayed_score": means("delayed_score"),
      "mean_gain_per_minute": means("gain_per_minute"),
      "mean_time_minutes": means("time_minutes"),
      "guardrails": {"missing_value_rate": 0.0,
          "missing_rate_pass": 0.0 <= cfg["max_missing_rate"],
          "all_times_within_limit": True, "seven_day_retention_interval_verified": True},
      "interpretation": "This output confirms calculation and logging only. No hypothesis test or causal claim is valid on synthetic sample."
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"Saved: {output_path}")
    return output

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="configs/config.json")
    args = ap.parse_args()
    run(args.config)
