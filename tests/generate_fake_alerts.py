"""
Generate fake FHIR-derived alerts for testing the dashboard and /api/alerts.
Writes JSON-lines to ../logs/alerts.log (one JSON object per line).

Usage:
    python tests/generate_fake_alerts.py

Options:
    --count N       Number of alerts to generate (default 20)
    --overwrite     Overwrite the alerts.log file instead of appending
"""

import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
DEFAULT_COUNT = 20
BASE_DIR = Path(__file__).resolve().parents[1]
LOGS_DIR = BASE_DIR / 'logs'
ALERTS_LOG_PATH = LOGS_DIR / 'alerts.log'

SOURCE_IPS = [
    "192.168.1.10",
    "192.168.1.20",
    "192.168.1.30",
    "192.168.1.40",
    "192.168.1.50",
    "10.0.0.5",
    "10.0.0.8",
]

PREDICTIONS = ["Normal", "Attack"]


def make_alert(i, attack_probability=0.5):
    is_attack = random.random() < attack_probability
    timestamp = (datetime.utcnow() - timedelta(seconds=random.randint(0, 3600))).isoformat()
    source_ip = random.choice(SOURCE_IPS)

    if is_attack:
        prediction = "Attack"
        anomaly_score = round(random.uniform(0.7, 0.99), 4)
        severity = random.choice(["HIGH", "CRITICAL"])
    else:
        prediction = "Normal"
        anomaly_score = round(random.uniform(0.0, 0.3), 4)
        severity = random.choice(["LOW", "MEDIUM"])  # normal entries may be low/medium

    alert = {
        "timestamp": timestamp,
        "source_ip": source_ip,
        "prediction": prediction,
        "anomaly_score": anomaly_score,
        "severity": severity,
        "raw_fhir_id": f"fake-audit-{i:03d}"
    }

    return alert


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--attack-ratio", type=float, default=0.5,
                        help="Fraction of generated alerts to mark as Attack (0.0-1.0)")
    args = parser.parse_args()

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    mode = "w" if args.overwrite else "a"
    with ALERTS_LOG_PATH.open(mode, encoding="utf-8") as f:
        for i in range(1, args.count + 1):
            alert = make_alert(i, attack_probability=args.attack_ratio)
            f.write(json.dumps(alert) + "\n")

    print(f"Wrote {args.count} alerts to {ALERTS_LOG_PATH}")

    # Print a short summary
    attacks = 0
    normals = 0
    with ALERTS_LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if obj.get("prediction") == "Attack":
                    attacks += 1
                else:
                    normals += 1
            except Exception:
                continue

    print(f"Summary: {attacks} attacks, {normals} normal (total {attacks+normals}) in {ALERTS_LOG_PATH}")


if __name__ == "__main__":
    main()
