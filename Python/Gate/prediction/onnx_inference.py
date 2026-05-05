"""ONNX inference engine module.

Responsible for loading ONNX models and executing inference,
supporting the edge-cloud collaborative sentinel framework.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np
import onnxruntime as ort

logger = logging.getLogger(__name__)


class ONNXModelInference:
    """ONNX model inference engine.

    Supports single-model inference and edge-cloud collaborative inference
    (sentinel model + full model).

    Attributes:
        edge_session: Edge model ONNX Runtime session.
        sentinel_session: Sentinel model ONNX Runtime session (optional).
        threshold: Sentinel confidence threshold.
        enable_sentinel: Whether to enable the sentinel framework.
        stats: Inference statistics.
    """

    def __init__(
        self,
        edge_model_path: str,
        sentinel_model_path: Optional[str] = None,
        threshold: float = 0.9
    ):
        """Initialize the ONNX inference engine.

        Args:
            edge_model_path: Path to the edge model ONNX file.
            sentinel_model_path: Path to the sentinel model ONNX file (optional).
            threshold: Sentinel confidence threshold, default 0.9.
        """
        self.threshold = threshold
        self.enable_sentinel = False
        self.edge_session: Optional[ort.InferenceSession] = None
        self.sentinel_session: Optional[ort.InferenceSession] = None
        self.stats = {
            "total_inferences": 0,
            "sentinel_only": 0,
            "edge_called": 0,
            "total_latency_ms": 0.0,
            "sentinel_latency_ms": 0.0,
            "edge_latency_ms": 0.0,
        }

        # Load edge model
        if not Path(edge_model_path).exists():
            raise FileNotFoundError(f"Edge model file not found: {edge_model_path}")

        self.edge_session = ort.InferenceSession(edge_model_path)
        logger.info("Edge model loaded successfully: %s", edge_model_path)
        logger.info(
            "  Input: %s, Shape: %s",
            self.edge_session.get_inputs()[0].name,
            self.edge_session.get_inputs()[0].shape
        )
        logger.info(
            "  Output: %s, Shape: %s",
            self.edge_session.get_outputs()[0].name,
            self.edge_session.get_outputs()[0].shape
        )

        # Load sentinel model
        if sentinel_model_path and Path(sentinel_model_path).exists():
            self.sentinel_session = ort.InferenceSession(sentinel_model_path)
            self.enable_sentinel = True
            logger.info("Sentinel model loaded successfully: %s", sentinel_model_path)
            logger.info("  Confidence threshold: %.2f", threshold)
        else:
            logger.info("Sentinel model not enabled, using edge model only")

    def predict(
        self,
        input_data: np.ndarray,
        return_stats: bool = False
    ) -> Tuple[np.ndarray, Optional[Dict]]:
        """Execute inference.

        If the sentinel framework is enabled, uses the sentinel model for
        fast inference first; low-confidence samples are re-evaluated by the edge model.

        Args:
            input_data: Input data, shape=(batch, seq_length, features).
            return_stats: Whether to return inference statistics.

        Returns:
            (Prediction results, Statistics) tuple.
            Prediction results shape=(batch, 1), range [0, 1].
        """
        if self.enable_sentinel and self.sentinel_session is not None:
            return self._predict_with_sentinel(input_data, return_stats)
        else:
            return self._predict_edge_only(input_data, return_stats)

    def _predict_edge_only(
        self,
        input_data: np.ndarray,
        return_stats: bool = False
    ) -> Tuple[np.ndarray, Optional[Dict]]:
        """Inference using only the edge model.

        Args:
            input_data: Input data.
            return_stats: Whether to return statistics.

        Returns:
            (Prediction results, Statistics) tuple.
        """
        start_time = time.perf_counter()

        # Execute inference
        input_name = self.edge_session.get_inputs()[0].name
        outputs = self.edge_session.run(None, {input_name: input_data})
        predictions = outputs[0]

        latency_ms = (time.perf_counter() - start_time) * 1000

        # Update statistics
        self.stats["total_inferences"] += 1
        self.stats["edge_called"] += 1
        self.stats["total_latency_ms"] += latency_ms
        self.stats["edge_latency_ms"] += latency_ms

        if return_stats:
            stats = {
                "latency_ms": latency_ms,
                "model_used": "edge",
                "batch_size": input_data.shape[0],
            }
            return predictions, stats

        return predictions, None

    def _predict_with_sentinel(
        self,
        input_data: np.ndarray,
        return_stats: bool = False
    ) -> Tuple[np.ndarray, Optional[Dict]]:
        """Inference using the edge-cloud collaborative framework.

        Sentinel model performs fast initial screening;
        low-confidence samples are processed by the edge model.

        Args:
            input_data: Input data.
            return_stats: Whether to return statistics.

        Returns:
            (Prediction results, Statistics) tuple.
        """
        batch_size = input_data.shape[0]

        # Sentinel model inference
        start_time = time.perf_counter()
        sentinel_input_name = self.sentinel_session.get_inputs()[0].name
        sentinel_outputs = self.sentinel_session.run(
            None, {sentinel_input_name: input_data}
        )
        sentinel_predictions = sentinel_outputs[0].flatten()
        sentinel_latency_ms = (time.perf_counter() - start_time) * 1000

        # Calculate confidence
        confidence = np.abs(sentinel_predictions - 0.5) * 2  # Normalize to [0, 1]
        high_conf_mask = confidence >= self.threshold
        low_conf_mask = ~high_conf_mask

        # Initialize results
        final_predictions = sentinel_predictions.copy()

        # Low-confidence samples use edge model
        edge_latency_ms = 0.0
        if low_conf_mask.any():
            start_time = time.perf_counter()
            edge_input_name = self.edge_session.get_inputs()[0].name
            edge_outputs = self.edge_session.run(
                None, {edge_input_name: input_data[low_conf_mask]}
            )
            edge_predictions = edge_outputs[0].flatten()
            edge_latency_ms = (time.perf_counter() - start_time) * 1000

            # Merge results
            final_predictions[low_conf_mask] = edge_predictions

        total_latency_ms = sentinel_latency_ms + edge_latency_ms

        # Update statistics
        self.stats["total_inferences"] += batch_size
        self.stats["sentinel_only"] += high_conf_mask.sum()
        self.stats["edge_called"] += low_conf_mask.sum()
        self.stats["total_latency_ms"] += total_latency_ms
        self.stats["sentinel_latency_ms"] += sentinel_latency_ms
        self.stats["edge_latency_ms"] += edge_latency_ms

        # Return results
        final_predictions = final_predictions.reshape(-1, 1)

        if return_stats:
            stats = {
                "total_latency_ms": total_latency_ms,
                "sentinel_latency_ms": sentinel_latency_ms,
                "edge_latency_ms": edge_latency_ms,
                "high_confidence_count": high_conf_mask.sum(),
                "low_confidence_count": low_conf_mask.sum(),
                "wake_rate": low_conf_mask.sum() / batch_size,
                "avg_confidence": confidence.mean(),
            }
            return final_predictions, stats

        return final_predictions, None

    def get_stats(self) -> Dict:
        """Get inference statistics.

        Returns:
            Statistics dictionary containing total inferences,
            wake rate, average latency, etc.
        """
        stats = self.stats.copy()

        if stats["total_inferences"] > 0:
            stats["avg_latency_ms"] = (
                stats["total_latency_ms"] / stats["total_inferences"]
            )
            stats["wake_rate"] = (
                stats["edge_called"] / stats["total_inferences"]
                if self.enable_sentinel
                else 1.0
            )

            if self.enable_sentinel:
                stats["avg_sentinel_latency_ms"] = (
                    stats["sentinel_latency_ms"] / stats["total_inferences"]
                )
                stats["avg_edge_latency_ms"] = (
                    stats["edge_latency_ms"] / stats["total_inferences"]
                )

        return stats

    def reset_stats(self) -> None:
        """Reset statistics."""
        self.stats = {
            "total_inferences": 0,
            "sentinel_only": 0,
            "edge_called": 0,
            "total_latency_ms": 0.0,
            "sentinel_latency_ms": 0.0,
            "edge_latency_ms": 0.0,
        }
        logger.info("Inference statistics have been reset")

    def warmup(self, input_shape: Tuple[int, int, int] = (1, 10, 6)) -> None:
        """Warm up the model.

        Performs several inference runs to warm up the model,
        optimizing inference speed.

        Args:
            input_shape: Shape of the warmup input.
        """
        logger.info("Starting model warmup...")
        dummy_input = np.random.randn(*input_shape).astype(np.float32)

        # Warm up sentinel model
        if self.enable_sentinel and self.sentinel_session is not None:
            for _ in range(5):
                input_name = self.sentinel_session.get_inputs()[0].name
                self.sentinel_session.run(None, {input_name: dummy_input})

        # Warm up edge model
        for _ in range(5):
            input_name = self.edge_session.get_inputs()[0].name
            self.edge_session.run(None, {input_name: dummy_input})

        logger.info("Model warmup complete")

    def get_model_info(self) -> Dict:
        """Get model information.

        Returns:
            Dictionary containing model information.
        """
        info = {
            "edge_model": {
                "input_shape": self.edge_session.get_inputs()[0].shape,
                "output_shape": self.edge_session.get_outputs()[0].shape,
            },
            "sentinel_enabled": self.enable_sentinel,
            "threshold": self.threshold,
        }

        if self.enable_sentinel and self.sentinel_session is not None:
            info["sentinel_model"] = {
                "input_shape": self.sentinel_session.get_inputs()[0].shape,
                "output_shape": self.sentinel_session.get_outputs()[0].shape,
            }

        return info

    def close(self) -> None:
        """Close inference sessions and release resources."""
        if self.edge_session is not None:
            del self.edge_session
            self.edge_session = None

        if self.sentinel_session is not None:
            del self.sentinel_session
            self.sentinel_session = None

        logger.info("ONNX inference engine has been closed")
