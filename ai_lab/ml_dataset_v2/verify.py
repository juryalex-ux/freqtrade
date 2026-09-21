"""Verify frozen inputs and record the complete Phase 3B artifact inventory."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip()
    assert branch == 'ai-lab-development'
    changes = subprocess.check_output(['git', 'diff', 'HEAD', '--name-only'], cwd=ROOT, text=True)
    assert not changes.strip(), changes
    expected = json.loads((ROOT/'ai_lab/evaluation/protocol.json').read_text())['strategy_sha256']
    actual = sha(ROOT/'ai_lab/strategies/LabBaseline.py')
    assert actual == expected
    before = json.loads((HERE/'audits/outcomes-before-consolidation.json').read_text())
    for name, digest in before.items():
        assert sha(HERE/'data'/name) == digest, name
    status = subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True)
    assert status.strip() == '?? ai_lab/ml_dataset_v2/', status
    result = dict(branch=branch, strategy_sha256=actual, frozen_strategy_unchanged=True,
                  tracked_files_unchanged=True, outcomes_unchanged_by_feature_consolidation=True,
                  git_status=status, scope='Only ai_lab/ml_dataset_v2 created. No holdout files read by this verifier.')
    (HERE/'audits/final-integrity.json').write_text(json.dumps(result, indent=2)+'\n')
    inventory = HERE/'reports/file-inventory.txt'
    manifest = HERE/'audits/artifact-sha256.json'
    files = sorted(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    paths = sorted(set(files+[inventory, manifest]))
    inventory.write_text('\n'.join(p.relative_to(ROOT).as_posix() for p in paths)+'\n')
    manifest.write_text(json.dumps({p.relative_to(HERE).as_posix(): sha(p) for p in paths if p != manifest}, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    print(f'{len(paths)} deliverable files; cache files excluded from inventory.')


if __name__ == '__main__':
    main()
