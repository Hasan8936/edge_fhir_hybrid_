"""
Edge FHIR Hybrid - Flask Backend Server
Serves the dashboard and /api/alerts endpoint for real-time anomaly alerts.
"""

from flask import Flask, render_template, jsonify
import json
import os
from datetime import datetime
from pathlib import Path

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '../dashboard/templates'),
    static_folder=os.path.join(os.path.dirname(__file__), '../dashboard/static')
)

# Configuration
ALERTS_LOG_PATH = os.path.join(os.path.dirname(__file__), '../logs/alerts.log')
MAX_ALERTS_RETURN = 50


def read_alerts_from_log():
    """
    Read and parse alerts from the alerts.log file.
    Each line is a JSON object representing one alert.
    Returns list of alerts, sorted by timestamp (newest first).
    """
    alerts = []
    
    if not os.path.exists(ALERTS_LOG_PATH):
        return alerts
    
    try:
        with open(ALERTS_LOG_PATH, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    alert = json.loads(line)
                    alerts.append(alert)
                except json.JSONDecodeError:
                    # Skip malformed JSON lines
                    continue
    except Exception as e:
        print(f"Error reading alerts log: {e}")
        return []
    
    # Sort by timestamp (newest first)
    alerts.sort(
        key=lambda x: x.get('timestamp', ''),
        reverse=True
    )
    
    return alerts[:MAX_ALERTS_RETURN]


@app.route('/', methods=['GET'])
def dashboard():
    """Serve the main dashboard HTML."""
    return render_template('dashboard.html')


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """
    API endpoint: Return recent alerts as JSON.
    
    Response format:
    {
        "alerts": [
            {
                "timestamp": "2025-12-21T10:30:45.123456",
                "source_ip": "192.168.1.100",
                "prediction": "Attack",
                "anomaly_score": 0.8752,
                "severity": "HIGH",
                "raw_fhir_id": "audit-event-12345"
            },
            ...
        ]
    }
    """
    alerts = read_alerts_from_log()
    return jsonify({
        'alerts': alerts,
        'count': len(alerts),
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring."""
    return jsonify({
        'status': 'ok',
        'service': 'edge_fhir_hybrid',
        'version': '1.0'
    })


if __name__ == '__main__':
    # Development mode: debug=True, host='127.0.0.1'
    # Production (Jetson): debug=False, host='0.0.0.0'
    app.run(
        debug=True,
        host='127.0.0.1',
        port=5000,
        threaded=True
    )
