# Public HAPI FHIR Server Integration Guide

## Overview
This project is now configured to connect to the **public HAPI FHIR server** at:
```
https://hapi.fhir.org/baseR4
```

## Configuration Files

### 1. **config/fhir_subscription.json**
Contains the FHIR Subscription resource definition:
- **resourceType**: Subscription (REST-hook based)
- **criteria**: AuditEvent (subscribes to audit events)
- **endpoint**: Your public IP + port 5001 `/fhir/notify`

### 2. **app/config.py**
Updated with FHIR server configuration:
```python
FHIR_SERVER_BASE_URL = 'https://hapi.fhir.org/baseR4'
FHIR_SUBSCRIPTION_ENDPOINT = 'http://YOUR_PUBLIC_IP:5001/fhir/notify'
FHIR_SUBSCRIPTION_CONFIG_PATH = PROJECT_ROOT / 'config' / 'fhir_subscription.json'
```

## Setup Steps

### Step 1: Update Your Public IP
Replace `YOUR_PUBLIC_IP` in the following files with your actual public IP address:

```bash
# Option A: Using sed on Windows PowerShell
$publicIP = "YOUR_ACTUAL_PUBLIC_IP"
(Get-Content config/fhir_subscription.json) -replace 'YOUR_PUBLIC_IP', $publicIP | Set-Content config/fhir_subscription.json
(Get-Content app/config.py) -replace 'YOUR_PUBLIC_IP', $publicIP | Set-Content app/config.py
```

**Option B: Manual Edit**
1. Edit `config/fhir_subscription.json` - Replace `YOUR_PUBLIC_IP` with your public IP
2. Edit `app/config.py` - Replace `YOUR_PUBLIC_IP` with your public IP

### Step 2: Expose Your Local Server (Port Forwarding)

You need to expose port 5001 to the public internet so HAPI can reach your `/fhir/notify` endpoint.

#### Option A: ngrok (Recommended for testing)
```bash
# Install ngrok: https://ngrok.com/download
ngrok http 5001

# This will give you a public URL like:
# Forwarding                    http://abc123.ngrok.io -> http://localhost:5001
```

Then use the ngrok URL as your endpoint:
```json
"endpoint": "http://abc123.ngrok.io/fhir/notify"
```

#### Option B: Port Forwarding (Home/Office Router)
1. Access your router settings (usually 192.168.1.1)
2. Forward external port 5001 → local IP 5001
3. Use your public IP address

#### Option C: Cloud Deployment
Deploy to AWS, Azure, GCP, or other cloud providers for a permanent public endpoint.

### Step 3: Register the Subscription

Use the subscription manager script:

```bash
# Register subscription with HAPI server
python app/fhir_subscription_manager.py register http://YOUR_PUBLIC_IP:5001/fhir/notify

# List all subscriptions
python app/fhir_subscription_manager.py list
```

Or use curl directly:

```bash
curl -X POST https://hapi.fhir.org/baseR4/Subscription \
  -H "Content-Type: application/fhir+json" \
  -d @config/fhir_subscription.json
```

### Step 4: Start the Edge FHIR Server

```bash
python app/server.py
```

The server will run on: `http://127.0.0.1:5000`
(or `http://0.0.0.0:5001` if modified for production)

### Step 5: Test the Integration

#### Test 1: Create a test AuditEvent
```bash
# Post a test audit event to the HAPI server
curl -X POST https://hapi.fhir.org/baseR4/AuditEvent \
  -H "Content-Type: application/fhir+json" \
  -d @tests/sample_audit.json
```

#### Test 2: Check if callback is received
Check the logs:
```bash
# View recent alerts (should show if your endpoint received the notification)
tail -f logs/alerts.log
```

#### Test 3: Query the dashboard
Open your browser and go to: `http://localhost:5000/`

## Project Architecture

```
Project Flow:
1. Create AuditEvent in HAPI FHIR Server
2. HAPI detects event matches "AuditEvent" criteria
3. HAPI sends REST-hook POST to your /fhir/notify endpoint
4. Your Edge FHIR server receives and processes it
5. Feature extraction → Model inference → Anomaly detection
6. Alert logged to logs/alerts.log
7. Dashboard displays the alert in real-time
```

## Troubleshooting

### Issue: Connection refused / Timeout
**Solution**: 
- Check your public IP is correctly configured
- Verify port forwarding/ngrok is active
- Check firewall settings allow port 5001

### Issue: Subscription not firing
**Solution**:
- Verify subscription status is "active" (use list command)
- Check your endpoint is reachable from the internet
- Monitor server logs for incoming requests
- Test with: `curl -X POST http://YOUR_IP:5001/fhir/notify -H "Content-Type: application/fhir+json" -d '{"resourceType":"AuditEvent"}'`

### Issue: Model not loading
**Solution**:
- The system falls back to mock inference if model unavailable
- Check `logs/alerts.log` for detailed error messages
- Verify model files exist in `models/` directory

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Dashboard UI |
| `/api/alerts` | GET | Get recent alerts |
| `/api/health` | GET | Health check |
| `/fhir/notify` | POST | HAPI subscription callback (internal) |

## Additional Resources

- HAPI FHIR Server: https://hapi.fhir.org/baseR4
- FHIR Subscription Documentation: https://www.hl7.org/fhir/subscription.html
- ngrok Tunneling: https://ngrok.com/
- AuditEvent Examples: https://www.hl7.org/fhir/auditevent-examples.html

## Next Steps

1. ✓ Update public IP in config files
2. ✓ Set up port forwarding / ngrok
3. ✓ Register subscription with HAPI
4. ✓ Start your Edge FHIR server
5. ✓ Test with sample AuditEvents
6. Monitor `logs/alerts.log` for incoming events
