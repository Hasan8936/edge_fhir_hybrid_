# Edge FHIR Hybrid - System Architecture & Data Flow

## 1. PROJECT OVERVIEW

**Edge FHIR Hybrid** is a lightweight security monitoring system that:
- Ingests **FHIR AuditEvent** JSON from healthcare systems
- Extracts **numeric features** from FHIR data
- Runs **CNN-based anomaly detection** for real-time threat identification
- Logs **security alerts** with severity levels
- Displays results on a **minimal HTML/CSS dashboard**

**Target Platforms:**
- **Development:** Windows + Python + ONNX Runtime (CPU)
- **Production:** NVIDIA Jetson Nano + TensorRT (GPU)

---

## 2. SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                     Healthcare System                           │
│                   (EHR / FHIR Server)                          │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    │ FHIR AuditEvent JSON
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│              Flask Backend (Python)                             │
│                    server.py                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ POST /ingest/audit-event                                │   │
│  │  - Receives FHIR AuditEvent JSON                        │   │
│  │  - Validates & logs raw event                           │   │
│  └────────────┬─────────────────────────────────────────────┘   │
│               │                                                  │
│               ▼                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ FHIR Feature Extraction (fhir_features.py)             │   │
│  │  - Parse FHIR fields (type, action, outcome, etc.)     │   │
│  │  - Encode categorical values                            │   │
│  │  - Extract timestamp features                           │   │
│  │  - Convert IP addresses to numeric                      │   │
│  │  → Output: Feature vector [64 floats]                  │   │
│  └────────────┬─────────────────────────────────────────────┘   │
│               │                                                  │
│               ▼                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ CNN Inference (edge_model.py)                           │   │
│  │  - Load ONNX or TensorRT model                          │   │
│  │  - Run prediction on feature vector                      │   │
│  │  → Output: Class probabilities [2-3 values]            │   │
│  └────────────┬─────────────────────────────────────────────┘   │
│               │                                                  │
│               ▼                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Detector / Severity Mapping (detector.py)               │   │
│  │  - Map max probability to anomaly_score                 │   │
│  │  - Compute severity (LOW / MEDIUM / HIGH)               │   │
│  │  → Output: Alert JSON                                   │   │
│  └────────────┬─────────────────────────────────────────────┘   │
│               │                                                  │
│               ▼                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Alert Logging                                            │   │
│  │  - Write alert JSON to alerts.log (line-delimited)      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ GET /api/alerts                                          │   │
│  │  - Read last 50 alerts from logs                        │   │
│  │  - Return as JSON array                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ GET /                                                    │   │
│  │  - Serve dashboard.html                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                    │
                    │ HTTP
                    ▼
┌─────────────────────────────────────────────────────────────────┐
│          Web Browser (Client)                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ dashboard.html                                           │   │
│  │  - Pure HTML + CSS + minimal JavaScript                │   │
│  │  - Polls /api/alerts every 5 seconds                   │   │
│  │  - Displays alerts in table format                      │   │
│  │  - Color-coded by severity (LOW/MEDIUM/HIGH)           │   │
│  │  - Real-time statistics (counts, last update)          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. DATA FLOW: FHIR → FEATURES → INFERENCE → ALERT

### 3.1 Input: FHIR AuditEvent JSON

Example FHIR AuditEvent resource:

```json
{
  "resourceType": "AuditEvent",
  "id": "audit-event-12345",
  "type": {
    "code": "110100",
    "display": "Application Activity"
  },
  "action": "R",
  "outcome": "0",
  "recorded": "2025-12-21T10:30:45.123456Z",
  "source": {
    "observer": {
      "display": "EHR-Server-01"
    }
  },
  "agent": [
    {
      "network": {
        "address": "192.168.1.50",
        "type": "2"
      },
      "name": "healthcare_worker_01"
    }
  ]
}
```

### 3.2 Feature Extraction

**FHIR Fields → Numeric Features**

| FHIR Field | Type | Extraction | Feature Value |
|-----------|------|-----------|------------------|
| `type.code` | string | Hash encoding | 0.0–1.0 |
| `action` | string | Hash encoding | 0.0–1.0 |
| `outcome` | string | Hash encoding | 0.0–1.0 |
| `source.observer.display` | string | Hash encoding | 0.0–1.0 |
| `recorded` (hour) | timestamp | Extract hour (0-23) | 0.0–1.0 |
| `recorded` (minute) | timestamp | Extract minute (0-59) | 0.0–1.0 |
| `recorded` (second) | timestamp | Extract second (0-59) | 0.0–1.0 |
| `agent[0].network.address` | IP | Parse octets (0-255) | 4 × [0.0–1.0] |
| (Padding) | — | Zero-fill to 64 | 0.0 |

**Result:** A 64-dimensional feature vector, all values in range [0.0, 1.0]

**Code Location:** [app/fhir_features.py](app/fhir_features.py)

### 3.3 CNN Inference

**Model Characteristics:**
- Input: 64-dimensional numeric vector
- Architecture: Convolutional Neural Network (2–3 layers)
- Output: Probability distribution over classes
  - Example: `[0.1, 0.85, 0.05]` → class 1 (Attack) with 85% confidence

**Inference Runtimes:**
- **Windows/Linux:** ONNX Runtime (CPU) — fast, low-memory
- **Jetson Nano:** TensorRT engine (GPU) — optimized for edge

**Code Location:** [app/edge_model.py](app/edge_model.py)

### 3.4 Severity Detection

**Anomaly Score → Severity Mapping**

Anomaly Score = max(output probabilities)

| Anomaly Score | Severity | Meaning |
|---------------|----------|---------|
| 0.0 – 0.40 | LOW | Likely normal behavior |
| 0.40 – 0.70 | MEDIUM | Suspicious; monitor |
| 0.70 – 1.00 | HIGH | Likely attack; alert |

**Thresholds:** Configurable in [app/config.py](app/config.py)

**Code Location:** [app/detector.py](app/detector.py)

### 3.5 Output: Alert JSON

```json
{
  "timestamp": "2025-12-21T10:30:45.123456",
  "source_ip": "192.168.1.50",
  "prediction": "Attack",
  "anomaly_score": 0.8752,
  "severity": "HIGH",
  "raw_fhir_id": "audit-event-12345",
  "meta": {}
}
```

**Logged to:** `logs/alerts.log` (one JSON per line)

---

## 4. PROJECT STRUCTURE

```
edge_fhir_hybrid/
│
├── app/                          # Backend Python
│   ├── server.py                # Flask entrypoint
│   ├── edge_model.py            # CNN ONNX/TensorRT wrapper
│   ├── detector.py              # Anomaly scoring + severity
│   ├── fhir_features.py         # FHIR JSON → feature extraction
│   └── config.py                # Config (paths, thresholds)
│
├── models/                       # Pre-trained models (NOT in repo)
│   ├── cnn_model.onnx           # ONNX Runtime model (Windows)
│   ├── cnn_model.engine         # TensorRT engine (Jetson)
│   ├── cnn_model.h5             # Original Keras/TF (reference)
│   ├── scaler.pkl               # Feature normalization (optional)
│   └── label_encoder.pkl        # Class name mapping (optional)
│
├── dashboard/                    # Frontend
│   └── templates/
│       └── dashboard.html       # Main UI (HTML + CSS + JS)
│
├── logs/                         # Runtime logs
│   └── alerts.log               # Line-delimited JSON alerts
│
├── tests/                        # Test data & scripts
│   ├── test_server_notify.py    # Integration test
│   ├── test_infer.json          # Test feature vectors
│   └── sample_audit.json        # Sample FHIR AuditEvent
│
├── tools/                        # Utilities
│   ├── convert_cnn_to_onnx.py   # ONNX conversion script
│   └── jetson_preflight_check.sh # Jetson setup validation
│
└── README.md                     # Project documentation
```

---

## 5. API ENDPOINTS

### 5.1 Ingest FHIR AuditEvent (Not yet implemented in server.py)

```
POST /ingest/audit-event
Content-Type: application/json

{
  "audit_event": { /* FHIR AuditEvent JSON */ }
}

Response:
{
  "status": "success",
  "alert": { /* Alert JSON */ }
}
```

### 5.2 Get Recent Alerts

```
GET /api/alerts

Response:
{
  "alerts": [
    {
      "timestamp": "2025-12-21T10:30:45.123456",
      "source_ip": "192.168.1.50",
      "prediction": "Attack",
      "anomaly_score": 0.8752,
      "severity": "HIGH",
      "raw_fhir_id": "audit-event-12345"
    },
    ...
  ],
  "count": 47,
  "timestamp": "2025-12-21T10:35:12.654321"
}
```

### 5.3 Health Check

```
GET /api/health

Response:
{
  "status": "ok",
  "service": "edge_fhir_hybrid",
  "version": "1.0"
}
```

### 5.4 Dashboard

```
GET /

Response: dashboard.html (HTML page)
```

---

## 6. DASHBOARD OVERVIEW

**File:** `dashboard/templates/dashboard.html`

**Features:**
- **Pure HTML + CSS** (no React, Vue, or Bootstrap)
- **Minimal inline JavaScript** (polling only)
- **Real-time alerts** via 5-second polling
- **Severity-based coloring:**
  - GREEN (LOW): #4caf50
  - ORANGE (MEDIUM): #ff9800
  - RED (HIGH): #f44336
- **Statistics cards:** HIGH, MEDIUM, LOW, TOTAL counts
- **Responsive design:** Mobile-friendly
- **Low memory footprint:** Suitable for Jetson Nano

**Dashboard Interaction:**
```
Browser
  ↓
GET / (fetch HTML)
  ↓
dashboard.html (rendered)
  ↓
[JavaScript runs]
  ↓
setInterval(refreshAlerts, 5000)
  ↓
fetch(/api/alerts)
  ↓
Update table + statistics
  ↓
User sees live alerts
```

---

## 7. FEATURE EXTRACTION RULES

### Safe Defaults (Never Crash)

Every FHIR field extraction has a safe default:

```python
def safe_get(obj, path, default=None):
    """Navigate nested dict safely."""
    if obj is None:
        return default
    # ... traverse keys ...
    return current or default
```

**Missing Fields Handling:**
- FHIR field missing → default value (0.0 for numeric)
- Network address missing → "0.0.0.0" → [0.0, 0.0, 0.0, 0.0]
- Timestamp unparseable → (0.0, 0.0, 0.0) for time features

### Categorical Encoding

Categorical fields (strings) are encoded as floats using hash-based normalization:

```python
def encode_categorical(value, max_code=10):
    if value is None:
        return 0.0
    hash_val = sum(ord(c) for c in str(value)) % max_code
    return float(hash_val) / max_code
```

Result: Lightweight, deterministic, range [0.0, 1.0]

### IP Address Encoding

IP address (e.g., "192.168.1.50") → 4 octets normalized to [0.0, 1.0]:

```
"192.168.1.50" → [192/255, 168/255, 1/255, 50/255] → [0.753, 0.659, 0.004, 0.196]
```

---

## 8. MODEL CONSTRAINTS & REQUIREMENTS

### No Forbidden Frameworks at Edge
- ❌ scikit-learn (fit/transform at inference time)
- ❌ LightGBM, XGBoost (tree-based models)
- ❌ Large ONNX models (>50 MB)

### Allowed
- ✅ CNN (Keras, TensorFlow, PyTorch)
- ✅ ONNX Runtime (stateless inference)
- ✅ TensorRT (GPU-optimized, Jetson-native)

### Model Conversion Workflow
1. **Train CNN:** Python + TensorFlow/PyTorch
2. **Save as ONNX:** `model.save('cnn_model.onnx')`
3. **Convert for Jetson:** ONNX → TensorRT engine (on Jetson)
4. **Deploy:** Copy `.onnx` to `models/` or `.engine` to Jetson

---

## 9. DEPLOYMENT: DEVELOPMENT vs. PRODUCTION

### Development (Windows)

```bash
# Setup
python -m venv venv
venv\Scripts\activate
pip install flask onnxruntime

# Run
python app/server.py

# Access
# Dashboard: http://127.0.0.1:5000
# Alerts API: http://127.0.0.1:5000/api/alerts
```

### Production (Jetson Nano)

```bash
# On Jetson: Install TensorRT, CUDA dependencies
# Copy project to Jetson
scp -r edge_fhir_hybrid/ nano@jetson:~/

# On Jetson:
cd edge_fhir_hybrid
python -m venv venv
source venv/bin/activate
pip install flask tensorrt

# Update config.py: INFERENCE_RUNTIME = 'tensorrt'
# Update config.py: FLASK_HOST = '0.0.0.0'

# Run
python app/server.py

# Access from network
# Dashboard: http://<jetson-ip>:5000
```

---

## 10. ERROR HANDLING & ROBUSTNESS

### Feature Extraction
- **Missing FHIR fields:** Use safe defaults (0.0)
- **Malformed JSON:** Log error, continue
- **Invalid IP addresses:** Default to 0.0.0.0

### Inference
- **Model not found:** Raise clear error at startup
- **Feature size mismatch:** Validate on load, truncate/pad if needed
- **Invalid probabilities:** Check for NaN/Inf, use fallback

### Logging
- **Alert logging:** Append-only, one JSON per line
- **Malformed alert JSON:** Skip silently, continue
- **Log file corruption:** Handle gracefully (skip bad lines)

---

## 11. PERFORMANCE CONSIDERATIONS

### Memory Usage
- Feature vector: 64 floats = 256 bytes
- ONNX Runtime session: ~50–200 MB (varies by model)
- Jetson Nano: ~200 MB free memory sufficient

### Latency
- Feature extraction: ~1 ms
- ONNX inference: ~5–10 ms (CPU)
- TensorRT inference: ~2–5 ms (GPU, Jetson)
- **Total per event:** ~10–20 ms

### Scalability
- **Single Jetson:** ~50–100 events/sec
- Polling interval: 5 seconds
- Dashboard polling overhead: negligible

---

## 12. SECURITY BEST PRACTICES

### Production Checklist
- [ ] Use HTTPS/TLS for dashboard (reverse proxy, nginx)
- [ ] Disable debug mode (`FLASK_DEBUG=False`)
- [ ] Restrict access to `/api/alerts` (authentication/firewall)
- [ ] Validate FHIR input (schema validation)
- [ ] Sanitize alert display (escape HTML in dashboard)
- [ ] Rotate alert logs periodically
- [ ] Monitor disk space (logs grow over time)

### Code Hardening
- All user input validated before inference
- FHIR fields extracted safely (no crashes on malformed input)
- Model paths validated at startup
- HTML dashboard includes XSS prevention (`escapeHtml()`)

---

## 13. NEXT STEPS

1. **Add FHIR ingest endpoint** to `server.py`:
   ```python
   @app.route('/ingest/audit-event', methods=['POST'])
   def ingest_audit():
       # Parse JSON
       # Extract features
       # Run inference
       # Log alert
   ```

2. **Deploy ONNX model** to `models/cnn_model.onnx`

3. **Test on Jetson Nano** with TensorRT conversion

4. **Add authentication** (JWT, API keys) if needed

5. **Set up Docker** for reproducible deployment

---

## References

- FHIR R4 AuditEvent: https://www.hl7.org/fhir/auditevent.html
- ONNX Runtime: https://onnxruntime.ai/
- TensorRT: https://developer.nvidia.com/tensorrt
- Flask: https://flask.palletsprojects.com/
- Jetson Nano: https://developer.nvidia.com/embedded/jetson-nano

---

**Last Updated:** 2025-12-21  
**Version:** 1.0  
**Author:** Edge FHIR Hybrid Team
