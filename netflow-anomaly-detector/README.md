# Network Traffic Anomaly Detector

An unsupervised, behavior-based anomaly detection pipeline for network flow data.
It catches things signature-based tools miss — beaconing/C2 patterns, data
exfiltration, and reconnaissance/port scanning — by learning what "normal"
looks like for your network and flagging statistically unusual behavior.

This is a **working, tested implementation** (not a template). It ships with a
synthetic data generator so you can see it detect real attack patterns
immediately, and is structured so swapping in your own NetFlow/Zeek export is
a small, well-defined step.

## What it catches (validated in this build)

| Pattern | Detection method | Result on demo data |
|---|---|---|
| C2 beaconing | Dedicated periodicity detector (coefficient of variation of inter-arrival time per src/dst pair) | Caught: CoV=0.007 over 36 connections, risk=97.7 |
| Data exfiltration | Isolation Forest on windowed behavioral features (bytes out/in ratio, volume) | Caught: risk=100.0 |
| Port scanning | Isolation Forest on windowed behavioral features (unique dest IPs/ports, flow count) | Caught: risk=90.5 |

## Quick Start

```bash
pip install -r requirements.txt

# Run with auto-generated synthetic demo data (recommended first run)
python main.py --generate-demo

# Subsequent runs reuse the same generated data/flows.csv
python main.py
```

You'll see console output ranking the top alerts, and a full structured
alert list written to `output/alerts.json`.

## Project Structure

```
netflow-anomaly-detector/
├── main.py                    # CLI entrypoint / pipeline orchestration
├── config.yaml                # All tunable parameters
├── requirements.txt
├── src/
│   ├── data_generator.py      # Synthetic demo data w/ injected anomalies
│   ├── feature_extraction.py  # Raw flows -> per-src-IP behavioral features
│   ├── model.py                # IsolationForest wrapper + risk scoring + attribution
│   ├── beacon_detector.py     # Dedicated C2 periodicity detector
│   └── alerting.py            # Alert formatting / JSON output
├── data/                      # Input flow CSVs (generated or your own)
└── output/                    # alerts.json written here
```

## Using Your Own Data

Point `data.input_path` in `config.yaml` at a CSV with these columns:

| Column | Type | Description |
|---|---|---|
| `timestamp` | datetime (parseable) | Flow start time |
| `src_ip` | string | Source IP |
| `dst_ip` | string | Destination IP |
| `dst_port` | int | Destination port |
| `protocol` | string | TCP/UDP/etc |
| `bytes_out` | int | Bytes sent by source |
| `bytes_in` | int | Bytes received by source |
| `duration_sec` | float | Flow duration in seconds |

**Getting this from real sources:**
- **Zeek**: `conn.log` maps almost directly — `ts`→timestamp, `id.orig_h`→src_ip, `id.resp_h`→dst_ip, `id.resp_p`→dst_port, `orig_bytes`/`resp_bytes`→bytes_out/in, `duration`→duration_sec.
- **NetFlow/sFlow** (via nfdump/softflowd): export to CSV with `nfdump -o csv` and remap column names to match the schema above.
- **Cloud VPC Flow Logs** (AWS/Azure/GCP): export to CSV/S3, remap `srcaddr`/`dstaddr`/`dstport`/`bytes` fields similarly.

No model retraining code changes needed — just point `input_path` at the new file.

## Tuning for Your Environment

All of this lives in `config.yaml`, no code changes needed:

- **`model.contamination`** (default 0.02): expected fraction of anomalous
  windows. Start conservative (0.01–0.03); raise it if you're missing known-bad
  behavior in testing, lower it if you're drowning in alerts.
- **`scoring.alert_risk_threshold`** (default 70): raise to reduce alert
  volume, lower to catch more borderline cases during initial tuning.
- **`data.window_minutes`** (default 5): the aggregation window for the
  general model. Shorter windows catch fast bursts (scans, exfil) better;
  longer windows can dilute fast attacks but capture slower patterns.
- **`beacon_detector.cov_threshold`** (default 0.3): how "regular" timing has
  to be to flag as beaconing. Lower = stricter/fewer false positives, but
  will miss beacons with deliberate jitter designed to evade this exact kind
  of detection.
- **`beacon_detector.min_connections`** (default 8): minimum observed
  connections between a src/dst pair before judging periodicity. Too low
  gives unstable statistics; too high delays detection of new beacons.

## Important Design Note: Why There Are Two Detectors

Beaconing is a *periodicity* pattern that shows up across the **entire**
observation period for a specific (src, dst) pair — but the general model
aggregates behavior into fixed time windows (default 5 min) to catch
volume/scope anomalies like exfiltration and scanning. If a beacon's interval
is longer than the window size, the signal gets diluted by a host's unrelated
background traffic and can be missed by the windowed model alone.

This implementation was tested against exactly that failure mode (10-minute
beacon interval vs. 5-minute window) and the windowed model alone missed it.
The dedicated `beacon_detector.py` — analyzing inter-arrival time regularity
per (src,dst) pair across the full dataset — was added specifically to close
that gap. Both detectors feed into the same `alerts.json` output.

## Understanding Alert Output

Each alert in `output/alerts.json` includes:
- `risk_score` (0–100, higher = more anomalous)
- `severity` (low/medium/high/critical)
- `summary_stats` — the raw behavioral numbers behind the flag
- `top_contributing_features` (windowed alerts) — which features deviated
  most from baseline, in standard deviations, so an analyst isn't just
  handed a bare number
- `suggested_hypothesis` — a lightweight, rule-based first guess at what
  might be happening (NOT a substitute for investigation)

## Known Limitations (Be Upfront About These With Stakeholders)

1. **Cold start**: the model needs a baseline period of "mostly normal"
   traffic to learn from. If your network already has undetected malicious
   activity in the training window, the model will treat it as normal.
   Recommend training on a period that's been reviewed/cleared first.
2. **Contamination is a knob, not ground truth**: `contamination` is your
   *a priori guess* at what fraction of traffic is anomalous. Wrong guesses
   shift the threshold — this needs tuning against your actual environment
   and false-positive tolerance, not a one-time setting.
3. **Beacon detector can be evaded by deliberate jitter**: attackers who
   randomize their check-in interval enough will raise the coefficient of
   variation above the threshold. This is a real, known limitation of
   timing-based beacon detection generally, not specific to this
   implementation — pair with other signals (destination reputation, JA3
   fingerprinting, etc.) for defense in depth.
4. **This is a decision-support tool, not an automated blocker.** Alerts are
   designed to be triaged by an analyst, not to trigger automatic firewall
   actions, given the false-positive risk inherent to any unsupervised model.

## Next Steps for Production Deployment

1. Validate against your own historical incident data (do known-bad events
   score high?) before trusting thresholds.
2. Wire `output/alerts.json` into your SIEM/SOAR via a small forwarder
   (webhook, syslog, or scheduled ingestion job) instead of reading the file
   manually.
3. Add a feedback loop: let analysts mark alerts as true/false positive and
   feed that back into `contamination`/`alert_risk_threshold` tuning, or
   eventually a semi-supervised model.
4. Consider running this on a schedule (cron/Airflow) against rolling
   windows of live flow exports rather than a single static CSV.
