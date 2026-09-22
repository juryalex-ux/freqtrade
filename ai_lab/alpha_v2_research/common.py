"""Phase 5A constants and integrity helpers."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
YEARS = (2019, 2020, 2021, 2022)
CENTRAL = ("V2TrendPullback", "V2CompressionBreakout", "V2RegimeAdaptive")
VARIANTS = tuple(name + suffix for name in CENTRAL for suffix in ("Lo", "Hi"))
REFERENCES = ("LabBaseline", "AlphaBreakout")
BASELINE_SHA = "e7e32ae09ae5f6584afad52428f0f648e4f33dd92f352b6d04b763ad2c2e234c"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, default=str, allow_nan=False) + "\n", encoding="utf-8")


def log(event: str, **values) -> None:
    row = {"utc": now(), "event": event, **values}
    with (HERE / "audit.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, default=str) + "\n")
    print(json.dumps(row, default=str), flush=True)


def guard() -> None:
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    assert branch == "ai-lab-development", branch
    changed = subprocess.check_output(["git", "diff", "HEAD", "--name-only"], cwd=ROOT, text=True).splitlines()
    forbidden = [name for name in changed if not name.replace("\\", "/").startswith("ai_lab/alpha_v2_research/")]
    assert not forbidden, forbidden
    assert sha(ROOT / "ai_lab/strategies/LabBaseline.py") == BASELINE_SHA


def verify_frozen() -> dict:
    guard()
    protocol = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))
    for relative, digest in protocol["code_hashes"].items():
        assert sha(HERE / relative) == digest, relative
    for relative, digest in protocol["reference_hashes"].items():
        assert sha(ROOT / relative) == digest, relative
    return protocol

