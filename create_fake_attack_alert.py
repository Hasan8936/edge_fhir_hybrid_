import json
from datetime import datetime
import os

ALERTS_LOG_PATH = os.path.join(os.path.dirname(__file__), 'logs', 'alerts.log')

alert = {
    'timestamp': datetime.utcnow().isoformat(),
    'ts': datetime.utcnow().isoformat(),
    'source_ip': '203.0.113.5',
    'prediction': 'Attack',
    'pred': 'Attack',
    'anomaly_score': 0.95,
    'score': 0.95,
    'severity': 'HIGH',
    'sev': 'HIGH',
    'raw_fhir_id': 'fake-attack-1',
    'predicted_class': 1,
    'class_probs': [0.01, 0.95, 0.01, 0.01, 0.01, 0.005, 0.005, 0.0],
    'meta': {
        'true': 'Attack',
        'sample_id': 0,
        'raw_fhir_id': 'fake-attack-1'
    }
}

os.makedirs(os.path.dirname(ALERTS_LOG_PATH), exist_ok=True)
with open(ALERTS_LOG_PATH, 'a', encoding='utf-8') as f:
    f.write(json.dumps(alert) + '\n')

print('Wrote fake attack alert to', ALERTS_LOG_PATH)
