"""Locked Phase 4B scope helpers. No ML, fitting, or parameter selection."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASELINE_SHA = 'e7e32ae09ae5f6584afad52428f0f648e4f33dd92f352b6d04b763ad2c2e234c'
PERIODS = {
    'A_2023': ('20230101', '20240101'),
    'B_2024': ('20240101', '20250101'),
    'C_2025_to_2026Q1': ('20250101', '20260401'),
    'D_2026_shadow': ('20260401', '20260901'),
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, default=str, allow_nan=False) + '\n', encoding='utf-8')


def log(event, **details):
    record = {'utc': now(), 'event': event, **details}
    with (HERE/'audit.jsonl').open('a', encoding='utf-8') as file:
        file.write(json.dumps(record, default=str) + '\n')
    print(json.dumps(record, default=str), flush=True)


def guard():
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()
    assert branch == 'ai-lab-development', branch
    changed = subprocess.check_output(['git', 'diff', 'HEAD', '--name-only'], cwd=ROOT, text=True)
    assert not changed.strip(), changed
    assert sha(ROOT/'ai_lab/strategies/LabBaseline.py') == BASELINE_SHA
    return branch


def verify_frozen():
    guard()
    frozen = json.loads((HERE/'frozen-manifest.json').read_text())
    for relative, digest in frozen['frozen_source_hashes'].items():
        assert sha(ROOT/relative) == digest, relative
    for relative, digest in frozen['validation_source_hashes'].items():
        assert sha(HERE/relative) == digest, relative
    return frozen
