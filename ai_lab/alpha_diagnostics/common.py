"""Paths and integrity helpers for Phase 5B diagnostics."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "ai_lab/alpha_v2_research"
STRATEGIES = ("LabBaseline", "AlphaBreakout", "V2TrendPullback", "V2CompressionBreakout", "V2RegimeAdaptive")
YEARS = (2019, 2020, 2021, 2022)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str, allow_nan=False) + "\n", encoding="utf-8")


def guard() -> None:
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    assert branch == "ai-lab-development", branch
    changed = subprocess.check_output(["git", "diff", "HEAD", "--name-only"], cwd=ROOT, text=True).splitlines()
    forbidden = [name for name in changed if not name.replace("\\", "/").startswith("ai_lab/alpha_diagnostics/")]
    assert not forbidden, forbidden


def protocol() -> dict:
    guard()
    return json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))

