# Quick Reference - FHIR Event Polling

## Start the Server
```bash
python app/server.py
```

Expected output:
```
✓ FHIR Event Polling Configuration
✓ FHIR Server: https://hapi.fhir.org/baseR4
✓ Poll Interval: 30s
✓ FHIR Event Poller started in background
✓ Starting Flask server on http://127.0.0.1:5000
```

## Access Your Application

| Feature | URL |
|---------|-----|
| **Dashboard** | http://localhost:5000/ |
| **Alerts API** | http://localhost:5000/api/alerts |
| **Health Check** | http://localhost:5000/api/health |

## Create Test Events

```bash
python create_test_audit_event.py
```

Output: `✓ AuditEvent created successfully! ID: 53651882`

## Test Polling

```bash
python test_polling.py
```

This will:
1. Verify HAPI server connectivity ✓
2. Fetch and display events ✓
3. Run continuous polling for 10s ✓

## View Alerts

### Via Dashboard
Open http://localhost:5000 in browser

### Via Command Line
```bash
# Windows PowerShell
Get-Content logs/alerts.log -Tail 10 -Wait

# Linux/Mac
tail -f logs/alerts.log

# Or via API
curl http://localhost:5000/api/alerts
```

## Configuration

Edit `app/config.py` to customize:

```python
# Polling frequency (seconds)
FHIR_POLLING_INTERVAL = 30          # Change to 15 for faster, 60 for slower

# Events per poll
FHIR_POLLING_BATCH_SIZE = 20        # Change to 50 for more events

# Resource type to monitor
FHIR_POLLING_RESOURCE_TYPE = 'AuditEvent'  # Change to 'Patient', 'Observation', etc.

# Enable/disable polling
FHIR_POLLING_ENABLED = True         # Set to False to disable
```

## Troubleshooting

### No events being fetched?
```bash
# 1. Create a test event
python create_test_audit_event.py

# 2. Reset polling tracker
del .fhir_polling_tracker.json

# 3. Run test
python test_polling.py
```

### Check polling status
```bash
# View recent alerts
curl http://localhost:5000/api/alerts | python -m json.tool

# Check server health
curl http://localhost:5000/api/health
```

### HAPI server unreachable?
```bash
# Verify connectivity
python create_test_audit_event.py
# Should return HTTP 201 if working
```

## Project Structure

```
edge_fhir_hybrid/
├── app/
│   ├── server.py                 ← Main Flask app (with polling)
│   ├── fhir_event_poller.py      ← Polling implementation
│   ├── config.py                 ← Configuration
│   ├── fhir_features.py          ← Feature extraction
│   ├── edge_model.py             ← ML model
│   └── detector.py               ← Anomaly detection
├── logs/
│   └── alerts.log                ← Alert logs
├── models/
│   ├── cnn_model.onnx            ← ML model
│   └── feature_mask.npy          ← Feature mask
├── dashboard/
│   └── templates/dashboard.html  ← Web UI
├── tests/
│   └── ...
├── .fhir_polling_tracker.json    ← Auto-generated state file
├── test_polling.py               ← Test script
├── create_test_audit_event.py    ← Create test data
└── POLLING_INTEGRATION.md        ← Full documentation
```

## API Response Examples

### Get Alerts
```bash
curl http://localhost:5000/api/alerts
```

Response:
```json
{
  "alerts": [
    {
      "timestamp": "2025-12-21T13:45:20.123456",
      "source_ip": "192.168.1.100",
      "prediction": "Attack",
      "anomaly_score": 0.8752,
      "severity": "HIGH",
      "raw_fhir_id": "53651882",
      "predicted_class": 5,
      "class_probs": [0.1, 0.05, 0.05, 0.08, 0.04, 0.67, 0.02, 0.03]
    }
  ],
  "count": 1,
  "timestamp": "2025-12-21T13:45:25.654321"
}
```

### Health Check
```bash
curl http://localhost:5000/api/health
```

Response:
```json
{
  "status": "ok",
  "service": "edge_fhir_hybrid",
  "version": "1.0"
}
```

## Key Features

✅ **Automatic Polling** - Runs every 30 seconds by default
✅ **Deduplication** - Avoids processing same events twice
✅ **State Persistence** - Tracks progress across restarts
✅ **Background Thread** - Non-blocking, runs alongside Flask
✅ **Error Handling** - Continues on errors, logs issues
✅ **Configurable** - Easy to adjust intervals and resource types
✅ **Production Ready** - Tested with real HAPI server

## Common Commands

```bash
# Start server with polling
python app/server.py

# Test polling functionality
python test_polling.py

# Create a test AuditEvent
python create_test_audit_event.py

# View recent alerts (Windows)
Get-Content logs/alerts.log -Tail 20

# View recent alerts (Linux/Mac)
tail -20 logs/alerts.log

# Check alerts via API
curl http://localhost:5000/api/alerts

# Reset polling state (fetch older events)
del .fhir_polling_tracker.json
```

## Polling States

| State | Meaning | Action |
|-------|---------|--------|
| **First Run** | No tracking file | Fetches events from last 1 hour |
| **Running** | Polling in progress | Shows "polling thread started" |
| **Stopped** | Server shutdown | State saved to .fhir_polling_tracker.json |
| **Restarted** | Server restarted | Resumes from last timestamp |

## Customization Examples

### Faster Real-Time Polling
```python
# app/config.py
FHIR_POLLING_INTERVAL = 10          # Every 10 seconds instead of 30
FHIR_POLLING_BATCH_SIZE = 50        # Fetch more events
```

### Monitor Patients Instead
```python
# app/config.py
FHIR_POLLING_RESOURCE_TYPE = 'Patient'
FHIR_POLLING_INTERVAL = 60          # Every minute
```

### Disable Polling
```python
# app/config.py
FHIR_POLLING_ENABLED = False        # Manual webhook only
```

## Need Help?

1. **Check documentation**: See `POLLING_INTEGRATION.md`
2. **Run tests**: `python test_polling.py`
3. **View logs**: `logs/alerts.log`
4. **Test events**: `python create_test_audit_event.py`

## Summary

Your system now:
- ✓ Polls HAPI FHIR server every 30 seconds
- ✓ Automatically detects and processes AuditEvents
- ✓ Runs ML anomaly detection on events
- ✓ Logs alerts in real-time
- ✓ Provides web dashboard and API

**It's ready to use!** 🚀
