"""Test different subscription criteria formats"""
import requests
import json

endpoint = "https://missy-unaggravated-dandiacally.ngrok-free.dev:5001/fhir/notify"

# Test different criteria formats
criteria_options = [
    "AuditEvent?entity-type=2",  # With parameters
    "AuditEvent?",  # With trailing ?
    "Observation",
    "Encounter",
    "Patient?active=true",
    "MedicationRequest",
    "Observation?status=final",
]

url = 'https://hapi.fhir.org/baseR4/Subscription'
headers = {
    'Content-Type': 'application/fhir+json',
    'Accept': 'application/fhir+json'
}

for criteria in criteria_options:
    subscription = {
        "resourceType": "Subscription",
        "status": "active",
        "criteria": criteria,
        "channel": {
            "type": "rest-hook",
            "endpoint": endpoint,
            "payload": "application/fhir+json"
        }
    }
    
    print(f"\n{'='*60}")
    print(f"Testing criteria: {criteria}")
    print(f"{'='*60}")
    
    try:
        response = requests.post(url, json=subscription, headers=headers, timeout=10)
        
        if response.status_code == 201 or response.status_code == 200:
            print(f"✓ SUCCESS! HTTP {response.status_code}")
            result = response.json()
            print(f"  Subscription ID: {result.get('id')}")
        else:
            print(f"✗ FAILED! HTTP {response.status_code}")
            try:
                error = response.json()
                diag = error.get('issue', [{}])[0].get('diagnostics', 'No error message')
                print(f"  Error: {diag}")
            except:
                print(f"  Response: {response.text[:200]}")
    
    except Exception as e:
        print(f"✗ Exception: {e}")
