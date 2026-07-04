"""
Integration test: runs the FULL pipeline (generate -> features -> model ->
beacon detector -> alerts) end-to-end and validates against the ground-truth
anomalous hosts that the data generator itself injected.

This is the most important test in the suite: unit tests confirm each part
works in isolation, but this confirms the pieces actually work TOGETHER to
catch real attack patterns - which is the entire point of the tool.

Run with: pytest tests/test_integration.py -v -s
(-s shows the print output so you can see what got detected)
"""
import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_generator import generate_dataset
from src.feature_extraction import load_flows, build_features, FEATURE_COLUMNS
from src.model import AnomalyModel
from src.alerting import build_alerts
from src.beacon_detector import detect_beacons, beacon_alerts


def test_full_pipeline_catches_all_injected_anomalies():
    tmp_dir = tempfile.mkdtemp()
    try:
        csv_path = os.path.join(tmp_dir, "flows.csv")
        df, ground_truth = generate_dataset(output_path=csv_path, hours=6)

        flows = load_flows(csv_path)
        features = build_features(flows, window_minutes=5)

        model = AnomalyModel(FEATURE_COLUMNS, model_type="isolation_forest", contamination=0.02)
        scored = model.fit_predict(features)
        window_alerts = build_alerts(scored, threshold=70)

        beacon_df = detect_beacons(flows, min_connections=8, cov_threshold=0.3)
        beacons = beacon_alerts(beacon_df) if not beacon_df.empty else []

        all_alerts = window_alerts + beacons
        flagged_hosts = {a["src_ip"] for a in all_alerts}

        print(f"\nGround truth: {ground_truth}")
        print(f"Flagged hosts: {flagged_hosts}")

        # The exfiltration host should be caught by the windowed model
        assert ground_truth["exfiltration"] in flagged_hosts, (
            "Exfiltration host was not flagged - check bytes_out_in_ratio feature / contamination setting"
        )

        # The port scan host should be caught by the windowed model
        assert ground_truth["port_scan"] in flagged_hosts, (
            "Port scan host was not flagged - check unique_dst_ips/ports features"
        )

        # The beaconing host should be caught by the dedicated beacon detector
        assert ground_truth["beaconing"] in flagged_hosts, (
            "Beaconing host was not flagged - check beacon_detector cov_threshold/min_connections"
        )

    finally:
        shutil.rmtree(tmp_dir)


def test_pipeline_produces_reasonable_alert_volume():
    """Sanity check: with default settings on ~6 hours of demo traffic across
    40 hosts, we shouldn't be flagging an unreasonable fraction of all windows
    (that would indicate the model/threshold is miscalibrated for this data)."""
    tmp_dir = tempfile.mkdtemp()
    try:
        csv_path = os.path.join(tmp_dir, "flows.csv")
        generate_dataset(output_path=csv_path, hours=6)

        flows = load_flows(csv_path)
        features = build_features(flows, window_minutes=5)

        model = AnomalyModel(FEATURE_COLUMNS, model_type="isolation_forest", contamination=0.02)
        scored = model.fit_predict(features)
        alerts = build_alerts(scored, threshold=70)

        alert_fraction = len(alerts) / len(features)
        # With contamination=0.02 we expect roughly 2% flagged, generously bounded here
        assert alert_fraction < 0.10, f"Too many windows flagged ({alert_fraction:.1%}) - alert fatigue risk"

    finally:
        shutil.rmtree(tmp_dir)
