"""Generate Phase 3C comparison tables from frozen out-of-fold predictions."""
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                             brier_score_loss, f1_score, precision_score,
                             recall_score, roc_auc_score)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "ai_lab/ml_dataset_v2"
PRIMARY = "profitable_after_fees"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def score(y, p):
    pred = p >= .5
    return {"n": len(y), "prevalence": y.mean(), "mean_probability": p.mean(),
            "roc_auc": roc_auc_score(y, p), "pr_auc_ap": average_precision_score(y, p),
            "balanced_accuracy": balanced_accuracy_score(y, pred),
            "precision": precision_score(y, pred, zero_division=0),
            "recall": recall_score(y, pred, zero_division=0),
            "f1": f1_score(y, pred, zero_division=0), "brier": brier_score_loss(y, p)}


def f(value, digits=3):
    return "—" if pd.isna(value) else f"{value:.{digits}f}"


def main():
    assert subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() == "ai-lab-development"
    d = pd.read_parquet(SOURCE / "data/A_portfolio.parquet")
    pred = pd.read_parquet(HERE / "results/predictions.parquet")
    fold = pd.DataFrame(json.loads((HERE / "results/fold-metrics.json").read_text()))
    econ = pd.read_csv(HERE / "results/economics.csv")
    lookup = d.set_index("row_id")
    fold.to_csv(HERE / "reports/all-fold-metrics.csv", index=False)

    pair_rows = []
    for key, group in pred.groupby(["target", "feature_set", "model", "evaluation_year"]):
        target, feature_set, model, year = key
        for pair in ["BTC/USDT", "ETH/USDT"]:
            ids = group.row_id.map(lookup.pair).eq(pair)
            rows = group.loc[ids]
            y = lookup.loc[rows.row_id, target].to_numpy()
            pair_rows.append({"target": target, "feature_set": feature_set, "model": model,
                              "evaluation_year": int(year), "pair": pair,
                              **score(y, rows.probability.to_numpy())})
    pairs = pd.DataFrame(pair_rows)
    pairs.to_csv(HERE / "reports/pair-classification-metrics.csv", index=False)

    primary = fold[fold.target == PRIMARY].copy()
    dummy = primary[primary.model == "dummy"][["evaluation_year", "feature_set", "pr_auc_ap"]].rename(columns={"pr_auc_ap": "dummy_ap"})
    primary = primary.merge(dummy, on=["evaluation_year", "feature_set"])
    summary = primary.groupby(["feature_set", "model"]).agg(
        mean_roc_auc=("roc_auc", "mean"), median_roc_auc=("roc_auc", "median"),
        worst_roc_auc=("roc_auc", "min"), mean_pr_auc=("pr_auc_ap", "mean"),
        mean_brier=("brier", "mean"), mean_ece=("ece_5_bins", "mean"),
        years_roc_above_half=("roc_auc", lambda x: int((x > .5).sum())),
        years_ap_above_dummy=("pr_auc_ap", lambda x: 0),
    ).reset_index()
    ap_counts = primary.assign(beat=primary.pr_auc_ap > primary.dummy_ap).groupby(["feature_set", "model"]).beat.sum()
    summary["years_ap_above_dummy"] = [int(ap_counts.loc[(r.feature_set, r.model)]) for r in summary.itertuples()]
    summary.to_csv(HERE / "reports/classification-summary.csv", index=False)

    coefficients = pd.read_csv(HERE / "results/logistic-coefficients.csv")
    coefficient_rows, rank_rows = [], []
    for feature_set, group in coefficients.groupby("feature_set"):
        pivot = group.pivot_table(index="feature", columns="evaluation_year", values="coefficient")
        for feature, values in pivot.iterrows():
            nonzero = values.dropna()
            coefficient_rows.append({"feature_set": feature_set, "feature": feature,
                "mean_coefficient": nonzero.mean(), "std_coefficient": nonzero.std(),
                "positive_fold_fraction": (nonzero > 0).mean(),
                "same_sign_all_folds": bool((nonzero > 0).all() or (nonzero < 0).all()),
                "mean_absolute_rank": nonzero.abs().rank(ascending=False).mean()})
        correlations = []
        for left in pivot.columns:
            for right in pivot.columns:
                if left < right:
                    correlations.append(spearmanr(pivot[left], pivot[right]).statistic)
        rank_rows.append({"feature_set": feature_set,
                          "median_fold_rank_correlation": np.nanmedian(correlations),
                          "minimum_fold_rank_correlation": np.nanmin(correlations)})
    pd.DataFrame(coefficient_rows).to_csv(HERE / "reports/logistic-coefficient-stability.csv", index=False)
    pd.DataFrame(rank_rows).to_csv(HERE / "reports/logistic-rank-stability.csv", index=False)

    yearly = econ[(econ.target == PRIMARY) & (econ.period == "year")].copy()
    aggregate = econ[(econ.target == PRIMARY) & (econ.period == "aggregate")].copy()
    yearly.to_csv(HERE / "reports/primary-economic-yearly.csv", index=False)
    aggregate.to_csv(HERE / "reports/primary-economic-aggregate.csv", index=False)
    base_ids = pred[(pred.target == PRIMARY) & (pred.feature_set == "A_all") & (pred.model == "dummy")].row_id.unique()
    base = d[d.row_id.isin(base_ids)]
    baseline_year = base.groupby("year").agg(trades=("row_id", "size"), net_profit_usdt=("net_profit_usdt", "sum"),
        win_rate_pct=(PRIMARY, lambda x: x.mean() * 100)).reset_index()
    baseline_year.to_csv(HERE / "reports/unfiltered-baseline-by-year.csv", index=False)

    all_logistic_55 = yearly[(yearly.feature_set == "A_all") & (yearly.model == "logistic") & (yearly.threshold == .55)]
    all_primary = primary[primary.feature_set == "A_all"]
    mean_table = summary[summary.feature_set == "A_all"].set_index("model")
    ablation = summary[summary.model == "logistic"].sort_values("feature_set")
    pair_summary = pairs[(pairs.target == PRIMARY) & (pairs.feature_set == "A_all")].groupby(["model", "pair"])[["roc_auc", "pr_auc_ap", "brier"]].mean().reset_index()
    importance = pd.read_csv(HERE / "results/importance-stability.csv")
    coeff_rank = pd.DataFrame(rank_rows)

    lines = ["# Phase 3C review", "",
        "The larger dataset produces more encouraging development evidence, especially for conservative logistic regression,",
        "but it does not establish deployable ML. All 2019–2024 years are observed development evidence; there is no pristine holdout result.", "",
        "## Exact chronological folds", "",
        "| Evaluation | Train rows | Evaluation rows | Purged | Right-edge exclusions |", "| ---: | ---: | ---: | ---: | ---: |"]
    for item in json.loads((HERE / "audits/fold-audit.json").read_text()):
        lines.append(f"| {item['evaluation_year']} | {item['train_rows']} | {item['test_rows']} | {item['purged_train']} | {item['right_boundary_test_exclusions']} |")
    lines += ["", "The 48-hour embargo and label-end purge are applied from the frozen Phase 3B row-ID manifests.", "",
              "## Primary target: all-feature fold results", "",
              "| Year | Model | ROC-AUC | PR-AUC | Balanced accuracy | Brier | ECE |", "| ---: | --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in all_primary.sort_values(["evaluation_year", "model"]).itertuples():
        lines.append(f"| {row.evaluation_year} | {row.model} | {f(row.roc_auc)} | {f(row.pr_auc_ap)} | {f(row.balanced_accuracy)} | {f(row.brier)} | {f(row.ece_5_bins)} |")
    lines += ["", "## Across-year classification summary: all features", "",
              "| Model | Mean ROC-AUC | Worst ROC-AUC | Mean PR-AUC | Mean Brier | Years ROC > 0.5 | Years AP > Dummy |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for model, row in mean_table.iterrows():
        lines.append(f"| {model} | {f(row.mean_roc_auc)} | {f(row.worst_roc_auc)} | {f(row.mean_pr_auc)} | {f(row.mean_brier)} | {int(row.years_roc_above_half)}/5 | {int(row.years_ap_above_dummy)}/5 |")
    lines += ["", "## Logistic feature-set comparison", "",
              "| Feature set | Mean ROC-AUC | Worst ROC-AUC | Mean PR-AUC | Mean Brier | AP beats Dummy |",
              "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in ablation.itertuples():
        lines.append(f"| {row.feature_set} | {f(row.mean_roc_auc)} | {f(row.worst_roc_auc)} | {f(row.mean_pr_auc)} | {f(row.mean_brier)} | {int(row.years_ap_above_dummy)}/5 |")
    lines += ["", "## Prespecified 0.55 threshold: all-feature logistic economics", "",
              "| Year | Trades | Retained | Win rate | Net USDT | Avg trade | Profit factor | Drawdown | BTC | ETH |",
              "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for row in all_logistic_55.sort_values("evaluation_year").itertuples():
        lines.append(f"| {int(row.evaluation_year)} | {row.trades} | {f(row.retention_pct,1)}% | {f(row.win_rate_pct,1)}% | {f(row.net_profit_usdt)} | {f(row.average_trade_pct)}% | {f(row.profit_factor)} | {f(row.closed_subset_max_drawdown_pct)}% | {f(row.btc_net_usdt)} | {f(row.eth_net_usdt)} |")
    agg = aggregate[(aggregate.feature_set == "A_all") & (aggregate.model == "logistic") & (aggregate.threshold == .55)].iloc[0]
    lines += [f"", f"Aggregate: {int(agg.trades)} trades ({agg.retention_pct:.1f}% retained), {agg.net_profit_usdt:.3f} USDT, "
              f"median year {agg.median_yearly_net_usdt:.3f}, worst year {agg.worst_year_net_usdt:.3f}, "
              f"{int(agg.profitable_years)}/5 profitable years. This threshold was prespecified; it was not selected after seeing these years.", "",
              "## Pair classification", "",
              "| Model | Pair | Mean ROC-AUC | Mean PR-AUC | Mean Brier |", "| --- | --- | ---: | ---: | ---: |"]
    for row in pair_summary.itertuples():
        lines.append(f"| {row.model} | {row.pair} | {f(row.roc_auc)} | {f(row.pr_auc_ap)} | {f(row.brier)} |")
    lines += ["", "## Stability and interpretation", "",
        f"Logistic coefficient fold-rank stability for all features: median {coeff_rank.loc[coeff_rank.feature_set=='A_all','median_fold_rank_correlation'].iloc[0]:.3f}; "
        f"minimum {coeff_rank.loc[coeff_rank.feature_set=='A_all','minimum_fold_rank_correlation'].iloc[0]:.3f}.",
        f"Block-permutation importance median year-rank correlation: logistic {importance[(importance.model=='logistic')&(importance.pair=='ALL')].median_year_rank_correlation.iloc[0]:.3f}, "
        f"forest {importance[(importance.model=='forest')&(importance.pair=='ALL')].median_year_rank_correlation.iloc[0]:.3f}, "
        f"hist-gradient {importance[(importance.model=='hist_gradient')&(importance.pair=='ALL')].median_year_rank_correlation.iloc[0]:.3f}.",
        "Those near-zero correlations show unstable explanatory structure despite better average predictions.", "",
        "The expanded sample improves development evidence relative to Phase 3A: all-feature logistic ROC-AUC exceeds 0.5 in all five folds",
        "and PR-AUC exceeds the contemporaneous Dummy in all five. Forest does so in four years; 2023 remains weak.",
        "Several prespecified logistic thresholds improve pooled economics and four of five years, but rows and labels overlap,",
        "importance is unstable, and no untouched holdout was evaluated. This is evidence worth preserving, not enough to integrate ML into trading.", "",
        "## Required conclusions", "",
        "1. Expansion from 422 to 1,271 examples improves the development evidence: logistic ROC-AUC and PR-AUC beat Dummy in every annual fold.",
        "2. Logistic is the most consistent ranker. Forest is competitive and better calibrated on average, but misses Dummy PR-AUC in 2023. Hist-gradient is less stable.",
        "3. Logistic beats Dummy classification across multiple years; its all-feature mean Brier score is worse than Dummy, so probability calibration does not improve consistently.",
        "4. The prespecified logistic 0.55 threshold is profitable in four years and improves net P/L versus the unfiltered baseline in three years. It worsens 2020 and 2023.",
        "5. Economic gains are not confined to one year, but much of the benefit comes from avoiding losses in 2021 and 2022; only 81 trades are retained.",
        "6. BTC and ETH are not materially contradictory. Logistic mean ROC-AUC is 0.583 for BTC and 0.572 for ETH; ETH has higher PR-AUC because its fold prevalence/ranking differs.",
        "7. Regime fields add small average logistic value (ROC-AUC +0.007, PR-AUC +0.009 versus exclusion), but the gain is too small and unstable to call decisive. Calendar exclusion is essentially neutral.",
        "8. Calibration varies by year. Logistic coefficient ranks are moderately stable, while time-block permutation ranks are near zero across years; explanatory importance is not stable.",
        "9. Nonstationarity and overfitting risk remain clear: 2023 is weak, calibration shifts, feature importance changes, labels overlap, and all years have informed development.",
        "10. There is not enough evidence to integrate ML into the strategy. The evidence supports preserving a frozen candidate for a later genuinely sealed evaluation.", "",
        "Complete results are in fold-metrics.json, prediction-calibration-by-year.json, primary-economic-yearly.csv,",
        "primary-economic-aggregate.csv, and pair-classification-metrics.csv. Secondary-target results remain in the full result files."]
    (HERE / "reports/summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    files = sorted(p for p in HERE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
    inventory = HERE / "reports/file-inventory.txt"
    manifest = HERE / "audits/artifact-sha256.json"
    paths = sorted(set(files + [inventory, manifest]))
    inventory.write_text("\n".join(p.relative_to(ROOT).as_posix() for p in paths) + "\n", encoding="utf-8")
    manifest.write_text(json.dumps({p.relative_to(HERE).as_posix(): sha(p) for p in paths if p != manifest}, indent=2) + "\n")
    print("\n".join(lines[:65]))


if __name__ == "__main__":
    main()
