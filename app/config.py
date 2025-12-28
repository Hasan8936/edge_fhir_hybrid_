"""
Config Module - Centralized configuration for Edge FHIR Hybrid
"""

import os
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Model paths
MODELS_DIR = PROJECT_ROOT / 'models'
MODEL_ONNX_PATH = MODELS_DIR / 'cnn_model.onnx'
MODEL_TENSORRT_PATH = MODELS_DIR / 'cnn_model.engine'
MODEL_H5_PATH = MODELS_DIR / 'cnn_model.h5'
MODEL_TFLITE_PATH = MODELS_DIR / 'cnn_model.tflite'

SCALER_PATH = MODELS_DIR / 'scaler.pkl'
LABEL_ENCODER_PATH = MODELS_DIR / 'label_encoder.pkl'
FEATURE_MASK_PATH = MODELS_DIR / 'feature_mask.npy'

# Log paths
LOGS_DIR = PROJECT_ROOT / 'logs'
ALERTS_LOG_PATH = LOGS_DIR / 'alerts.log'

# Dashboard paths
DASHBOARD_DIR = PROJECT_ROOT / 'dashboard'
TEMPLATES_DIR = DASHBOARD_DIR / 'templates'
DASHBOARD_HTML_PATH = TEMPLATES_DIR / 'dashboard.html'

# Feature extraction
FEATURE_SIZE = 64

# Anomaly detection thresholds
ANOMALY_THRESHOLD_LOW = 0.4
ANOMALY_THRESHOLD_MEDIUM = 0.7

# Inference runtime (set based on deployment target)
# 'onnx' for Windows/Linux development
# 'tensorrt' for Jetson Nano production
INFERENCE_RUNTIME = 'onnx'  # Change to 'tensorrt' on Jetson

# Flask server config
FLASK_DEBUG = True  # Set to False in production
FLASK_HOST = '127.0.0.1'  # Set to '0.0.0.0' on Jetson for external access
FLASK_PORT = 5000

# API config
MAX_ALERTS_RETURN = 50

# FHIR Server Configuration - Public HAPI FHIR Server
FHIR_SERVER_BASE_URL = 'https://hapi.fhir.org/baseR4'
FHIR_SUBSCRIPTION_ENDPOINT = 'http://YOUR_PUBLIC_IP:5001/fhir/notify'
FHIR_SUBSCRIPTION_CONFIG_PATH = PROJECT_ROOT / 'config' / 'fhir_subscription.json'

# FHIR Event Polling Configuration (Alternative to subscriptions)
FHIR_POLLING_ENABLED = True  # Enable polling for events
FHIR_POLLING_INTERVAL = 30  # Seconds between polls
FHIR_POLLING_BATCH_SIZE = 20  # How many events to fetch per poll
FHIR_POLLING_RESOURCE_TYPE = 'AuditEvent'  # Resource type to monitor
FHIR_POLLING_TRACKER_FILE = PROJECT_ROOT / '.fhir_polling_tracker.json'

# Batch processing
BATCH_SIZE = 32

# Ensure directories exist
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)
