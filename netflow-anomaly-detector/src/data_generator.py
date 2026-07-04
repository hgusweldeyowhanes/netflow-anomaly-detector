"""
Synthetic NetFlow-style traffic generator.

Purpose: produce a realistic-looking flow log (source IP, dest IP, port, bytes,
duration, timestamp) for demoing and testing the anomaly detection pipeline
when a real NetFlow/Zeek export isn't available.

Three types of injected anomalies are included so detection can be validated:
  1. Beaconing        - a host calling out to the same external IP at very
                         regular intervals (C2-style behavior)
  2. Data exfiltration - a host sending an unusually large volume of bytes
                         outbound in a short window
  3. Port scan        - a host touching many distinct destination ports
                         across many hosts in a short window

Run directly to generate data/flows.csv:
    python src/data_generator.py
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import ipaddress
import random

RNG = np.random.default_rng(42)
random.seed(42)


def _random_internal_ip():
    return f"10.0.{random.randint(0, 20)}.{random.randint(2, 254)}"


def _random_external_ip():
    return str(ipaddress.IPv4Address(random.randint(0x01000000, 0xDFFFFFFF)))


def generate_normal_traffic(n_hosts=40, hours=6, flows_per_host_per_hour=15, start_time=None):
    """Simulate typical internal-to-external and internal-to-internal traffic."""
    start_time = start_time or (datetime.now() - timedelta(hours=hours))
    hosts = [_random_internal_ip() for _ in range(n_hosts)]
    common_ports = [443, 443, 443, 80, 80, 53, 22, 3389, 445, 8080]
    rows = []

    for host in hosts:
        n_flows = int(RNG.normal(flows_per_host_per_hour * hours, flows_per_host_per_hour * hours * 0.2))
        n_flows = max(n_flows, 5)
        for _ in range(n_flows):
            offset_minutes = RNG.uniform(0, hours * 60)
            ts = start_time + timedelta(minutes=offset_minutes)
            dest = _random_external_ip() if random.random() < 0.7 else _random_internal_ip()
            port = random.choice(common_ports)
            bytes_sent = max(int(RNG.lognormal(mean=8, sigma=1.2)), 100)
            duration = max(RNG.exponential(scale=2.0), 0.1)
            rows.append({
                "timestamp": ts,
                "src_ip": host,
                "dst_ip": dest,
                "dst_port": port,
                "protocol": "TCP" if port != 53 else "UDP",
                "bytes_out": bytes_sent,
                "bytes_in": max(int(bytes_sent * RNG.uniform(0.1, 3.0)), 0),
                "duration_sec": round(duration, 2),
            })
    return rows, hosts, start_time


def inject_beaconing(rows, hosts, start_time, hours, interval_minutes=10, jitter_seconds=5):
    """A single compromised host calls out to one external C2 IP at a fixed interval."""
    infected_host = random.choice(hosts)
    c2_ip = _random_external_ip()
    n_beacons = int((hours * 60) / interval_minutes)
    for i in range(n_beacons):
        jitter = RNG.uniform(-jitter_seconds, jitter_seconds)
        ts = start_time + timedelta(minutes=i * interval_minutes, seconds=jitter)
        rows.append({
            "timestamp": ts,
            "src_ip": infected_host,
            "dst_ip": c2_ip,
            "dst_port": 443,
            "protocol": "TCP",
            "bytes_out": int(RNG.normal(512, 20)),   # very consistent small payload
            "bytes_in": int(RNG.normal(256, 15)),
            "duration_sec": round(RNG.normal(0.8, 0.05), 2),
        })
    return infected_host, c2_ip


def inject_exfiltration(rows, hosts, start_time, hours):
    """A host sends a very large volume of data outbound in a short burst."""
    host = random.choice(hosts)
    dest = _random_external_ip()
    burst_start = start_time + timedelta(minutes=RNG.uniform(0, hours * 60 - 30))
    for i in range(20):
        ts = burst_start + timedelta(seconds=i * RNG.uniform(1, 5))
        rows.append({
            "timestamp": ts,
            "src_ip": host,
            "dst_ip": dest,
            "dst_port": 443,
            "protocol": "TCP",
            "bytes_out": int(RNG.normal(5_000_000, 500_000)),  # massive outbound transfer
            "bytes_in": int(RNG.normal(5_000, 500)),
            "duration_sec": round(RNG.uniform(5, 15), 2),
        })
    return host, dest


def inject_port_scan(rows, hosts, start_time, hours):
    """A host probes many distinct ports across many distinct hosts rapidly."""
    host = random.choice(hosts)
    scan_start = start_time + timedelta(minutes=RNG.uniform(0, hours * 60 - 10))
    targets = [_random_internal_ip() for _ in range(60)]
    for i, target in enumerate(targets):
        ts = scan_start + timedelta(seconds=i * RNG.uniform(0.2, 1.0))
        rows.append({
            "timestamp": ts,
            "src_ip": host,
            "dst_ip": target,
            "dst_port": random.randint(1, 65535),
            "protocol": "TCP",
            "bytes_out": random.randint(40, 80),   # tiny SYN-style probes
            "bytes_in": 0,
            "duration_sec": round(RNG.uniform(0.01, 0.05), 2),
        })
    return host


def generate_dataset(output_path="data/flows.csv", hours=6):
    rows, hosts, start_time = generate_normal_traffic(hours=hours)
    beacon_host, c2_ip = inject_beaconing(rows, hosts, start_time, hours)
    exfil_host, exfil_dest = inject_exfiltration(rows, hosts, start_time, hours)
    scan_host = inject_port_scan(rows, hosts, start_time, hours)

    df = pd.DataFrame(rows).sort_values("timestamp").reset_index(drop=True)
    df.to_csv(output_path, index=False)

    print(f"Generated {len(df)} flow records -> {output_path}")
    print("\nGround-truth anomalies injected (for validation only, not used by the model):")
    print(f"  Beaconing host:      {beacon_host}  -> C2 IP {c2_ip}")
    print(f"  Exfiltration host:   {exfil_host}  -> {exfil_dest}")
    print(f"  Port scan host:      {scan_host}")
    return df, {"beaconing": beacon_host, "exfiltration": exfil_host, "port_scan": scan_host}


if __name__ == "__main__":
    generate_dataset()
