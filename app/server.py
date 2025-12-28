"""
Edge FHIR Hybrid - Flask Backend Server
Serves the dashboard and /api/alerts endpoint for real-time anomaly alerts.
Polls public HAPI FHIR server for AuditEvents.
"""

from flask import Flask, render_template, jsonify, request
import json
import numpy as np
import traceback
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

# Global poller instance (will be initialized in main)
fhir_poller = None


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


# Initialize components for /fhir/notify pipeline (best-effort)
from fhir_features import FHIRFeatureExtractor
from edge_model import EdgeCNNModel
from detector import AnomalyDetector

# Try to load ONNX model; if unavailable, fallback to mock inference
MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/cnn_model.onnx')
MODEL_RUNTIME = 'onnx'
feature_extractor = FHIRFeatureExtractor(feature_size=64)
model = None
model_input_size = feature_extractor.feature_size
model_output_size = 8

try:
    if os.path.exists(MODEL_PATH):
        model = EdgeCNNModel(MODEL_PATH, runtime=MODEL_RUNTIME)
        if model.get_input_size() is not None:
            model_input_size = model.get_input_size()
        if model.get_output_size() is not None:
            model_output_size = model.get_output_size()
except Exception as e:
    print(f"Warning: failed to load model: {e}")

# Create human-readable class labels (truncate/extend to model output size)
default_labels = ['Normal', 'Recon', 'DDoS', 'BruteForce', 'DoS', 'Web', 'Spoofing', 'Other']
class_labels = {}
for i in range(model_output_size):
    if i < len(default_labels):
        class_labels[i] = default_labels[i]
    else:
        class_labels[i] = f'class_{i}'

detector = AnomalyDetector(class_labels=class_labels)


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
@app.route("/fhir/notify", methods=["POST"])
def fhir_notify():
    """Receive FHIR AuditEvent, run feature extraction + inference + alert logging.

    Returns the alert JSON (including 8-class probabilities if available).
    This handler is defensive: if the model is not available it will produce
    a mock softmax probability vector so the pipeline can be tested end-to-end.
    """
    try:
        payload = request.get_json(force=True)

        # If the incoming AuditEvent doesn't include agent.network.address,
        # inject the client's IP address from the HTTP request so the
        # feature extractor can find a source IP instead of returning 'UNKNOWN'.
        try:
            has_ip = False
            if isinstance(payload, dict):
                a = payload.get('agent')
                if isinstance(a, list) and len(a) > 0:
                    net = a[0].get('network') if isinstance(a[0], dict) else None
                    if isinstance(net, dict) and net.get('address'):
                        has_ip = True
            if not has_ip:
                # Use Flask's request.remote_addr as a best-effort fallback
                payload.setdefault('agent', [{'network': {'address': request.remote_addr}}])
        except Exception:
            # Defensive: if payload shape is unexpected, continue without failing
            pass

        alert = process_fhir_event_payload(payload)
        return jsonify(alert), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def _normalize_features(features, target_size):
    """Ensure feature vector length matches model input size.

    Simple strategy: truncate if longer, pad with zeros if shorter.
    """
    try:
        feats = list(features)
    except Exception:
        feats = [0.0]

    if len(feats) == target_size:
        return feats
    if len(feats) > target_size:
        return feats[:target_size]
    # pad
    return feats + [0.0] * (target_size - len(feats))


def process_fhir_event_payload(payload: dict) -> dict:
    """
    Process a FHIR AuditEvent payload and return an alert dict.

    This function is safe to call outside Flask request context (used by poller).
    """
    try:
        # Extract features and source ip
        features = feature_extractor.extract_features(payload)
        source_ip = feature_extractor.extract_source_ip(payload)
        fhir_id = payload.get('id') if isinstance(payload, dict) else None

        # Determine expected input size
        expected_input = model_input_size
        if model is not None and hasattr(model, 'get_input_size'):
            mi = model.get_input_size()
            if mi is not None:
                expected_input = mi

        # Normalize feature vector to expected model input size
        features = _normalize_features(features, expected_input)

        # Run inference (ONNX if available, otherwise mock 8-class softmax)
        if model is not None:
            try:
                out = model.infer(features)
                probs = np.array(out).flatten().tolist()
            except Exception as e:
                # If model inference fails, log and fall back to mock probs
                print(f"Model inference failed: {e}")
                rand = np.random.rand(model_output_size)
                probs = (rand / np.sum(rand)).tolist()
        else:
            # Mock: create an 8-class softmax with a random peak
            rand = np.random.rand(model_output_size)
            probs = (rand / np.sum(rand)).tolist()

        # Ensure probs length matches detector expectation
        if len(probs) != len(detector.class_labels):
            target = len(detector.class_labels)
            if len(probs) < target:
                probs = probs + [0.0] * (target - len(probs))
            else:
                probs = probs[:target]

        det = detector.process_alert(probs, source_ip, fhir_id)

        # Compose alert with both legacy and compact keys
        ts = datetime.utcnow().isoformat()
        pred_label = det.get('prediction')
        score = float(det.get('anomaly_score', 0.0))
        sev = det.get('severity')

        final_alert = {
            'timestamp': ts,
            'ts': ts,
            'source_ip': source_ip or 'UNKNOWN',
            'prediction': pred_label,
            'pred': pred_label,
            'anomaly_score': score,
            'score': score,
            'severity': sev,
            'sev': sev,
            'raw_fhir_id': fhir_id,
            'predicted_class': int(np.argmax(probs)),
            'class_probs': [float(x) for x in probs],
            'meta': {
                'true': pred_label,
                'sample_id': None,
                'raw_fhir_id': fhir_id,
            }
        }

        # Append to alerts log (safe outside app context)
        try:
            Path(os.path.dirname(ALERTS_LOG_PATH)).mkdir(parents=True, exist_ok=True)
            with open(ALERTS_LOG_PATH, 'a', encoding='utf-8') as f:
                f.write(json.dumps(final_alert) + '\n')
        except Exception as e:
            print(f"Failed to write alert log: {e}")

        return final_alert

    except Exception as e:
        traceback.print_exc()
        return {'error': str(e)}


if __name__ == '__main__':
    # Import config
    from config import (
        FHIR_SERVER_BASE_URL,
        FHIR_POLLING_ENABLED,
        FHIR_POLLING_INTERVAL,
        FHIR_POLLING_BATCH_SIZE,
        FHIR_POLLING_RESOURCE_TYPE,
        FHIR_POLLING_TRACKER_FILE
    )
    from fhir_event_poller import FHIREventPoller
    
    # Initialize FHIR Event Poller if enabled
    if FHIR_POLLING_ENABLED:
        print(f"\n{'='*60}")
        print(f"FHIR Event Polling Configuration")
        print(f"{'='*60}")
        print(f"✓ FHIR Server: {FHIR_SERVER_BASE_URL}")
        print(f"✓ Resource Type: {FHIR_POLLING_RESOURCE_TYPE}")
        print(f"✓ Poll Interval: {FHIR_POLLING_INTERVAL}s")
        print(f"✓ Batch Size: {FHIR_POLLING_BATCH_SIZE}")
        print(f"{'='*60}\n")
        
        fhir_poller = FHIREventPoller(
            fhir_base_url=FHIR_SERVER_BASE_URL,
            poll_interval_seconds=FHIR_POLLING_INTERVAL,
            batch_size=FHIR_POLLING_BATCH_SIZE,
            resource_type=FHIR_POLLING_RESOURCE_TYPE,
            tracking_file=str(FHIR_POLLING_TRACKER_FILE)
        )
        
        # Start polling with a safe callback that uses the context-free processor
        def _poller_callback(event):
            try:
                alert = process_fhir_event_payload(event)
                if isinstance(alert, dict) and alert.get('error'):
                    print(f"Poller processing error: {alert.get('error')}")
                else:
                    print(f"Poller processed event: {alert.get('raw_fhir_id', alert.get('id'))} -> {alert.get('severity')}")
            except Exception as e:
                print(f"Error in poller callback: {e}")

        fhir_poller.start_polling(
            callback=_poller_callback,
            daemon=True
        )
        print("✓ FHIR Event Poller started in background\n")
    
    # Development mode: debug=True, host='127.0.0.1'
    # Production (Jetson): debug=False, host='0.0.0.0'
    print(f"Starting Flask server on http://127.0.0.1:5000")
    print(f"Dashboard: http://localhost:5000/")
    print(f"API Health: http://localhost:5000/api/health")
    print(f"Get Alerts: http://localhost:5000/api/alerts\n")
    
    try:
        app.run(
            debug=True,
            host='127.0.0.1',
            port=5000,
            threaded=True
        )
    finally:
        # Cleanup
        if fhir_poller and fhir_poller.is_running:
            print("\nShutting down FHIR poller...")
            fhir_poller.stop_polling()
