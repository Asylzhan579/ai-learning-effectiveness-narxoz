import unittest
from pathlib import Path
from src.benchmark import run

class SmokeTest(unittest.TestCase):
    def test_example_pipeline(self):
        root = Path(__file__).resolve().parents[1]
        result = run(root / "configs/config.json")
        self.assertEqual(result["n_participants"], 4)
        self.assertEqual(result["n_rows"], 8)
        self.assertTrue(result["guardrails"]["missing_rate_pass"])
        self.assertEqual(result["data_kind"], "synthetic_example_not_research_evidence")

if __name__ == "__main__":
    unittest.main()
