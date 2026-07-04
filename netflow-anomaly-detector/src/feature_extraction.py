"""
Feature extraction for network anomaly detection.

Raw flow records (one row per connection) are aggregated into per-source-IP,
per-time-window behavioral feature vectors. Anomaly detection works far better
on these aggregated behavioral features than on raw flows, because things like
"beaconing" or "port scanning" are only visible as a *pattern over time*, not
in any single flow.

Features computed per (src_ip, window):
  - flow_count            : number of flows in the window
  - unique_dst_ips        : distinct destinations contacted
  - unique_dst_ports      : distinct destination ports touched
  - total_bytes_out       : sum of outbound bytes
  - total_bytes_in        : sum of inbound bytes
  - bytes_out_in_ratio    : outbound/inbound ratio (exfiltration signal)
  - avg_duration          : average flow duration
  - mean_interval_sec     : mean time between consecutive flows (beaconing signal)
  - std_interval_sec      : std deviation of inter-flow interval
                            (LOW std + regular mean interval = classic beaconing)
  - external_ratio        : fraction of flows going to non-RFC1918 addresses
"""

import pandas as pd
import numpy as np
import ipaddress


def _is_external(ip: str) -> bool:
    try:
        return not ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def load_flows(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def build_features(df: pd.DataFrame, window_minutes: int = 5) -> pd.DataFrame:
    """Aggregate raw flows into per-source-IP, per-window feature vectors."""
    df = df.copy()
    df["is_external"] = df["dst_ip"].apply(_is_external)
    df["window"] = df["timestamp"].dt.floor(f"{window_minutes}min")

    records = []
    grouped = df.groupby(["src_ip", "window"])

    for (src_ip, window), g in grouped:
        g = g.sort_values("timestamp")
        intervals = g["timestamp"].diff().dt.total_seconds().dropna()

        record = {
            "src_ip": src_ip,
            "window": window,
            "flow_count": len(g),
            "unique_dst_ips": g["dst_ip"].nunique(),
            "unique_dst_ports": g["dst_port"].nunique(),
            "total_bytes_out": g["bytes_out"].sum(),
            "total_bytes_in": g["bytes_in"].sum(),
            "bytes_out_in_ratio": (g["bytes_out"].sum() + 1) / (g["bytes_in"].sum() + 1),
            "avg_duration": g["duration_sec"].mean(),
            "mean_interval_sec": intervals.mean() if len(intervals) > 0 else 0.0,
            "std_interval_sec": intervals.std() if len(intervals) > 1 else 0.0,
            "external_ratio": g["is_external"].mean(),
        }
        records.append(record)

    features = pd.DataFrame(records)
    features["std_interval_sec"] = features["std_interval_sec"].fillna(0.0)
    features["mean_interval_sec"] = features["mean_interval_sec"].fillna(0.0)
    return features


FEATURE_COLUMNS = [
    "flow_count",
    "unique_dst_ips",
    "unique_dst_ports",
    "total_bytes_out",
    "total_bytes_in",
    "bytes_out_in_ratio",
    "avg_duration",
    "mean_interval_sec",
    "std_interval_sec",
    "external_ratio",
]
