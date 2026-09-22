"""Audit archived locked backtest outputs without executing another backtest."""

from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

from common import log

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def strategy_payload(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".json") and not name.endswith("_config.json")]
        if len(names) != 1:
            raise ValueError(f"Expected one result JSON in {path}, found {names}")
        return json.loads(archive.read(names[0]))["strategy"]


def main() -> None:
    periods: dict[str, dict] = {}
    for period_dir in sorted(path for path in RESULTS.iterdir() if path.is_dir()):
        archives = sorted(period_dir.glob("backtest-result-*.zip"))
        payloads = [strategy_payload(path) for path in archives]
        equivalent = len({json.dumps(payload, sort_keys=True, separators=(",", ":")) for payload in payloads}) <= 1
        summaries = []
        for payload in payloads:
            summaries.append(
                {
                    name: {
                        key: result.get(key)
                        for key in ("total_trades", "wins", "losses", "profit_total_abs", "profit_total", "profit_factor")
                    }
                    for name, result in sorted(payload.items())
                }
            )
        economics_identical = len({json.dumps(summary, sort_keys=True, separators=(",", ":")) for summary in summaries}) <= 1
        periods[period_dir.name] = {
            "archive_count": len(archives),
            "archives": [{"name": path.name, "sha256": sha256(path)} for path in archives],
            "all_strategy_payloads_identical": equivalent,
            "economic_summaries_identical": economics_identical,
            "strategy_summaries": summaries,
            "canonical_metrics": "metrics.json",
            "note": (
                "Multiple locked executions were retained for audit; the full payload metadata differs, but all reported economic summaries are identical."
                if len(archives) > 1 and economics_identical
                else "One archived locked execution."
                if len(archives) == 1
                else "Multiple archived outputs require review."
            ),
        }
    output = {
        "purpose": "Post-run archive integrity audit; no backtest was executed by this script.",
        "periods": periods,
    }
    target = ROOT / "audits" / "backtest-run-audit.json"
    target.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    log("backtest_archive_audit", physical_archives=sum(x["archive_count"] for x in periods.values()),
        economic_summaries_identical_for_duplicate_C=periods["C_2025_to_2026Q1"]["economic_summaries_identical"])
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
