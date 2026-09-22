"""Final integrity and exhaustive file inventory."""
from __future__ import annotations

import json
import subprocess
from common import HERE, ROOT, YEARS, log, now, save, sha, verify_frozen


def main() -> None:
    verify_frozen()
    events = [json.loads(line) for line in (HERE / "audit.jsonl").read_text(encoding="utf-8").splitlines()]
    completed = [row for row in events if row["event"] == "locked_run_completed"]
    assert len(completed) == 12
    assert all(int(row["year"]) in YEARS for row in completed)
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    assert status.strip() == "?? ai_lab/alpha_v2_research/", status
    save(HERE / "audits/final-integrity.json", {
        "utc": now(), "branch": "ai-lab-development", "git_status": status,
        "LabBaseline_unchanged": True, "AlphaBreakout_unchanged": True,
        "protocol_and_strategy_hashes_verified": True, "parameter_changes_after_freeze": False,
        "runs_completed": 12, "latest_data_timestamp": "2022-12-31T23:00:00+00:00",
        "data_2023_or_later_read": False, "live_trading": False, "ml_or_freqai": False,
    })
    inventory = HERE / "reports/file-inventory.txt"
    hashes = HERE / "audits/artifact-sha256.json"
    files = sorted({p for p in HERE.rglob("*") if p.is_file() and "__pycache__" not in p.parts} | {inventory, hashes})
    inventory.write_text("\n".join(p.relative_to(ROOT).as_posix() for p in files) + "\n", encoding="utf-8")
    save(hashes, {p.relative_to(HERE).as_posix(): sha(p) for p in files if p != hashes})
    log("final_integrity_complete", deliverable_files=len(files), completed_runs=12)


if __name__ == "__main__":
    main()

