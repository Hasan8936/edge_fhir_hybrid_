"""
FHIR Features Module - Extract features from FHIR AuditEvent JSON
Converts FHIR AuditEvent to numeric feature vector for CNN inference.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Any


class FHIRFeatureExtractor:
    """
    Extracts and encodes features from FHIR AuditEvent resources.
    
    FHIR Fields Used:
    - AuditEvent.type.code (categorical)
    - AuditEvent.action (categorical)
    - AuditEvent.outcome (categorical)
    - AuditEvent.recorded (timestamp)
    - AuditEvent.source.observer.display (categorical)
    - AuditEvent.agent.network.address (IP address)
    
    Output: Numeric feature vector (list of floats)
    """
    
    def __init__(self, feature_size=64):
        """
        Args:
            feature_size: Expected input size for CNN model
        """
        self.feature_size = feature_size
        self.feature_names = [
            'event_type_encoded',
            'action_encoded',
            'outcome_encoded',
            'source_encoded',
            'time_hour',
            'time_minute',
            'time_second',
            'ip_hash_1',
            'ip_hash_2',
            'ip_hash_3',
            'ip_hash_4',
        ]
    
    def safe_get(self, obj: Dict, path: str, default: Any = None) -> Any:
        """
        Safely navigate nested dict using dot notation.
        E.g., 'agent.0.network.address' -> obj['agent'][0]['network']['address']
        """
        if obj is None:
            return default
        
        keys = path.split('.')
        current = obj
        
        for key in keys:
            if isinstance(current, list):
                try:
                    current = current[int(key)]
                except (ValueError, IndexError):
                    return default
            elif isinstance(current, dict):
                current = current.get(key)
            else:
                return default
        
        return current if current is not None else default
    
    def encode_categorical(self, value: str, max_code: int = 10) -> float:
        """
        Encode categorical value as integer hash.
        Uses first character hash to keep it lightweight.
        """
        if value is None or value == '':
            return 0.0
        
        hash_val = sum(ord(c) for c in str(value)) % max_code
        return float(hash_val) / max_code
    
    def encode_ip_address(self, ip: str) -> Tuple[float, float, float, float]:
        """
        Encode IP address as 4 numeric features.
        Converts dotted notation to numeric octets.
        """
        default = (0.0, 0.0, 0.0, 0.0)
        
        if not ip or not isinstance(ip, str):
            return default
        
        try:
            octets = ip.split('.')
            if len(octets) != 4:
                return default
            
            # Normalize each octet to [0, 1]
            return tuple(float(int(o)) / 255.0 for o in octets)
        except (ValueError, AttributeError):
            return default
    
    def extract_timestamp_features(self, timestamp_str: str) -> Tuple[float, float, float]:
        """
        Extract hour, minute, second from ISO-8601 timestamp.
        Normalize to [0, 1] range.
        """
        default = (0.0, 0.0, 0.0)
        
        if not timestamp_str:
            return default
        
        try:
            # Support both ISO-8601 with and without 'Z'
            ts_str = timestamp_str.replace('Z', '+00:00')
            dt = datetime.fromisoformat(ts_str)
            
            hour = dt.hour / 24.0
            minute = dt.minute / 60.0
            second = dt.second / 60.0
            
            return (hour, minute, second)
        except (ValueError, AttributeError):
            return default
    
    def extract_features(self, audit_event: Dict) -> List[float]:
        """
        Extract feature vector from FHIR AuditEvent.
        
        Args:
            audit_event: dict representing FHIR AuditEvent resource
        
        Returns:
            list of floats (length = feature_size, padded with 0.0 if needed)
        
        Never raises exception; uses safe defaults for missing fields.
        """
        features = []
        
        # 1. Event type (categorical)
        event_type = self.safe_get(audit_event, 'type.code', 'UNKNOWN')
        features.append(self.encode_categorical(event_type))
        
        # 2. Action (categorical)
        action = self.safe_get(audit_event, 'action', 'UNKNOWN')
        features.append(self.encode_categorical(action))
        
        # 3. Outcome (categorical)
        outcome = self.safe_get(audit_event, 'outcome', 'UNKNOWN')
        features.append(self.encode_categorical(outcome))
        
        # 4. Source observer (categorical)
        source = self.safe_get(audit_event, 'source.observer.display', 'UNKNOWN')
        features.append(self.encode_categorical(source))
        
        # 5-7. Timestamp features
        timestamp = self.safe_get(audit_event, 'recorded', '')
        hour, minute, second = self.extract_timestamp_features(timestamp)
        features.extend([hour, minute, second])
        
        # 8-11. IP address features
        ip_addr = self.safe_get(audit_event, 'agent.0.network.address', '0.0.0.0')
        ip_features = self.encode_ip_address(ip_addr)
        features.extend(ip_features)
        
        # Pad with zeros to reach feature_size
        while len(features) < self.feature_size:
            features.append(0.0)
        
        # Truncate if over-length (should not happen with this design)
        return features[:self.feature_size]
    
    def extract_source_ip(self, audit_event: Dict) -> str:
        """
        Extract source IP from AuditEvent for logging/display.
        """
        ip = self.safe_get(audit_event, 'agent.0.network.address', 'UNKNOWN')
        return str(ip)
