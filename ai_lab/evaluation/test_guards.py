"""Offline regression tests for chronological split and execution safeguards."""
from copy import deepcopy
import os
import unittest
from unittest.mock import patch

import evaluate


class Guards(unittest.TestCase):
    def test_current_protocol(self):
        evaluate.check_ranges()
        evaluate.guard()

    def test_primary_overlap_rejected(self):
        p = deepcopy(evaluate.P)
        p["splits"]["test"][0] = "20240601"
        with patch.object(evaluate, "P", p), self.assertRaises(AssertionError):
            evaluate.check_ranges()

    def test_future_fold_rejected(self):
        p = deepcopy(evaluate.P)
        p["walk_forward"][0]["development"][1] = "20230801"
        with patch.object(evaluate, "P", p), self.assertRaises(AssertionError):
            evaluate.check_ranges()

    def test_wrong_branch_rejected(self):
        with patch("subprocess.check_output", return_value="develop\n"), self.assertRaises(AssertionError):
            evaluate.guard()

    def test_environment_override_rejected(self):
        with patch.dict(os.environ, {"FREQTRADE__DRY_RUN": "false"}), self.assertRaises(AssertionError):
            evaluate.guard()

    def test_changed_strategy_rejected(self):
        p = deepcopy(evaluate.P)
        p["strategy_sha256"] = "changed"
        with patch.object(evaluate, "P", p), self.assertRaises(AssertionError):
            evaluate.guard()


if __name__ == "__main__":
    unittest.main(verbosity=2)
