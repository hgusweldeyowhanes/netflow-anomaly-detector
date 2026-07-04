"""
AI-Powered Anomaly Detection for Network Traffic
--------------------------------------------------
End-to-end CLI pipeline:
  1. Load (or generate) flow data
  2. Extract behavioral features per source IP per time window
  3. Score windows with an unsupervised anomaly model (Isolation Forest)
  4. Emit structured alerts for anything above the risk threshold

Usage:
    python main.py                      # generates demo data if none exists, runs full pipeline
    python main.py --input data/flows.csv --config config.yaml
    python main.py --generate-demo      # force-regenerate synthetic demo data
"""

import argparse
import os
import sys
import yaml
import pandas as pd

from src.feature_extraction import load_flows, build_features, FEATURE_COLUMNS
from src.model import AnomalyModel
from src.alerting import build_alerts, write_alerts
from src.data_generator import generate_dataset
from src.beacon_detector import detect_beacons, beacon_alerts


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Network traffic anomaly detection pipeline")
    parser.add_argument("--config", default="config.yaml", help="Path to config YAML")
    parser.add_argument("--input", default=None, help="Override input flow CSV path")
    parser.add_argument("--generate-demo", action="store_true", help="Force regeneration of synthetic demo data")
    args = parser.parse_args()

    cfg = load_config(args.config)
    input_path = args.input or cfg["data"]["input_path"]

    os.makedirs(os.path.dirname(input_path), exist_ok=True)
    os.makedirs(os.path.dirname(cfg["alerting"]["output_path"]), exist_ok=True)

    if args.generate_demo or not os.path.exists(input_path):
        print(f"[*] No input data found at {input_path} (or --generate-demo set). Generating synthetic demo dataset...")
        generate_dataset(output_path=input_path)

    print(f"\n[*] Loading flows from {input_path} ...")
    flows = load_flows(input_path)
    print(f"    {len(flows)} raw flow records loaded.")

    print(f"\n[*] Extracting behavioral features (window={cfg['data']['window_minutes']} min) ...")
    features = build_features(flows, window_minutes=cfg["data"]["window_minutes"])
    print(f"    {len(features)} (src_ip, window) feature vectors built.")

    print(f"\n[*] Training anomaly model ({cfg['model']['type']}) ...")
    model = AnomalyModel(
        feature_columns=FEATURE_COLUMNS,
        model_type=cfg["model"]["type"],
        contamination=cfg["model"]["contamination"],
        n_estimators=cfg["model"].get("n_estimators", 200),
        random_state=cfg["model"].get("random_state", 42),
    )
    scored = model.fit_predict(features)

    threshold = cfg["scoring"]["alert_risk_threshold"]
    n_flagged = (scored["risk_score"] >= threshold).sum()
    print(f"\n[*] Scoring complete. {n_flagged} of {len(scored)} windows flagged at risk_score >= {threshold}.")

    alerts = build_alerts(scored, threshold=threshold, top_n_features=cfg["alerting"]["top_n_features"])

    print(f"\n[*] Running dedicated beacon/periodicity detector (catches C2 patterns the windowed model can miss) ...")
    beacon_cfg = cfg.get("beacon_detector", {})
    beacon_df = detect_beacons(
        flows,
        min_connections=beacon_cfg.get("min_connections", 8),
        cov_threshold=beacon_cfg.get("cov_threshold", 0.3),
    )
    beacon_alert_list = beacon_alerts(beacon_df) if not beacon_df.empty else []
    print(f"    {len(beacon_alert_list)} beaconing pattern(s) flagged.")

    all_alerts = alerts + beacon_alert_list
    out_path = write_alerts(all_alerts, cfg["alerting"]["output_path"])
    print(f"[*] {len(all_alerts)} total alerts written to {out_path}\n")

    if all_alerts:
        print("=" * 70)
        print("TOP ALERTS")
        print("=" * 70)
        sorted_alerts = sorted(all_alerts, key=lambda a: a["risk_score"], reverse=True)
        for a in sorted_alerts[:15]:
            if a.get("detector") == "beacon_periodicity":
                print(f"\n[{a['severity'].upper()}] risk={a['risk_score']}  BEACONING  {a['src_ip']} -> {a['dst_ip']}")
            else:
                print(f"\n[{a['severity'].upper()}] risk={a['risk_score']}  src_ip={a['src_ip']}  window={a['window_start']}")
            print(f"  Hypothesis: {a['suggested_hypothesis']}")
            if "top_contributing_features" in a:
                print(f"  Top features: {', '.join(f['feature'] + '(' + str(f['zscore']) + ')' for f in a['top_contributing_features'])}")
    else:
        print("No alerts above threshold. Try lowering scoring.alert_risk_threshold in config.yaml.")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
