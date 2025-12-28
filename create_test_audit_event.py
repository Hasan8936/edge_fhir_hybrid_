#!/usr/bin/env python3
"""
Create a test AuditEvent in HAPI FHIR server to trigger polling
"""

import requests
import json
from datetime import datetime

FHIR_BASE = 'https://hapi.fhir.org/baseR4'

# Create a test AuditEvent
test_audit_event = {
    "resourceType": "AuditEvent",
    "type": {
        "system": "http://terminology.hl7.org/CodeSystem/audit-event-type",
        "code": "rest",
        "display": "RESTful Operation"
    },
    "subtype": [
        {
            "system": "http://hl7.org/fhir/restful-interaction",
            "code": "create",
            "display": "Create"
        }
    ],
    "action": "C",
    "recorded": datetime.utcnow().isoformat() + "Z",
    "outcome": "0",
    "outcomeDesc": "Success",
    "agent": [
        {
            "type": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                        "code": "HUM",
                        "display": "human user"
                    }
                ]
            },
            "name": "Test User",
            "requestor": True
        }
    ],
    "source": {
        "site": "TestLab",
        "identifier": {
            "value": "192.168.1.100"
        },
        "type": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/security-source-type",
                "code": "4",
                "display": "Application Server"
            }
        ]
    },
    "entity": [
        {
            "type": {
                "system": "http://terminology.hl7.org/CodeSystem/audit-entity-type",
                "code": "2",
                "display": "System Object"
            },
            "role": {
                "system": "http://terminology.hl7.org/CodeSystem/object-role",
                "code": "1",
                "display": "Patient"
            },
            "lifecycle": {
                "system": "http://terminology.hl7.org/CodeSystem/object-lifecycle-events",
                "code": "1",
                "display": "Creation"
            },
            "name": "TestPatient"
        }
    ]
}

print("Creating test AuditEvent in HAPI FHIR server...")
print(f"Server: {FHIR_BASE}\n")

try:
    response = requests.post(
        f"{FHIR_BASE}/AuditEvent",
        json=test_audit_event,
        headers={'Content-Type': 'application/fhir+json'},
        timeout=10
    )
    
    if response.status_code in [200, 201]:
        result = response.json()
        event_id = result.get('id', 'unknown')
        print(f"✓ AuditEvent created successfully!")
        print(f"  ID: {event_id}")
        print(f"  Status: {response.status_code}")
        print(f"\nNow run polling test to fetch this event:")
        print(f"  python test_polling.py")
    else:
        print(f"✗ Failed to create AuditEvent (HTTP {response.status_code})")
        print(f"  Response: {response.text}")

except Exception as e:
    print(f"✗ Error: {e}")
