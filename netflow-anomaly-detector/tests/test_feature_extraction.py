"""
Unit tests for src/feature_extraction.py

Run with: pytest tests/test_feature_extraction.py -v
"""
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.feature_extraction import build_features, _is_external, FEATURE_COLUMNS


def make_flow(ts, src, dst, port=443, bytes_out=1000, bytes_in=500, duration=1.0):
    return {
        "timestamp": pd.Timestamp(ts),
        "src_ip": src,
        "dst_ip": dst,
        "dst_port": port,
        "protocol": "TCP",
        "bytes_out": bytes_out,
        "bytes_in": bytes_in,
        "duration_sec": duration,
    }


def test_is_external_private_ip():
    assert _is_external("10.0.0.5") is False
    assert _is_external("192.168.1.1") is False
    assert _is_external("172.16.0.1") is False


def test_is_external_public_ip():
    assert _is_external("8.8.8.8") is True
    assert _is_external("1.1.1.1") is True


def test_is_external_invalid_ip_does_not_crash():
    # Malformed data should not blow up the pipeline
    assert _is_external("not-an-ip") is False


def test_build_features_basic_aggregation():
    rows = [
        make_flow("2026-01-01 00:00:00", "10.0.0.1", "8.8.8.8"),
        make_flow("2026-01-01 00:01:00", "10.0.0.1", "8.8.4.4"),
        make_flow("2026-01-01 00:02:00", "10.0.0.1", "1.1.1.1"),
    ]
    df = pd.DataFrame(rows)
    features = build_features(df, window_minutes=5)

    assert len(features) == 1  # all 3 flows fall in the same 5-min window
    row = features.iloc[0]
    assert row["flow_count"] == 3
    assert row["unique_dst_ips"] == 3
    assert row["external_ratio"] == 1.0  # all destinations are public IPs


def test_build_features_separates_windows():
    rows = [
        make_flow("2026-01-01 00:00:00", "10.0.0.1", "8.8.8.8"),
        make_flow("2026-01-01 00:10:00", "10.0.0.1", "8.8.4.4"),  # 10 min later -> new window
    ]
    df = pd.DataFrame(rows)
    features = build_features(df, window_minutes=5)
    assert len(features) == 2


def test_build_features_separates_hosts():
    rows = [
        make_flow("2026-01-01 00:00:00", "10.0.0.1", "8.8.8.8"),
        make_flow("2026-01-01 00:00:30", "10.0.0.2", "8.8.8.8"),
    ]
    df = pd.DataFrame(rows)
    features = build_features(df, window_minutes=5)
    assert len(features) == 2
    assert set(features["src_ip"]) == {"10.0.0.1", "10.0.0.2"}


def test_build_features_bytes_ratio_reflects_exfiltration():
    # Large outbound, tiny inbound -> should produce a high bytes_out_in_ratio
    rows = [
        make_flow("2026-01-01 00:00:00", "10.0.0.1", "8.8.8.8", bytes_out=5_000_000, bytes_in=100),
    ]
    df = pd.DataFrame(rows)
    features = build_features(df, window_minutes=5)
    assert features.iloc[0]["bytes_out_in_ratio"] > 1000


def test_all_feature_columns_present():
    rows = [make_flow("2026-01-01 00:00:00", "10.0.0.1", "8.8.8.8")]
    df = pd.DataFrame(rows)
    features = build_features(df, window_minutes=5)
    for col in FEATURE_COLUMNS:
        assert col in features.columns


def test_no_nan_in_interval_features_for_single_flow():
    # A window with only one flow has no interval to compute - should be 0, not NaN
    rows = [make_flow("2026-01-01 00:00:00", "10.0.0.1", "8.8.8.8")]
    df = pd.DataFrame(rows)
    features = build_features(df, window_minutes=5)
    assert features.iloc[0]["mean_interval_sec"] == 0.0
    assert features.iloc[0]["std_interval_sec"] == 0.0
    assert not features["mean_interval_sec"].isna().any()
    assert not features["std_interval_sec"].isna().any()
