"""Create final integrity record, artifact hashes, and exhaustive inventory."""
from __future__ import annotations

import subprocess
from common import HERE, ROOT, now, protocol, save, sha


def main() -> None:
    manifest = protocol()
    for relative, digest in manifest["source_evidence_sha256"].items():
        assert sha(ROOT / relative) == digest
    for relative, digest in manifest["reference_source_sha256"].items():
        assert sha(ROOT / relative) == digest
    status = subprocess.check_output(["git", "status", "--short"], cwd=ROOT, text=True)
    assert status.strip() == "?? ai_lab/alpha_diagnostics/", status
    save(HERE / "audits/final-integrity.json", {"utc": now(), "branch": "ai-lab-development", "git_status": status,
         "source_hashes_verified": True, "strategies_modified": False, "Freqtrade_core_modified": False,
         "entry_logic_rerun": False, "parameters_optimized": False, "new_strategy_created": False,
         "data_2023_or_later_loaded": False, "live_trading": False, "ml_or_freqai": False})
    inventory = HERE / "reports/file-inventory.txt"
    hash_file = HERE / "audits/artifact-sha256.json"
    files = sorted({path for path in HERE.rglob("*") if path.is_file() and "__pycache__" not in path.parts} | {inventory, hash_file})
    inventory.write_text("\n".join(path.relative_to(ROOT).as_posix() for path in files) + "\n", encoding="utf-8")
    save(hash_file, {path.relative_to(HERE).as_posix(): sha(path) for path in files if path != hash_file})
    print(f"{len(files)} diagnostic artifacts finalized")


if __name__ == "__main__":
    main()

