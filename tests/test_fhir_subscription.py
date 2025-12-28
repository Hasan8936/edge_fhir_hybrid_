"""
Test Script for FHIR Subscription Server API
Tests the Flask server endpoints with FHIR AuditEvent data
"""

import requests
import json
from datetime import datetime, timedelta
import time

# Server configuration
SERVER_URL = "http://127.0.0.1:5000"
FHIR_SUBSCRIPTION_URL = f"{SERVER_URL}/api/alerts"
HEALTH_CHECK_URL = f"{SERVER_URL}/api/health"
DASHBOARD_URL = f"{SERVER_URL}/"

# Sample FHIR AuditEvent for subscription testing
SAMPLE_FHIR_AUDIT_EVENT = {
    "resourceType": "AuditEvent",
    "id": "audit-event-test-001",
    "type": {
        "code": "110100",
        "display": "Application Activity"
    },
    "action": "R",
    "outcome": "0",
    "recorded": datetime.utcnow().isoformat() + "Z",
    "source": {
        "observer": {
            "display": "EHR-Server-01"
        }
    },
    "agent": [{
        "network": {
            "address": "192.168.1.100",
            "type": "2"
        },
        "name": "healthcare_worker_01"
    }]
}

# Alert data matching the server's alert format
SAMPLE_ALERT = {
    "timestamp": datetime.utcnow().isoformat(),
    "source_ip": "192.168.1.100",
    "prediction": "Anomaly",
    "anomaly_score": 0.8752,
    "severity": "HIGH",
    "raw_fhir_id": "audit-event-test-001"
}


def test_health_check():
    """Test the health check endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check Endpoint")
    print("="*60)
    try:
        response = requests.get(HEALTH_CHECK_URL, timeout=5)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("✓ Health check passed")
            return True
        else:
            print("✗ Health check failed")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_dashboard_access():
    """Test dashboard endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Dashboard Access")
    print("="*60)
    try:
        response = requests.get(DASHBOARD_URL, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✓ Dashboard loaded successfully ({len(response.text)} bytes)")
            return True
        else:
            print("✗ Dashboard failed to load")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_alerts_endpoint():
    """Test the alerts/subscription endpoint"""
    print("\n" + "="*60)
    print("TEST 3: FHIR Subscription/Alerts Endpoint")
    print("="*60)
    try:
        response = requests.get(FHIR_SUBSCRIPTION_URL, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            alerts_count = data.get('count', 0)
            print(f"✓ Alerts endpoint working (found {alerts_count} alerts)")
            return True
        else:
            print("✗ Alerts endpoint failed")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_fhir_audit_event_structure():
    """Test FHIR AuditEvent data structure"""
    print("\n" + "="*60)
    print("TEST 4: FHIR AuditEvent Structure Validation")
    print("="*60)
    try:
        print("Sample FHIR AuditEvent:")
        print(json.dumps(SAMPLE_FHIR_AUDIT_EVENT, indent=2))
        
        # Validate required fields
        required_fields = ["resourceType", "id", "type", "action", "recorded", "source", "agent"]
        missing_fields = [field for field in required_fields if field not in SAMPLE_FHIR_AUDIT_EVENT]
        
        if missing_fields:
            print(f"✗ Missing required fields: {missing_fields}")
            return False
        else:
            print("✓ All required FHIR AuditEvent fields present")
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_alert_data_structure():
    """Test alert data structure"""
    print("\n" + "="*60)
    print("TEST 5: Alert Data Structure Validation")
    print("="*60)
    try:
        print("Sample Alert:")
        print(json.dumps(SAMPLE_ALERT, indent=2))
        
        # Validate required fields
        required_fields = ["timestamp", "source_ip", "prediction", "anomaly_score", "severity", "raw_fhir_id"]
        missing_fields = [field for field in required_fields if field not in SAMPLE_ALERT]
        
        if missing_fields:
            print(f"✗ Missing required fields: {missing_fields}")
            return False
        else:
            print("✓ All required alert fields present")
            return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_subscription_response_format():
    """Test that subscription response has correct format"""
    print("\n" + "="*60)
    print("TEST 6: Subscription Response Format")
    print("="*60)
    try:
        response = requests.get(FHIR_SUBSCRIPTION_URL, timeout=5)
        
        if response.status_code != 200:
            print("✗ Failed to get alerts")
            return False
        
        data = response.json()
        
        # Validate response structure
        required_keys = ["alerts", "count", "timestamp"]
        missing_keys = [key for key in required_keys if key not in data]
        
        if missing_keys:
            print(f"✗ Missing response keys: {missing_keys}")
            return False
        
        print(f"✓ Response format valid")
        print(f"  - alerts: {type(data['alerts']).__name__} with {len(data['alerts'])} items")
        print(f"  - count: {data['count']}")
        print(f"  - timestamp: {data['timestamp']}")
        
        # Check if alerts array has correct structure
        if data['alerts'] and len(data['alerts']) > 0:
            first_alert = data['alerts'][0]
            print(f"\nFirst alert structure:")
            print(json.dumps(first_alert, indent=2))
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("FHIR SUBSCRIPTION SERVER API TEST SUITE")
    print("="*60)
    print(f"Server URL: {SERVER_URL}")
    print(f"Test Start Time: {datetime.now().isoformat()}")
    
    # Wait for server to be ready
    print("\nWaiting for server to be ready...")
    max_retries = 5
    for i in range(max_retries):
        try:
            requests.get(HEALTH_CHECK_URL, timeout=2)
            print("✓ Server is ready")
            break
        except:
            if i < max_retries - 1:
                print(f"  Retry {i+1}/{max_retries-1}...")
                time.sleep(1)
            else:
                print("✗ Server not responding")
                return
    
    # Run tests
    results = {
        "Health Check": test_health_check(),
        "Dashboard Access": test_dashboard_access(),
        "Alerts Endpoint": test_alerts_endpoint(),
        "FHIR AuditEvent Structure": test_fhir_audit_event_structure(),
        "Alert Data Structure": test_alert_data_structure(),
        "Subscription Response Format": test_subscription_response_format(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Test End Time: {datetime.now().isoformat()}")
    
    if passed == total:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {total - passed} test(s) failed")


if __name__ == '__main__':
    run_all_tests()
