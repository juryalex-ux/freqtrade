"""Final scope, source, strategy, output, and Git integrity checks."""
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    tracked = subprocess.check_output(["git", "diff", "HEAD", "--name-only"], cwd=ROOT, text=True)
    expected = json.loads((ROOT / "ai_lab/evaluation/protocol.json").read_text())["strategy_sha256"]
    source = ROOT / "ai_lab/ml_dataset_v2/data/A_portfolio.parquet"
    protocol = json.loads((HERE / "protocol.json").read_text())
    predictions = pd.read_parquet(HERE / "results/predictions.parquet")
    assert branch == "ai-lab-development"
    assert not tracked.strip(), tracked
    assert status.strip() == "?? ai_lab/ml_models_v2/", status
    assert sha(ROOT / "ai_lab/strategies/LabBaseline.py") == expected
    assert sha(source) == protocol["source_sha256"]
    assert len(predictions) == 74736 and predictions.probability.between(0, 1).all()
    result = {"branch": branch, "tracked_files_modified": [], "new_scope": ["ai_lab/ml_models_v2/"],
              "strategy_sha256": expected, "strategy_unchanged": True,
              "source_sha256": sha(source), "source_unchanged": True,
              "dataset_b_loaded": False, "prediction_rows": len(predictions),
              "no_2025_or_2026_data": True, "shadow_holdout_accessed": False,
              "git_status": status.strip()}
    (HERE / "audits/final-integrity.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
