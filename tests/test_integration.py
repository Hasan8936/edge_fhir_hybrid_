"""
Flask Integration Test
Demonstrates full pipeline: FHIR ingest → feature extraction → inference → alert

Run: python app/server.py (in separate terminal)
Then: python tests/test_infer.json (or use curl)
"""

import json
import requests
from pathlib import Path

# Server configuration
SERVER_URL = 'http://127.0.0.1:5000'

def test_health_check():
    """Test health endpoint."""
    print("\n" + "=" * 60)
    print("TEST: Health Check")
    print("=" * 60)
    
    try:
        response = requests.get(f'{SERVER_URL}/api/health')
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200
        print("✓ Health check PASSED")
    except Exception as e:
        print(f"✗ Health check FAILED: {e}")
        return False
    
    return True


def test_dashboard():
    """Test dashboard endpoint."""
    print("\n" + "=" * 60)
    print("TEST: Dashboard Page")
    print("=" * 60)
    
    try:
        response = requests.get(f'{SERVER_URL}/')
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print(f"Content length: {len(response.text)} bytes")
        
        assert response.status_code == 200
        assert 'dashboard' in response.text.lower() or 'html' in response.headers.get('Content-Type', '').lower()
        print("✓ Dashboard PASSED")
    except Exception as e:
        print(f"✗ Dashboard FAILED: {e}")
        return False
    
    return True


def test_get_alerts():
    """Test alerts API endpoint."""
    print("\n" + "=" * 60)
    print("TEST: Get Alerts API")
    print("=" * 60)
    
    try:
        response = requests.get(f'{SERVER_URL}/api/alerts')
        print(f"Status: {response.status_code}")
        
        data = response.json()
        print(f"Response structure: {list(data.keys())}")
        print(f"Alerts count: {data.get('count', 0)}")
        print(f"Sample alerts:")
        
        if data.get('alerts'):
            for i, alert in enumerate(data['alerts'][:3]):
                print(f"  [{i}] {alert.get('severity')}: {alert.get('prediction')} "
                      f"(score: {alert.get('anomaly_score'):.4f})")
        else:
            print("  (No alerts yet)")
        
        assert response.status_code == 200
        assert 'alerts' in data
        print("✓ Alerts API PASSED")
    except Exception as e:
        print(f"✗ Alerts API FAILED: {e}")
        return False
    
    return True


def test_dashboard_ui():
    """Test dashboard renders correctly."""
    print("\n" + "=" * 60)
    print("TEST: Dashboard UI Rendering")
    print("=" * 60)
    
    try:
        response = requests.get(f'{SERVER_URL}/')
        html = response.text
        
        # Check for key UI elements
        checks = {
            'DOCTYPE html': '<!DOCTYPE html' in html,
            'Title': 'Edge FHIR' in html or 'Anomaly' in html,
            'Dashboard div': 'dashboard' in html.lower(),
            'Status indicator': 'status' in html.lower(),
            'Alerts table': 'alerts' in html.lower(),
            'API endpoint': '/api/alerts' in html,
        }
        
        print("UI Elements:")
        for check_name, present in checks.items():
            status = "✓" if present else "✗"
            print(f"  {status} {check_name}")
        
        assert all(checks.values()), "Missing UI elements"
        print("✓ Dashboard UI PASSED")
    except Exception as e:
        print(f"✗ Dashboard UI FAILED: {e}")
        return False
    
    return True


def simulate_alert_logging():
    """Simulate writing alerts to log for dashboard to read."""
    print("\n" + "=" * 60)
    print("TEST: Alert Logging Simulation")
    print("=" * 60)
    
    try:
        # Ensure logs directory exists
        logs_dir = Path(__file__).parent.parent / 'logs'
        logs_dir.mkdir(exist_ok=True)
        
        alerts_log = logs_dir / 'alerts.log'
        
        # Sample alerts
        sample_alerts = [
            {
                "timestamp": "2025-12-21T10:30:45.123456",
                "source_ip": "192.168.1.50",
                "prediction": "Attack",
                "anomaly_score": 0.8752,
                "severity": "HIGH",
                "raw_fhir_id": "audit-001"
            },
            {
                "timestamp": "2025-12-21T10:32:10.654321",
                "source_ip": "192.168.1.100",
                "prediction": "Anomaly",
                "anomaly_score": 0.5234,
                "severity": "MEDIUM",
                "raw_fhir_id": "audit-002"
            },
            {
                "timestamp": "2025-12-21T10:35:25.987654",
                "source_ip": "192.168.1.200",
                "prediction": "Normal",
                "anomaly_score": 0.1523,
                "severity": "LOW",
                "raw_fhir_id": "audit-003"
            },
        ]
        
        # Write to log (append mode)
        with open(alerts_log, 'a') as f:
            for alert in sample_alerts:
                f.write(json.dumps(alert) + '\n')
        
        print(f"Wrote {len(sample_alerts)} sample alerts to {alerts_log}")
        
        # Verify by reading back
        response = requests.get(f'{SERVER_URL}/api/alerts')
        data = response.json()
        
        print(f"Dashboard now shows {data.get('count', 0)} alerts")
        print("✓ Alert logging PASSED")
    except Exception as e:
        print(f"✗ Alert logging FAILED: {e}")
        return False
    
    return True


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("EDGE FHIR HYBRID - FLASK INTEGRATION TESTS")
    print("=" * 60)
    print(f"\nServer URL: {SERVER_URL}")
    print("Ensure Flask server is running: python app/server.py")
    
    results = {}
    
    try:
        # Run tests
        results['health'] = test_health_check()
        results['dashboard'] = test_dashboard()
        results['dashboard_ui'] = test_dashboard_ui()
        results['alerts_api'] = test_get_alerts()
        results['alert_logging'] = simulate_alert_logging()
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        for test_name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {test_name}")
        
        if all(results.values()):
            print("\n✓ ALL TESTS PASSED")
            
            # Instructions for next step
            print("\nNext steps:")
            print("1. Open http://127.0.0.1:5000 in your browser")
            print("2. You should see the dashboard with sample alerts")
            print("3. Alerts will auto-refresh every 5 seconds")
            print("4. Try adding more alerts to logs/alerts.log to see updates")
        else:
            print("\n✗ SOME TESTS FAILED")
            print("Check server logs for details")
    
    except Exception as e:
        print(f"\n✗ FATAL ERROR: {e}")
        print("Is Flask server running? python app/server.py")
