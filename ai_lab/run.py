"""Run the three approved Phase 1 operations from the repository root."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
LAB = ROOT / "ai_lab"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("download", "backtest", "dry-run"))
    args = parser.parse_args()
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=ROOT, text=True
    ).strip()
    if branch != "ai-lab-development":
        parser.error("Current branch must be ai-lab-development.")
    if any(key.startswith("FREQTRADE__") for key in os.environ):
        parser.error("Remove FREQTRADE__ environment overrides before running Phase 1.")
    name = "dry-run" if args.action == "dry-run" else "backtest"
    path = LAB / "configs" / (name + ".json")
    config = json.loads(path.read_text())
    if (config.get("dry_run") is not True
            or config.get("trading_mode") != "spot"
            or config.get("exchange", {}).get("pair_whitelist") != ["BTC/USDT", "ETH/USDT"]
            or any(config["exchange"].get(k) for k in ("key", "secret", "password"))
            or config.get("add_config_files")
            or config.get("api_server", {}).get("enabled")
            or config.get("telegram", {}).get("enabled")):
        parser.error("Config violates Phase 1 paper-trading requirements.")
    command = {"download": "download-data", "backtest": "backtesting", "dry-run": "trade"}[args.action]
    cmd = [sys.executable, "-m", "freqtrade", command,
           "--config", str(path), "--userdir", str(LAB),
           "--datadir", str(LAB / "data"),
           "--logfile", str(LAB / "logs" / (args.action + ".log"))]
    if args.action == "download":
        cmd += ["--pairs", "BTC/USDT", "ETH/USDT", "--timeframes", "1h",
                "--timerange", "20241201-20250401"]
    else:
        cmd += ["--strategy", "LabBaseline", "--strategy-path", str(LAB / "strategies")]
    if args.action == "backtest":
        cmd += ["--timerange", "20250101-20250401", "--fee", "0.001",
                "--cache", "none", "--export", "trades",
                "--backtest-directory", str(LAB / "results")]
    if args.action == "dry-run":
        cmd += ["--dry-run", "--db-url", "sqlite:///ai_lab/results/dry-run.sqlite"]
    return subprocess.call(cmd, cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
