"""Execute only the frozen annual and fee-sensitivity matrix."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import zipfile
from common import HERE, ROOT, YEARS, CENTRAL, VARIANTS, REFERENCES, log, save, sha, verify_frozen


def execute(label: str, year: int, fee: float, strategies: tuple[str, ...]) -> None:
    output = HERE / "results" / label / str(year)
    output.mkdir(parents=True, exist_ok=True)
    assert not list(output.glob("*.zip")), output
    cmd = [sys.executable, "-B", "-m", "freqtrade", "backtesting", "--config", str(HERE / "backtest.json"),
           "--userdir", str(HERE), "--datadir", str(HERE / "data"),
           "--strategy-list", *strategies, "--timerange", f"{year}0101-{year + 1}0101",
           "--fee", str(fee), "--cache", "none", "--export", "trades", "--backtest-directory", str(output)]
    save(output / "command.json", cmd)
    log("locked_run_started", label=label, year=year, fee=fee, strategies=list(strategies))
    with (output / "output.log").open("w", encoding="utf-8") as handle:
        subprocess.run(cmd, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT, check=True,
                       env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    archive = next(output.glob("*.zip"))
    with zipfile.ZipFile(archive) as zipped:
        result_name = next(name for name in zipped.namelist() if name.endswith(".json") and not name.endswith("_config.json"))
        result = json.loads(zipped.read(result_name))["strategy"]
    assert set(result) == set(strategies)
    save(output / "metrics.json", result)
    verify_frozen()
    log("locked_run_completed", label=label, year=year, archive_sha256=sha(archive))


def main() -> None:
    protocol = verify_frozen()
    assert protocol["research_window"]["scored"][1] == "2023-01-01"
    assert not any(key.startswith("FREQTRADE__") for key in os.environ)
    for year in YEARS:
        execute("main_fee_0.10pct", year, 0.001, (*CENTRAL, *VARIANTS, *REFERENCES))
    for fee, label in ((0.0015, "fee_0.15pct"), (0.002, "fee_0.20pct")):
        for year in YEARS:
            execute(label, year, fee, CENTRAL)


if __name__ == "__main__":
    main()
