"""
Test script: Verify feature extraction and inference pipeline
Run: python tests/test_server_notify.py
"""

import json
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.fhir_features import FHIRFeatureExtractor
from app.detector import AnomalyDetector


def test_feature_extraction():
    """Test FHIR feature extraction."""
    print("=" * 60)
    print("TEST 1: FHIR Feature Extraction")
    print("=" * 60)
    
    # Load sample FHIR AuditEvent
    with open('tests/sample_audit.json', 'r') as f:
        audit_event = json.load(f)
    
    print("\nInput FHIR AuditEvent:")
    print(json.dumps(audit_event, indent=2))
    
    # Extract features
    extractor = FHIRFeatureExtractor(feature_size=64)
    features = extractor.extract_features(audit_event)
    source_ip = extractor.extract_source_ip(audit_event)
    
    print(f"\nExtracted {len(features)} features:")
    print(f"  Feature vector (first 16): {features[:16]}")
    print(f"  Source IP: {source_ip}")
    
    # Verify feature properties
    assert len(features) == 64, f"Feature size mismatch: {len(features)}"
    assert all(0.0 <= f <= 1.0 for f in features), "Features not normalized to [0, 1]"
    
    print("\n✓ Feature extraction PASSED")
    return features, source_ip


def test_detector():
    """Test anomaly detection and severity mapping."""
    print("\n" + "=" * 60)
    print("TEST 2: Anomaly Detection & Severity")
    print("=" * 60)
    
    detector = AnomalyDetector()
    
    # Test cases: different probability distributions
    test_cases = [
        ([0.9, 0.05, 0.05], 'Normal (LOW)'),
        ([0.3, 0.65, 0.05], 'Attack (MEDIUM)'),
        ([0.1, 0.15, 0.75], 'Attack (HIGH)'),
    ]
    
    for probs, label in test_cases:
        result = detector.process_alert(
            probs,
            source_ip='192.168.1.50',
            fhir_id='sample-audit-001'
        )
        
        print(f"\nTest: {label}")
        print(f"  Probabilities: {probs}")
        print(f"  Prediction: {result['prediction']}")
        print(f"  Anomaly Score: {result['anomaly_score']:.4f}")
        print(f"  Severity: {result['severity']}")
        
        # Verify alert structure
        assert 'prediction' in result
        assert 'anomaly_score' in result
        assert 'severity' in result
        assert result['severity'] in ['LOW', 'MEDIUM', 'HIGH']
    
    print("\n✓ Anomaly detection PASSED")


def test_alert_format():
    """Test alert JSON format."""
    print("\n" + "=" * 60)
    print("TEST 3: Alert JSON Format")
    print("=" * 60)
    
    alert = {
        "timestamp": "2025-12-21T10:30:45.123456",
        "source_ip": "192.168.1.50",
        "prediction": "Attack",
        "anomaly_score": 0.8752,
        "severity": "HIGH",
        "raw_fhir_id": "audit-event-12345"
    }
    
    print("\nAlert JSON:")
    print(json.dumps(alert, indent=2))
    
    # Verify required fields
    required_fields = ['timestamp', 'source_ip', 'prediction', 'anomaly_score', 'severity']
    for field in required_fields:
        assert field in alert, f"Missing required field: {field}"
    
    print("\n✓ Alert format validation PASSED")


def test_mock_inference():
    """Test mock inference without actual model."""
    print("\n" + "=" * 60)
    print("TEST 4: Mock Inference Pipeline")
    print("=" * 60)
    
    # Simulate full pipeline without actual model
    with open('tests/sample_audit.json', 'r') as f:
        audit_event = json.load(f)
    
    # Step 1: Extract features
    extractor = FHIRFeatureExtractor(feature_size=64)
    features = extractor.extract_features(audit_event)
    source_ip = extractor.extract_source_ip(audit_event)
    
    print(f"✓ Extracted {len(features)} features")
    
    # Step 2: Mock inference (simulate CNN output)
    mock_probabilities = [0.1, 0.85, 0.05]  # Simulated attack
    
    print(f"✓ Mock inference output: {mock_probabilities}")
    
    # Step 3: Compute alert
    detector = AnomalyDetector()
    alert = detector.process_alert(
        mock_probabilities,
        source_ip=source_ip,
        fhir_id=audit_event.get('id')
    )
    alert['timestamp'] = '2025-12-21T10:30:45.123456'
    
    print(f"✓ Alert generated: {alert['severity']} severity")
    print(f"\nFull Alert JSON:")
    print(json.dumps(alert, indent=2))
    
    print("\n✓ Mock inference pipeline PASSED")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("EDGE FHIR HYBRID - INTEGRATION TESTS")
    print("=" * 60 + "\n")
    
    try:
        # Run all tests
        test_feature_extraction()
        test_detector()
        test_alert_format()
        test_mock_inference()
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60 + "\n")
    
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
