"""
Edge Model Module - CNN Inference Wrapper
Wraps ONNX Runtime (Windows) and TensorRT (Jetson Nano) inference.
"""

import numpy as np
from typing import List, Tuple
import os


class EdgeCNNModel:
    """
    CNN inference wrapper for anomaly detection.
    Supports ONNX Runtime (CPU, Windows/Linux) and TensorRT (Jetson Nano).
    """
    
    def __init__(self, model_path: str, runtime='onnx'):
        """
        Args:
            model_path: Path to ONNX (.onnx) or TensorRT (.engine) model
            runtime: 'onnx' or 'tensorrt'
        
        Raises:
            FileNotFoundError: If model file doesn't exist
            RuntimeError: If inference runtime not available
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found: {model_path}")
        
        self.model_path = model_path
        self.runtime = runtime
        self.session = None
        self.input_shape = None
        self.output_shape = None
        
        if runtime == 'onnx':
            self._init_onnx()
        elif runtime == 'tensorrt':
            self._init_tensorrt()
        else:
            raise ValueError(f"Unknown runtime: {runtime}")
    
    def _init_onnx(self):
        """Initialize ONNX Runtime session."""
        try:
            import onnxruntime as rt
        except ImportError:
            raise RuntimeError("onnxruntime not installed. Install with: pip install onnxruntime")
        
        try:
            # Use CPU providers only (no GPU)
            self.session = rt.InferenceSession(
                self.model_path,
                providers=['CPUExecutionProvider']
            )
            
            # Get input/output shapes
            input_info = self.session.get_inputs()[0]
            output_info = self.session.get_outputs()[0]
            
            self.input_shape = input_info.shape
            self.output_shape = output_info.shape
            
            print(f"ONNX model loaded: {self.model_path}")
            print(f"  Input shape: {self.input_shape}")
            print(f"  Output shape: {self.output_shape}")
        
        except Exception as e:
            raise RuntimeError(f"Failed to load ONNX model: {e}")
    
    def _init_tensorrt(self):
        """Initialize TensorRT engine (Jetson Nano only)."""
        try:
            import tensorrt as trt
            import pycuda.driver as cuda
            import pycuda.autoinit
        except ImportError:
            raise RuntimeError(
                "tensorrt or pycuda not installed. "
                "On Jetson: pip install tensorrt pycuda"
            )
        
        try:
            # Load TensorRT engine
            logger = trt.Logger(trt.Logger.WARNING)
            
            with open(self.model_path, 'rb') as f:
                engine = trt.Runtime(logger).deserialize_cuda_engine(f.read())
            
            self.session = engine.create_execution_context()
            
            print(f"TensorRT engine loaded: {self.model_path}")
        
        except Exception as e:
            raise RuntimeError(f"Failed to load TensorRT engine: {e}")
    
    def infer(self, feature_vector: List[float]) -> np.ndarray:
        """
        Run inference on feature vector.
        
        Args:
            feature_vector: list or np.ndarray of floats
        
        Returns:
            np.ndarray: Output logits/probabilities (shape = output_shape)
        
        Raises:
            ValueError: If input shape doesn't match model expectations
        """
        # Convert to numpy and reshape
        input_data = np.array(feature_vector, dtype=np.float32)
        
        # Reshape if needed (typically: [1, feature_size] for batch inference)
        if self.runtime == 'onnx':
            # ONNX Runtime expects dict input
            input_name = self.session.get_inputs()[0].name
            
            # Flatten and reshape to match model input
            if input_data.ndim == 1:
                input_data = input_data.reshape(1, -1)
            
            output = self.session.run(None, {input_name: input_data})
            
            # Typically output is list with one array
            return np.array(output[0] if isinstance(output, list) else output)
        
        elif self.runtime == 'tensorrt':
            # TensorRT inference (simplified; actual implementation depends on engine)
            # This is a placeholder; real implementation requires CUDA/GPU handling
            raise NotImplementedError(
                "TensorRT inference requires CUDA setup. "
                "Implement with pycuda bindings on Jetson Nano."
            )
    
    def infer_batch(self, feature_vectors: List[List[float]]) -> np.ndarray:
        """
        Run inference on batch of feature vectors.
        
        Args:
            feature_vectors: list of lists/arrays
        
        Returns:
            np.ndarray: Batch predictions
        """
        batch_data = np.array(feature_vectors, dtype=np.float32)
        
        if self.runtime == 'onnx':
            input_name = self.session.get_inputs()[0].name
            output = self.session.run(None, {input_name: batch_data})
            return np.array(output[0] if isinstance(output, list) else output)
        
        else:
            raise NotImplementedError("Batch inference not yet implemented for TensorRT")
    
    def get_input_size(self) -> int:
        """Return expected input feature vector size."""
        if self.input_shape and len(self.input_shape) > 1:
            return self.input_shape[1]
        return None
    
    def get_output_size(self) -> int:
        """Return output class count (typically 2 or 3)."""
        if self.output_shape and len(self.output_shape) > 1:
            return self.output_shape[1]
        return None
