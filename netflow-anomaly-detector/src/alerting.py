"""
Alert formatting and output.

Converts scored, flagged windows into structured alert objects suitable for
forwarding to a SIEM/SOAR (as JSON) or for direct human review. Each alert
includes the contributing features so an analyst isn't just handed a bare
number.
"""

import json
from datetime import datetime
from src.model import AnomalyModel


def _severity_from_score(score: float) -> str:
    if score >= 90:
        return "critical"
    elif score >= 80:
        return "high"
    elif score >= 70:
        return "medium"
    else:
        return "low"


def build_alerts(scored_df, threshold: float, top_n_features: int = 5):
    """Build a list of alert dicts for all rows above the risk threshold."""
    alerts = []
    flagged = scored_df[scored_df["risk_score"] >= threshold].sort_values(
        "risk_score", ascending=False
    )

    for _, row in flagged.iterrows():
        contributing = AnomalyModel.top_contributing_features(row["_zscores"], top_n_features)
        alert = {
            "generated_at": datetime.now().isoformat(),
            "src_ip": row["src_ip"],
            "window_start": str(row["window"]),
            "risk_score": row["risk_score"],
            "severity": _severity_from_score(row["risk_score"]),
            "summary_stats": {
                "flow_count": int(row["flow_count"]),
                "unique_dst_ips": int(row["unique_dst_ips"]),
                "unique_dst_ports": int(row["unique_dst_ports"]),
                "total_bytes_out": int(row["total_bytes_out"]),
                "total_bytes_in": int(row["total_bytes_in"]),
                "mean_interval_sec": round(float(row["mean_interval_sec"]), 2),
                "std_interval_sec": round(float(row["std_interval_sec"]), 2),
                "external_ratio": round(float(row["external_ratio"]), 2),
            },
            "top_contributing_features": contributing,
            "suggested_hypothesis": _hypothesize(row, contributing),
        }
        alerts.append(alert)

    return alerts


def _hypothesize(row, contributing) -> str:
    """Very lightweight heuristic to give analysts a starting hypothesis.
    This is NOT a substitute for investigation - just a triage hint."""
    feature_names = {c["feature"] for c in contributing}

    if row["std_interval_sec"] < 5 and row["mean_interval_sec"] > 0 and "mean_interval_sec" in feature_names:
        return "Regular, low-jitter timing between flows to the same destination suggests possible beaconing / C2 activity."
    if row["bytes_out_in_ratio"] > 10 and "total_bytes_out" in feature_names:
        return "Large outbound-to-inbound byte ratio suggests possible data exfiltration."
    if row["unique_dst_ips"] > 20 and "unique_dst_ips" in feature_names:
        return "High number of distinct destinations in a short window suggests possible scanning/reconnaissance."
    return "Statistically unusual behavior relative to baseline; manual review recommended."


def write_alerts(alerts, output_path: str):
    with open(output_path, "w") as f:
        json.dump(alerts, f, indent=2, default=str)
    return output_path
