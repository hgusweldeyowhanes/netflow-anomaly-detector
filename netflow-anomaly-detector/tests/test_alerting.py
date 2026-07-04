"""
Unit tests for src/alerting.py

Run with: pytest tests/test_alerting.py -v
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.alerting import build_alerts, _severity_from_score, _hypothesize


def make_scored_row(risk_score, **overrides):
    base = {
        "src_ip": "10.0.0.1",
        "window": pd.Timestamp("2026-01-01 00:00:00"),
        "risk_score": risk_score,
        "flow_count": 5,
        "unique_dst_ips": 3,
        "unique_dst_ports": 3,
        "total_bytes_out": 1000,
        "total_bytes_in": 800,
        "mean_interval_sec": 60.0,
        "std_interval_sec": 5.0,
        "external_ratio": 0.5,
        "bytes_out_in_ratio": 1.25,
        "_zscores": {"flow_count": 1.0, "unique_dst_ips": 0.5},
    }
    base.update(overrides)
    return base


def test_severity_thresholds():
    assert _severity_from_score(95) == "critical"
    assert _severity_from_score(85) == "high"
    assert _severity_from_score(72) == "medium"
    assert _severity_from_score(50) == "low"


def test_build_alerts_filters_by_threshold():
    df = pd.DataFrame([
        make_scored_row(95),
        make_scored_row(50),   # below threshold, should be excluded
        make_scored_row(80),
    ])
    alerts = build_alerts(df, threshold=70)
    assert len(alerts) == 2
    assert all(a["risk_score"] >= 70 for a in alerts)


def test_build_alerts_sorted_descending():
    df = pd.DataFrame([make_scored_row(75), make_scored_row(99), make_scored_row(80)])
    alerts = build_alerts(df, threshold=70)
    scores = [a["risk_score"] for a in alerts]
    assert scores == sorted(scores, reverse=True)


def test_build_alerts_output_schema():
    df = pd.DataFrame([make_scored_row(90)])
    alerts = build_alerts(df, threshold=70, top_n_features=2)
    alert = alerts[0]
    for key in ["generated_at", "src_ip", "window_start", "risk_score", "severity",
                "summary_stats", "top_contributing_features", "suggested_hypothesis"]:
        assert key in alert
    assert len(alert["top_contributing_features"]) <= 2


def test_hypothesize_exfiltration_pattern():
    row = pd.Series(make_scored_row(90, bytes_out_in_ratio=50, total_bytes_out=5_000_000))
    contributing = [{"feature": "total_bytes_out", "zscore": 10, "direction": "high"}]
    hyp = _hypothesize(row, contributing)
    assert "exfiltration" in hyp.lower()


def test_hypothesize_scan_pattern():
    row = pd.Series(make_scored_row(90, unique_dst_ips=50, bytes_out_in_ratio=1.0))
    contributing = [{"feature": "unique_dst_ips", "zscore": 10, "direction": "high"}]
    hyp = _hypothesize(row, contributing)
    assert "scan" in hyp.lower() or "reconnaissance" in hyp.lower()


def test_hypothesize_falls_back_to_generic():
    row = pd.Series(make_scored_row(90, unique_dst_ips=2, bytes_out_in_ratio=1.0,
                                     std_interval_sec=50, mean_interval_sec=60))
    contributing = [{"feature": "flow_count", "zscore": 2, "direction": "high"}]
    hyp = _hypothesize(row, contributing)
    assert "manual review" in hyp.lower()
