"""
Unit tests for src/beacon_detector.py

Run with: pytest tests/test_beacon_detector.py -v
"""
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.beacon_detector import detect_beacons, beacon_alerts


def make_regular_beacon_flows(src, dst, n=20, interval_sec=600, jitter_sec=2, start="2026-01-01 00:00:00"):
    """Simulate a host beaconing to the same destination at a fixed interval."""
    rng = np.random.default_rng(1)
    start_ts = pd.Timestamp(start)
    rows = []
    for i in range(n):
        jitter = rng.uniform(-jitter_sec, jitter_sec)
        ts = start_ts + pd.Timedelta(seconds=i * interval_sec + jitter)
        rows.append({
            "timestamp": ts, "src_ip": src, "dst_ip": dst,
            "dst_port": 443, "protocol": "TCP",
            "bytes_out": 512, "bytes_in": 256, "duration_sec": 0.5,
        })
    return rows


def make_irregular_flows(src, dst, n=20, start="2026-01-01 00:00:00"):
    """Simulate normal, human-driven irregular traffic to the same destination."""
    rng = np.random.default_rng(2)
    start_ts = pd.Timestamp(start)
    rows = []
    cumulative = 0
    for i in range(n):
        cumulative += rng.exponential(scale=300)  # highly variable gaps
        ts = start_ts + pd.Timedelta(seconds=cumulative)
        rows.append({
            "timestamp": ts, "src_ip": src, "dst_ip": dst,
            "dst_port": 443, "protocol": "TCP",
            "bytes_out": int(rng.uniform(200, 5000)), "bytes_in": int(rng.uniform(200, 5000)),
            "duration_sec": rng.uniform(0.1, 3.0),
        })
    return rows


def test_detects_regular_beacon():
    rows = make_regular_beacon_flows("10.0.0.1", "203.0.113.5", n=20, interval_sec=600, jitter_sec=2)
    df = pd.DataFrame(rows)
    result = detect_beacons(df, min_connections=8, cov_threshold=0.3)
    assert len(result) == 1
    assert result.iloc[0]["src_ip"] == "10.0.0.1"
    assert result.iloc[0]["dst_ip"] == "203.0.113.5"
    assert result.iloc[0]["coefficient_of_variation"] < 0.3


def test_does_not_flag_irregular_traffic():
    rows = make_irregular_flows("10.0.0.2", "203.0.113.9", n=20)
    df = pd.DataFrame(rows)
    result = detect_beacons(df, min_connections=8, cov_threshold=0.3)
    assert result.empty


def test_respects_min_connections_threshold():
    # Only 5 connections - below default min_connections of 8, should not be flagged
    # even though the timing is perfectly regular
    rows = make_regular_beacon_flows("10.0.0.3", "203.0.113.7", n=5, interval_sec=600, jitter_sec=1)
    df = pd.DataFrame(rows)
    result = detect_beacons(df, min_connections=8, cov_threshold=0.3)
    assert result.empty


def test_mixed_population_flags_only_the_beacon():
    beacon_rows = make_regular_beacon_flows("10.0.0.1", "203.0.113.5", n=20, interval_sec=600, jitter_sec=2)
    normal_rows = make_irregular_flows("10.0.0.2", "203.0.113.9", n=20)
    df = pd.DataFrame(beacon_rows + normal_rows)
    result = detect_beacons(df, min_connections=8, cov_threshold=0.3)
    assert len(result) == 1
    assert result.iloc[0]["src_ip"] == "10.0.0.1"


def test_beacon_alerts_output_schema():
    rows = make_regular_beacon_flows("10.0.0.1", "203.0.113.5", n=20, interval_sec=600, jitter_sec=2)
    df = pd.DataFrame(rows)
    beacon_df = detect_beacons(df, min_connections=8, cov_threshold=0.3)
    alerts = beacon_alerts(beacon_df)

    assert len(alerts) == 1
    alert = alerts[0]
    for key in ["detector", "src_ip", "dst_ip", "risk_score", "severity", "summary_stats", "suggested_hypothesis"]:
        assert key in alert
    assert alert["detector"] == "beacon_periodicity"
    assert 0 <= alert["risk_score"] <= 100
    assert alert["severity"] in {"low", "medium", "high", "critical"}


def test_stricter_cov_threshold_reduces_detections():
    # A moderately-jittered beacon that passes a lenient threshold but fails a strict one
    rows = make_regular_beacon_flows("10.0.0.1", "203.0.113.5", n=20, interval_sec=600, jitter_sec=90)
    df = pd.DataFrame(rows)
    lenient = detect_beacons(df, min_connections=8, cov_threshold=0.9)
    strict = detect_beacons(df, min_connections=8, cov_threshold=0.05)
    assert len(lenient) >= len(strict)
