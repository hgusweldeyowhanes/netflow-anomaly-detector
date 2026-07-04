"""
Unit tests for src/model.py

Run with: pytest tests/test_model.py -v
"""
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.model import AnomalyModel
from src.feature_extraction import FEATURE_COLUMNS


def make_feature_df(n_normal=100, n_anomalies=3, seed=42):
    """Build a synthetic feature dataframe: mostly tight-clustered 'normal'
    rows plus a few far-outlier rows, so we can check the model separates them."""
    rng = np.random.default_rng(seed)

    normal = pd.DataFrame({
        col: rng.normal(loc=10, scale=1, size=n_normal) for col in FEATURE_COLUMNS
    })
    normal["src_ip"] = [f"10.0.0.{i}" for i in range(n_normal)]
    normal["window"] = pd.Timestamp("2026-01-01")

    anomalies = pd.DataFrame({
        col: rng.normal(loc=200, scale=5, size=n_anomalies) for col in FEATURE_COLUMNS
    })
    anomalies["src_ip"] = [f"10.0.1.{i}" for i in range(n_anomalies)]
    anomalies["window"] = pd.Timestamp("2026-01-01")

    return pd.concat([normal, anomalies], ignore_index=True), n_normal, n_anomalies


def test_fit_predict_adds_expected_columns():
    df, _, _ = make_feature_df()
    model = AnomalyModel(FEATURE_COLUMNS, model_type="isolation_forest", contamination=0.03)
    result = model.fit_predict(df)
    for col in ["raw_score", "risk_score", "is_anomaly", "_zscores"]:
        assert col in result.columns


def test_risk_score_bounded_0_to_100():
    df, _, _ = make_feature_df()
    model = AnomalyModel(FEATURE_COLUMNS, model_type="isolation_forest", contamination=0.03)
    result = model.fit_predict(df)
    assert result["risk_score"].min() >= 0
    assert result["risk_score"].max() <= 100


def test_injected_outliers_score_higher_than_normal():
    df, n_normal, n_anomalies = make_feature_df()
    model = AnomalyModel(FEATURE_COLUMNS, model_type="isolation_forest", contamination=0.03)
    result = model.fit_predict(df)

    normal_scores = result.iloc[:n_normal]["risk_score"]
    anomaly_scores = result.iloc[n_normal:]["risk_score"]

    # The injected far-outliers should score meaningfully higher on average
    assert anomaly_scores.mean() > normal_scores.mean()
    # And the single highest risk score in the dataset should belong to an outlier
    assert result.loc[result["risk_score"].idxmax(), "src_ip"].startswith("10.0.1.")


def test_top_contributing_features_returns_correct_count():
    zscores = {"a": 3.5, "b": -0.2, "c": 5.1, "d": 0.1, "e": -4.0, "f": 0.05}
    top = AnomalyModel.top_contributing_features(zscores, top_n=3)
    assert len(top) == 3
    # Ranked by absolute z-score magnitude, largest first: c(5.1) > e(4.0) > a(3.5)
    assert [t["feature"] for t in top] == ["c", "e", "a"]


def test_top_contributing_features_direction_labels():
    zscores = {"high_feat": 3.0, "low_feat": -3.0}
    top = AnomalyModel.top_contributing_features(zscores, top_n=2)
    directions = {t["feature"]: t["direction"] for t in top}
    assert directions["high_feat"] == "high"
    assert directions["low_feat"] == "low"


def test_lof_model_type_runs_without_error():
    df, _, _ = make_feature_df(n_normal=50, n_anomalies=3)
    model = AnomalyModel(FEATURE_COLUMNS, model_type="lof", contamination=0.05)
    result = model.fit_predict(df)
    assert "risk_score" in result.columns
    assert len(result) == len(df)
