"""
Detector Module - Anomaly Detection Logic
Combines CNN inference score with severity thresholds.
"""

class AnomalyDetector:
    """
    Maps CNN inference output (anomaly score: 0.0 - 1.0) to severity levels.
    
    Severity Mapping:
    - LOW:    anomaly_score < 0.4
    - MEDIUM: 0.4 <= anomaly_score < 0.7
    - HIGH:   anomaly_score >= 0.7
    """
    
    def __init__(
        self,
        low_threshold=0.4,
        medium_threshold=0.7,
        class_labels=None
    ):
        """
        Args:
            low_threshold: Boundary below which severity is LOW
            medium_threshold: Boundary above which severity is HIGH
            class_labels: Optional dict mapping class indices to readable names
        """
        self.low_threshold = low_threshold
        self.medium_threshold = medium_threshold
        self.class_labels = class_labels or {
            0: 'Normal',
            1: 'Attack',
            2: 'Anomaly'
        }
    
    def compute_severity(self, anomaly_score):
        """
        Map anomaly score to severity level.
        
        Args:
            anomaly_score: float in [0.0, 1.0]
        
        Returns:
            str: 'LOW', 'MEDIUM', or 'HIGH'
        """
        if anomaly_score < self.low_threshold:
            return 'LOW'
        elif anomaly_score < self.medium_threshold:
            return 'MEDIUM'
        else:
            return 'HIGH'
    
    def get_prediction_label(self, class_index):
        """
        Map class index to readable label.
        
        Args:
            class_index: int (output from CNN argmax)
        
        Returns:
            str: Readable class name
        """
        return self.class_labels.get(class_index, f'Class_{class_index}')
    
    def process_alert(self, probabilities, source_ip, fhir_id=None):
        """
        Full alert processing: probabilities -> prediction + anomaly_score + severity.
        
        Args:
            probabilities: list of floats (CNN output logits or softmax)
            source_ip: str (IP address from FHIR AuditEvent)
            fhir_id: str (optional FHIR resource ID for traceability)
        
        Returns:
            dict: {
                'prediction': 'Normal' | 'Attack' | ...,
                'anomaly_score': float,
                'severity': 'LOW' | 'MEDIUM' | 'HIGH',
                'source_ip': str,
                'raw_fhir_id': str or None
            }
        """
        # Get class with highest probability
        predicted_class = max(range(len(probabilities)), key=lambda i: probabilities[i])
        anomaly_score = max(probabilities)
        
        prediction_label = self.get_prediction_label(predicted_class)
        severity = self.compute_severity(anomaly_score)
        
        return {
            'prediction': prediction_label,
            'anomaly_score': float(anomaly_score),
            'severity': severity,
            'source_ip': source_ip,
            'raw_fhir_id': fhir_id
        }
