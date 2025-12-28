# FHIR Subscription Registration - Findings & Solutions

## Problem Found

**HTTP 412 Error**: The public HAPI FHIR server (`hapi.fhir.org`) has **subscription criteria restrictions enabled**.

Error message:
```
HAPI-2672: Criteria is not permitted on this server: [ResourceType]
```

This is a **security configuration** on the public server that restricts what subscriptions can be created (to prevent abuse and resource exhaustion).

## Root Causes

1. **Public HAPI Server Configuration**: The server administrator has disabled or restricted subscription creation to prevent abuse
2. **No Whitelisted Resources**: The server doesn't allow subscriptions on common resources like `AuditEvent`, `Patient`, `Observation`, etc.
3. **REST-Hook Subscriptions Disabled**: The server may require email or other non-REST-hook delivery methods

## Solution Options

### Option 1: Use Your Own HAPI Server (Recommended for Development)
Deploy a local or private HAPI FHIR server where you have full control:

**Local Docker Setup:**
```bash
# Pull and run local HAPI FHIR server
docker run -d --name hapi-fhir \
  -p 8080:8080 \
  hapiproject/hapi:latest
```

**Then use:**
```bash
python register_fhir_subscription.py register http://localhost:8080/fhir/notify/
```

### Option 2: Use a Cloud HAPI Server with Full Permissions
Deploy HAPI on a cloud provider where you control the configuration:
- **AWS** (via EC2 or ECS)
- **Google Cloud Run**
- **Azure Container Instances**
- **Digital Ocean**

### Option 3: Polling Instead of Subscriptions
Instead of REST-hook subscriptions (which require server-initiated callbacks), use **polling**:

```python
# Poll the HAPI server for AuditEvents periodically
import time
import requests

FHIR_BASE = 'https://hapi.fhir.org/baseR4'

def poll_audit_events():
    """Periodically fetch AuditEvents from HAPI"""
    while True:
        response = requests.get(
            f'{FHIR_BASE}/AuditEvent',
            params={'_sort': '-_lastUpdated', '_count': 10}
        )
        if response.status_code == 200:
            events = response.json()
            process_events(events)
        
        time.sleep(5)  # Poll every 5 seconds

def process_events(events):
    """Process fetched events"""
    for entry in events.get('entry', []):
        audit_event = entry.get('resource')
        print(f"Got AuditEvent: {audit_event.get('id')}")
```

### Option 4: Test with a Public Subscription Server
Some alternatives:
- **BLUEBELL FHIR Sandbox**: https://fhirtest.uhn.ca/
- **STU3 Test Server**: May have different restrictions
- Check if they allow subscriptions on test servers

## Recommended Implementation

### Best Practice: Use Local HAPI Server

**Step 1: Start Local HAPI Server**
```bash
# Using Docker (recommended)
docker run -d \
  --name hapi-fhir-server \
  -p 8080:8080 \
  -e hapi.fhir.server.name="Local HAPI" \
  -e hapi.fhir.server.address="http://localhost:8080" \
  hapiproject/hapi:latest

# Or with docker-compose
version: '3'
services:
  hapi-fhir:
    image: hapiproject/hapi:latest
    ports:
      - "8080:8080"
    environment:
      HAPI_FHIR_SERVER_ADDRESS: http://localhost:8080/
```

**Step 2: Register Subscription Locally**
```bash
python register_fhir_subscription.py register http://localhost:8080/fhir/notify
```

**Step 3: Update Your Config**
Update `app/config.py`:
```python
FHIR_SERVER_BASE_URL = 'http://localhost:8080'  # Local server
FHIR_SUBSCRIPTION_ENDPOINT = 'http://YOUR_PUBLIC_IP:5001/fhir/notify'
```

**Step 4: Create Test AuditEvents**
```bash
curl -X POST http://localhost:8080/AuditEvent \
  -H "Content-Type: application/fhir+json" \
  -d @tests/sample_audit.json
```

## Architecture Changes

### Current (Attempted)
```
Your App → Public HAPI Server (subscriptions disabled) ✗
```

### Recommended (Local HAPI)
```
Your App ↔ Local HAPI Server (subscriptions enabled) ✓
```

### Alternative (Polling)
```
Your App → Poll Public HAPI Server → Process Events ✓
```

## Next Steps

1. **If using local HAPI**: Set up Docker and HAPI server
2. **If using polling**: Implement polling loop in `app/server.py`
3. **If using public server**: Contact HAPI admin or find alternative

## Updated Script Usage

The `register_fhir_subscription.py` script works with ANY HAPI server that allows subscriptions:

```bash
# Local HAPI
python register_fhir_subscription.py register http://localhost:8080/fhir/notify AuditEvent

# Custom FHIR server
python register_fhir_subscription.py register http://your-fhir-server.com/fhir/notify

# List subscriptions
python register_fhir_subscription.py list

# Get specific subscription
python register_fhir_subscription.py get {subscription-id}
```

## References

- **HAPI FHIR Official**: http://hapifhir.io/
- **FHIR Subscriptions**: https://www.hl7.org/fhir/subscription.html
- **FHIR Test Servers**: https://confluence.hl7.org/display/FHIR/Public+Test+Servers
- **Docker HAPI**: https://hub.docker.com/r/hapiproject/hapi
