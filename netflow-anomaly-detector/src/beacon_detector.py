"""
Dedicated beaconing detector.

Why this exists separately from the windowed IsolationForest model:
Beaconing (regular C2 check-ins) is a *periodicity* signal that shows up
across the full observation period for a specific (src_ip, dst_ip) pair.
If the beacon interval is longer than the aggregation window used for the
general anomaly model, the signal gets diluted by each host's unrelated
background traffic within the same window and can be missed entirely.

This module instead looks at inter-arrival times for every (src_ip, dst_ip)
pair across the ENTIRE dataset, and flags pairs with:
  - a minimum number of connections (so we have enough data to judge
    periodicity)
  - low coefficient of variation (CoV = std/mean) of inter-arrival time,
    i.e. very regular timing - the hallmark of automated beaconing vs.
    human-driven or bursty traffic
"""

import pandas as pd
import numpy as np


def detect_beacons(df: pd.DataFrame, min_connections: int = 8, cov_threshold: float = 0.3):
    """
    Args:
        df: raw flow dataframe with columns [timestamp, src_ip, dst_ip, ...]
        min_connections: minimum number of connections between a pair to evaluate
        cov_threshold: max coefficient of variation (std/mean) of interval to
                       consider "regular enough" to flag as likely beaconing.
                       Lower = stricter / fewer false positives.

    Returns:
        DataFrame of flagged (src_ip, dst_ip) pairs with periodicity stats,
        sorted by regularity (most regular first).
    """
    df = df.sort_values("timestamp")
    results = []

    for (src, dst), g in df.groupby(["src_ip", "dst_ip"]):
        if len(g) < min_connections:
            continue

        intervals = g["timestamp"].diff().dt.total_seconds().dropna()
        if len(intervals) < min_connections - 1:
            continue

        mean_interval = intervals.mean()
        std_interval = intervals.std()
        if mean_interval <= 0:
            continue

        cov = std_interval / mean_interval

        if cov <= cov_threshold:
            results.append({
                "src_ip": src,
                "dst_ip": dst,
                "connection_count": len(g),
                "mean_interval_sec": round(mean_interval, 2),
                "std_interval_sec": round(std_interval, 2),
                "coefficient_of_variation": round(cov, 3),
                "first_seen": g["timestamp"].min(),
                "last_seen": g["timestamp"].max(),
                "avg_bytes_out": round(g["bytes_out"].mean(), 1),
            })

    result_df = pd.DataFrame(results)
    if not result_df.empty:
        result_df = result_df.sort_values("coefficient_of_variation")
    return result_df


def beacon_alerts(beacon_df: pd.DataFrame):
    """Convert flagged beacon pairs into the same alert schema used elsewhere."""
    alerts = []
    for _, row in beacon_df.iterrows():
        # Very low CoV -> very high confidence -> map to a risk score for consistency
        risk_score = round(max(0, 100 * (1 - row["coefficient_of_variation"] / 0.3)), 1)
        severity = "critical" if risk_score >= 90 else "high" if risk_score >= 75 else "medium"
        alerts.append({
            "detector": "beacon_periodicity",
            "src_ip": row["src_ip"],
            "dst_ip": row["dst_ip"],
            "risk_score": risk_score,
            "severity": severity,
            "summary_stats": {
                "connection_count": int(row["connection_count"]),
                "mean_interval_sec": row["mean_interval_sec"],
                "std_interval_sec": row["std_interval_sec"],
                "coefficient_of_variation": row["coefficient_of_variation"],
                "avg_bytes_out": row["avg_bytes_out"],
                "first_seen": str(row["first_seen"]),
                "last_seen": str(row["last_seen"]),
            },
            "suggested_hypothesis": (
                f"Highly regular connection timing (CoV={row['coefficient_of_variation']}) "
                f"between {row['src_ip']} and {row['dst_ip']} over {row['connection_count']} "
                f"connections is consistent with automated C2 beaconing rather than human-driven traffic."
            ),
        })
    return alerts
