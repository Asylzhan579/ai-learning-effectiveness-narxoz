"""Unit tests for src/process_data.py  (run: python -m unittest discover -s tests -v)."""
import unittest

import numpy as np
import pandas as pd

from src import process_data as pdm

CFG = pdm.load_config()


def _row(**kw):
    base = dict(participant_id="P01", phase="evaluation", condition="AI", module="A",
                period=1, pre_score=4.0, post_score=8.0, delayed_score=7.0,
                study_time_min=25.0, delayed_interval_days=7)
    base.update(kw)
    return base


class TestProcessData(unittest.TestCase):
    def test_warmup_is_split_off(self):
        df = pd.DataFrame([_row(phase="warmup"), _row(), _row(condition="Conventional")])
        warm, ev = pdm.split_warmup(df)
        self.assertEqual((len(warm), len(ev)), (1, 2))

    def test_normalized_gain_formula(self):
        d, _ = pdm.add_derived(pd.DataFrame([_row(pre_score=4, post_score=8)]), CFG)
        self.assertAlmostEqual(d["norm_gain"].iloc[0], (8 - 4) / (10 - 4))

    def test_ceiling_pretest_excluded(self):
        d, c = pdm.add_derived(pd.DataFrame([_row(pre_score=10, post_score=10)]), CFG)
        self.assertEqual((len(d), len(c)), (0, 1))

    def test_guardrails_flag_bad_records(self):
        df = pd.DataFrame([_row(), _row(post_score=11), _row(study_time_min=45),
                           _row(delayed_score=None), _row(delayed_interval_days=6)])
        valid, invalid, rep = pdm.validate_records(df, CFG)
        self.assertEqual(len(valid), 1)
        self.assertEqual(rep["n_invalid"], 4)
        self.assertAlmostEqual(rep["error_rate"], 0.8)
        self.assertFalse(rep["guardrail_ok"])

    def test_only_complete_pairs_kept(self):
        df = pd.DataFrame([_row(), _row(condition="Conventional"), _row(participant_id="P02")])
        self.assertEqual(pdm.complete_pairs(df)["participant_id"].nunique(), 1)

    def test_bootstrap_is_reproducible_and_brackets_mean(self):
        x = np.arange(20, dtype=float)
        a = pdm.bootstrap_ci(x, "mean", 2000, seed=42)
        b = pdm.bootstrap_ci(x, "mean", 2000, seed=42)
        self.assertEqual(a, b)
        self.assertLess(a[0], x.mean())
        self.assertGreater(a[1], x.mean())

    def test_full_pipeline_on_sample(self):
        res = pdm.run_pipeline(CFG, write=False)
        self.assertEqual(res["guardrails"]["n_warmup_discarded"], 40)
        self.assertEqual(res["guardrails"]["n_pairs_analysed"], 19)
        self.assertTrue((res["data"]["study_time_min"] <= 30).all())


if __name__ == "__main__":
    unittest.main()
