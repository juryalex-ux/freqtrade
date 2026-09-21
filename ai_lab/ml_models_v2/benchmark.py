"""Conservative expanding-year benchmark over the frozen Phase 3B dataset."""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp, spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, balanced_accuracy_score,
                             brier_score_loss, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "ai_lab/ml_dataset_v2"
SCHEMA = json.loads((SOURCE / "schema.json").read_text())
ALL = SCHEMA["features"]
NUMERIC = SCHEMA["numeric_features"]
TARGETS = ["profitable_after_fees", "return_above_0_5_percent", "return_above_1_percent"]
MODELS = ["dummy", "logistic", "forest", "hist_gradient"]
THRESHOLDS = [.50, .55, .60, .65, .70]
SEED = 31415

# Fixed before fitting. These removals use formula/domain redundancy only, never outcomes.
REDUCED_REMOVALS = {
    "ema_gap": "Algebraically represented by the two close-normalized EMA distances.",
    "macd_signal_ratio": "Retain one normalized MACD component in the compact set.",
    "distance_high_24": "Retain the 168h high distance to avoid duplicate horizon families.",
    "distance_low_24": "Retain the 168h low distance to avoid duplicate horizon families.",
    "return_3h": "Retain 1h, 6h, 24h and 168h momentum horizons.",
    "return_12h": "Retain 1h, 6h, 24h and 168h momentum horizons.",
    "return_72h": "Retain 1h, 6h, 24h and 168h momentum horizons.",
    "source_synthetic": "Sparse data-quality flag, not a market feature.",
}
PRICE = [
    "ema20_distance", "ema50_distance", "ema_gap", "ema20_slope_6", "ema50_slope_6",
    "trend_efficiency_20", "range_ratio", "body_to_range", "close_location",
    "distance_high_24", "distance_low_24", "distance_high_168", "distance_low_168",
    "return_1h", "return_3h", "return_6h", "return_12h", "return_24h", "return_72h",
    "return_168h", "up_fraction_24", "pair",
]
VOL = ["natr14", "return_std_24", "return_std_168", "volatility_percentile_720",
       "volatility_ratio_24_168", "natr_ratio_168", "range_expansion_24"]
TIME = ["hour_of_day", "day_of_week"]
REGIME = ["regime", "regime_duration", "regime_transition"]
SETS = {
    "A_all": ALL,
    "B_reduced": [c for c in ALL if c not in REDUCED_REMOVALS],
    "C_price_trend": PRICE,
    "D_price_trend_volatility": PRICE + VOL,
    "E_all_excluding_regime": [c for c in ALL if c not in REGIME],
    "F_all_excluding_calendar": [c for c in ALL if c not in TIME],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, default=str, allow_nan=False) + "\n", encoding="utf-8")


def make_pipeline(name, columns):
    categorical = [c for c in columns if c in ("pair", "regime")]
    numeric = [c for c in columns if c not in categorical]
    prep = ColumnTransformer([
        ("numeric", StandardScaler(), numeric),
        ("category", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical),
    ])
    estimators = {
        "dummy": DummyClassifier(strategy="prior"),
        "logistic": LogisticRegression(C=.1, l1_ratio=0, solver="lbfgs", max_iter=2000,
                                       class_weight=None, random_state=SEED),
        "forest": RandomForestClassifier(n_estimators=160, max_depth=4, min_samples_leaf=20,
                                         max_features="sqrt", bootstrap=True, n_jobs=1,
                                         random_state=SEED),
        "hist_gradient": HistGradientBoostingClassifier(max_iter=80, learning_rate=.04,
                    max_leaf_nodes=7, max_depth=3, min_samples_leaf=20,
                    l2_regularization=12, early_stopping=False, random_state=SEED),
    }
    return Pipeline([("preprocess", prep), ("model", estimators[name])])


def metrics(y, probability):
    y = np.asarray(y, dtype=int)
    p = np.asarray(probability, dtype=float)
    pred = p >= .5
    calibration = []
    ece = 0.0
    edges = np.linspace(0, 1, 6)
    for index in range(5):
        lo, hi = edges[index], edges[index + 1]
        mask = (p >= lo) & (p <= hi if index == 4 else p < hi)
        if mask.any():
            item = {"lower": float(lo), "upper": float(hi), "n": int(mask.sum()),
                    "mean_probability": float(p[mask].mean()), "observed_rate": float(y[mask].mean())}
            calibration.append(item)
            ece += mask.mean() * abs(item["mean_probability"] - item["observed_rate"])
    return {
        "n": int(len(y)), "prevalence": float(y.mean()), "mean_probability": float(p.mean()),
        "roc_auc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None,
        "pr_auc_ap": float(average_precision_score(y, p)),
        "balanced_accuracy": float(balanced_accuracy_score(y, pred)),
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "brier": float(brier_score_loss(y, p)), "ece_5_bins": float(ece),
        "confusion_matrix": confusion_matrix(y, pred, labels=[0, 1]).tolist(),
        "calibration": calibration,
    }


def economics(frame, selected):
    chosen = frame.loc[np.asarray(selected)].sort_values(["decision_time", "pair"])
    profit = chosen.net_profit_usdt
    positive = profit[profit > 0].sum()
    negative = -profit[profit < 0].sum()
    if len(chosen):
        daily = chosen.groupby(chosen.decision_time.dt.floor("D")).net_profit_usdt.sum().sort_index()
        equity = np.r_[1000.0, 1000.0 + daily.cumsum().to_numpy()]
        peak = np.maximum.accumulate(equity)
        drawdown = float(np.max((peak - equity) / peak) * 100)
    else:
        drawdown = 0.0
    return {
        "trades": int(len(chosen)), "retention_pct": float(len(chosen) / len(frame) * 100),
        "win_rate_pct": float((profit > 0).mean() * 100) if len(chosen) else None,
        "net_profit_usdt": float(profit.sum()),
        "average_trade_pct": float(chosen.net_profit_ratio.mean() * 100) if len(chosen) else None,
        "profit_factor": float(positive / negative) if negative > 0 else None,
        "expectancy_usdt": float(profit.mean()) if len(chosen) else None,
        "closed_subset_max_drawdown_pct": drawdown,
        "btc_net_usdt": float(chosen.loc[chosen.pair == "BTC/USDT", "net_profit_usdt"].sum()),
        "eth_net_usdt": float(chosen.loc[chosen.pair == "ETH/USDT", "net_profit_usdt"].sum()),
        "regime_distribution": {str(k): int(v) for k, v in chosen.regime.value_counts().items()},
    }


def block_permutation(model, test, columns, target, fold, pair="ALL"):
    """Permute values as contiguous seven-day blocks; score by average precision."""
    selected = test if pair == "ALL" else test[test.pair == pair]
    if len(selected) < 20 or selected[target].nunique() < 2:
        return []
    base = average_precision_score(selected[target], model.predict_proba(selected[columns])[:, 1])
    block_ids = selected.decision_time.dt.floor("7D")
    blocks = [idx.to_numpy() for _, idx in selected.groupby(block_ids).groups.items()]
    rng = np.random.default_rng(SEED + fold + (0 if pair == "ALL" else 100 if pair.startswith("BTC") else 200))
    rows = []
    for column in columns:
        drops = []
        for _ in range(3):
            order = rng.permutation(len(blocks))
            source = np.concatenate([blocks[i] for i in order])
            target_index = np.concatenate(blocks)
            changed = selected[columns].copy()
            changed.loc[target_index, column] = selected.loc[source, column].to_numpy()
            score = average_precision_score(selected[target], model.predict_proba(changed)[:, 1])
            drops.append(base - score)
        rows.append({"fold": fold, "evaluation_year": int(test.year.iloc[0]), "pair": pair,
                     "feature": column, "ap_drop": float(np.mean(drops))})
    return rows


def main():
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    assert branch == "ai-lab-development"
    expected = json.loads((ROOT / "ai_lab/evaluation/protocol.json").read_text())["strategy_sha256"]
    assert sha(ROOT / "ai_lab/strategies/LabBaseline.py") == expected
    data_path = SOURCE / "data/A_portfolio.parquet"
    d = pd.read_parquet(data_path).sort_values(["decision_time", "pair"]).reset_index(drop=True)
    assert len(d) == 1271 and d.row_id.is_unique and set(d.year) == set(range(2019, 2025))
    assert not d[ALL + TARGETS].isna().any().any()
    assert (d.feature_candle_open + pd.Timedelta(hours=1) <= d.decision_time).all()
    folds = [f for f in json.loads((SOURCE / "folds.json").read_text()) if f["dataset"] == "A_portfolio"]
    assert [f["evaluation_year"] for f in folds] == [2020, 2021, 2022, 2023, 2024]
    protocol = {
        "source": "Phase 3B Dataset A only; Dataset B is intentionally not combined.",
        "source_sha256": sha(data_path), "targets": TARGETS, "feature_sets": SETS,
        "reduced_removals": REDUCED_REMOVALS, "models": MODELS, "thresholds": THRESHOLDS,
        "model_parameters": {m: make_pipeline(m, ALL).named_steps["model"].get_params() for m in MODELS},
        "fold_source": "ai_lab/ml_dataset_v2/folds.json exact row IDs",
        "selection": "No winner or threshold selection. Fixed configurations; report all yearly and aggregate evidence.",
        "importance": "Primary target, A_all only; contiguous 7-day block permutation, three repeats.",
        "cautions": ["2019-2024 are development evidence", "labels and samples overlap in time",
                     "no IID confidence intervals", "2023 and 2024 were previously observed"],
        "seed": SEED,
    }
    write_json(HERE / "protocol.json", protocol)

    fold_audit, fold_metrics, predictions = [], [], []
    coefficients, permutations = [], []
    for fold_number, manifest in enumerate(folds, 1):
        train_ids, test_ids = set(manifest["train_ids"]), set(manifest["test_ids"])
        train = d[d.row_id.isin(train_ids)].copy()
        test = d[d.row_id.isin(test_ids)].copy()
        assert len(train) == manifest["train_rows"] and len(test) == manifest["test_rows"]
        assert not train_ids & test_ids
        assert train.label_end.max() < pd.Timestamp(manifest["boundary"]) - pd.Timedelta(hours=48)
        assert test.label_end.max() < pd.Timestamp(manifest["test_end_exclusive"])
        fold_audit.append({"fold": fold_number, **{k: manifest[k] for k in
                           ["evaluation_year", "train_rows", "test_rows", "purged_train",
                            "right_boundary_test_exclusions", "embargo_hours"]},
                           "last_train_label_end": train.label_end.max(),
                           "first_test_decision": test.decision_time.min(),
                           "train_prevalence": float(train.profitable_after_fees.mean()),
                           "test_prevalence": float(test.profitable_after_fees.mean())})
        for target in TARGETS:
            for set_name, columns in SETS.items():
                for model_name in MODELS:
                    model = make_pipeline(model_name, columns)
                    model.fit(train[columns], train[target])
                    probability = model.predict_proba(test[columns])[:, 1]
                    key = {"fold": fold_number, "evaluation_year": manifest["evaluation_year"],
                           "target": target, "feature_set": set_name, "model": model_name}
                    fold_metrics.append({**key, **metrics(test[target], probability)})
                    predictions.extend({**key, "row_id": row_id, "probability": float(p)}
                                       for row_id, p in zip(test.row_id, probability))
                    if target == TARGETS[0] and model_name == "logistic":
                        names = model.named_steps["preprocess"].get_feature_names_out()
                        coefficients.extend({**key, "feature": feature, "coefficient": float(value)}
                                            for feature, value in zip(names, model.named_steps["model"].coef_[0]))
                    if target == TARGETS[0] and set_name == "A_all" and model_name != "dummy":
                        for pair in ["ALL", "BTC/USDT", "ETH/USDT"]:
                            permutations.extend({**key, **row} for row in
                                block_permutation(model, test, columns, target, fold_number, pair))
        print(f"completed fold {fold_number}: evaluation {manifest['evaluation_year']}", flush=True)

    write_json(HERE / "audits/fold-audit.json", fold_audit)
    write_json(HERE / "results/fold-metrics.json", fold_metrics)
    pred = pd.DataFrame(predictions)
    pred.to_parquet(HERE / "results/predictions.parquet", index=False)
    pd.DataFrame(coefficients).to_csv(HERE / "results/logistic-coefficients.csv", index=False)
    pd.DataFrame(permutations).to_csv(HERE / "results/block-permutation-importance.csv", index=False)

    # Economic results retain calendar years; aggregates concatenate out-of-fold years only.
    economics_rows = []
    for key, group in pred.groupby(["target", "feature_set", "model"]):
        target, set_name, model_name = key
        merged = group.merge(d, on="row_id", validate="one_to_one").sort_values(["decision_time", "pair"])
        for threshold in THRESHOLDS:
            yearly = []
            for year, year_frame in merged.groupby("evaluation_year"):
                result = economics(year_frame, year_frame.probability >= threshold)
                row = {"target": target, "feature_set": set_name, "model": model_name,
                       "threshold": threshold, "period": "year", "evaluation_year": int(year), **result}
                economics_rows.append(row)
                yearly.append(result)
            aggregate = economics(merged, merged.probability >= threshold)
            profits = [r["net_profit_usdt"] for r in yearly]
            economics_rows.append({"target": target, "feature_set": set_name, "model": model_name,
                "threshold": threshold, "period": "aggregate", "evaluation_year": None, **aggregate,
                "median_yearly_net_usdt": float(np.median(profits)), "worst_year_net_usdt": float(min(profits)),
                "profitable_years": int(sum(value > 0 for value in profits)),
                "yearly_net_std_usdt": float(np.std(profits, ddof=1))})
    econ = pd.DataFrame(economics_rows)
    econ.to_json(HERE / "results/economics.json", orient="records", indent=2)
    econ.to_csv(HERE / "results/economics.csv", index=False)

    # Yearly feature/prediction drift and importance stability are descriptive.
    drift = []
    reference = d[d.year == 2019]
    for year in range(2019, 2025):
        current = d[d.year == year]
        for feature in NUMERIC:
            drift.append({"year": year, "feature": feature, "n": len(current),
                "mean": float(current[feature].mean()), "std": float(current[feature].std()),
                "ks_vs_2019": float(ks_2samp(reference[feature], current[feature]).statistic)})
    pd.DataFrame(drift).to_csv(HERE / "results/feature-drift.csv", index=False)
    prediction_drift = []
    for key, group in pred.groupby(["target", "feature_set", "model", "evaluation_year"]):
        target, set_name, model_name, year = key
        labels = d.set_index("row_id").loc[group.row_id, target].to_numpy()
        prediction_drift.append({"target": target, "feature_set": set_name, "model": model_name,
            "year": int(year), **metrics(labels, group.probability)})
    write_json(HERE / "results/prediction-calibration-by-year.json", prediction_drift)

    perm = pd.DataFrame(permutations)
    stability = []
    for (model_name, pair), group in perm.groupby(["model", "pair"]):
        piv = group.pivot_table(index="feature", columns="evaluation_year", values="ap_drop")
        correlations = []
        for left in piv.columns:
            for right in piv.columns:
                if left < right:
                    correlations.append(spearmanr(piv[left], piv[right]).statistic)
        stability.append({"model": model_name, "pair": pair,
            "median_year_rank_correlation": float(np.nanmedian(correlations)),
            "min_year_rank_correlation": float(np.nanmin(correlations)),
            "mean_positive_importance_fraction": float((piv > 0).mean(axis=1).mean())})
    pd.DataFrame(stability).to_csv(HERE / "results/importance-stability.csv", index=False)
    assert sha(ROOT / "ai_lab/strategies/LabBaseline.py") == expected
    write_json(HERE / "audits/integrity.json", {"branch": branch, "strategy_sha256": expected,
        "source_sha256": sha(data_path), "source_rows": len(d), "dataset_b_loaded": False,
        "years": [2019, 2020, 2021, 2022, 2023, 2024], "no_2025_or_2026_data": True,
        "models_fitted": len(fold_metrics), "prediction_rows": len(pred),
        "shadow_holdout_accessed": False})
    print(f"complete: {len(fold_metrics)} fold/model results; {len(pred)} predictions", flush=True)


if __name__ == "__main__":
    main()
