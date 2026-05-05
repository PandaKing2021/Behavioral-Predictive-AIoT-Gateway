"""Prediction module configuration file.

Defines constants for model paths, inference parameters, scene thresholds, etc.
"""

# Model file paths
EDGE_MODEL_PATH = "models/edge_1dcnn_lstm.onnx"
SENTINEL_MODEL_PATH = "models/sentinel_lstm.onnx"

# Data collection configuration
DATA_COLLECTION_WINDOW_HOURS = 168  # Cache the last 7 days of data
DATA_PULL_INTERVAL = 300  # Data pull interval (seconds)
MIN_DATA_SAMPLES = 100  # Minimum data samples required

# Data preprocessing configuration
SEQUENCE_LENGTH = 10  # Input sequence length
FEATURE_COLUMNS = [
    "temperature",
    "humidity",
    "brightness",
    "light_th",
    "light_cu",
    "curtain_status",
:]
FEATURE_DIM = len(FEATURE_COLUMNS)  # Feature dimension

# Normalization parameters
NORMALIZATION_METHOD = "minmax"  # minmax or standard

# Inference engine configuration
SENTINEL_THRESHOLD = 0.9  # Sentinel confidence threshold
BATCH_SIZE = 1  # Batch inference size
INFERENCE_TIMEOUT = 5.0  # Inference timeout (seconds)

# Scene trigger thresholds
SCENE_TRIGGER_THRESHOLD = 0.7  # Prediction probability trigger threshold
SCENE_COOLDOWN_TIME = 60  # Scene trigger cooldown time (seconds)

# Performance monitoring
ENABLE_PERF_MONITORING = True
LOG_INFERENCE_STATS = True

# Degradation strategy
FALLBACK_TO_THRESHOLD = True  # Degrade to threshold decision when model fails
MAX_RETRY_ATTEMPTS = 3  # Maximum retry attempts
