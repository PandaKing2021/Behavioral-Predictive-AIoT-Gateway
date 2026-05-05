"""Prediction module configuration file (multi-activity version).

Defines constants for model paths, inference parameters, scene thresholds, etc.
Supports multi-class classification with 8 activity categories.

Activity categories:
1. Sleep
2. Work_On_Computer
3. Watch_TV
4. Cook_Dinner
5. Read_Book
6. Leave_Home
7. Exercise
8. Relax
"""

# Model file paths
EDGE_MODEL_PATH = "models/edge_1dcnn_lstm_multi.onnx"
SENTINEL_MODEL_PATH = "models/sentinel_lstm.onnx"

# Activity category definitions
ACTIVITY_CLASSES = [
    "Sleep",
    "Work_On_Computer",
    "Watch_TV",
    "Cook_Dinner",
    "Read_Book",
    "Leave_Home",
    "Exercise",
    "Relax"
]

NUM_CLASSES = len(ACTIVITY_CLASSES)

# Activity to device state mapping
ACTIVITY_DEVICE_MAPPING = {
    "Sleep": {
        "light_th": 0,      # AC off
        "light_cu": 0,      # Lights off
        "curtain_status": 0 # Curtains closed
    },
    "Work_On_Computer": {
        "light_th": 0,
        "light_cu": 1,      # Lights on
        "curtain_status": 1 # Curtains open
    },
    "Watch_TV": {
        "light_th": 0,
        "light_cu": 1,
        "curtain_status": 0
    },
    "Cook_Dinner": {
        "light_th": 1,      # AC may be on
        "light_cu": 1,
        "curtain_status": 1
    },
    "Read_Book": {
        "light_th": 0,
        "light_cu": 1,
        "curtain_status": 1
    },
    "Leave_Home": {
        "light_th": 0,
        "light_cu": 0,
        "curtain_status": 0
    },
    "Exercise": {
        "light_th": 0,
        "light_cu": 0,
        "curtain_status": 1
    },
    "Relax": {
        "light_th": 0,
        "light_cu": 1,
        "curtain_status": 1
    }
}

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
    "motion",
    "sound",
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

# Scene template configuration
SCENE_TEMPLATES = {
    # Sleep scene
    "sleep_mode": {
        "trigger_conditions": {
            "prediction_class": "Sleep",
            "confidence_min": 0.7
        },
        "actions": {
            "light_th": 0,
            "light_cu": 0,
            "curtain_status": 0
        },
        "priority": 10,
        "cooldown": 300  # 5 minutes
    },

    # Work scene
    "work_mode": {
        "trigger_conditions": {
            "prediction_class": "Work_On_Computer",
            "confidence_min": 0.6
        },
        "actions": {
            "light_th": 0,
            "light_cu": 1,
            "curtain_status": 1
        },
        "priority": 8,
        "cooldown": 180  # 3 minutes
    },

    # TV scene
    "tv_mode": {
        "trigger_conditions": {
            "prediction_class": "Watch_TV",
            "confidence_min": 0.6
        },
        "actions": {
            "light_th": 0,
            "light_cu": 1,
            "curtain_status": 0
        },
        "priority": 7,
        "cooldown": 180
    },

    # Cooking scene
    "cooking_mode": {
        "trigger_conditions": {
            "prediction_class": "Cook_Dinner",
            "confidence_min": 0.6,
            "temperature_max": 28.0
        },
        "actions": {
            "light_th": 1,
            "light_cu": 1,
            "curtain_status": 1
        },
        "priority": 9,
        "cooldown": 180
    },

    # Reading scene
    "reading_mode": {
        "trigger_conditions": {
            "prediction_class": "Read_Book",
            "confidence_min": 0.6,
            "brightness_max": 400
        },
        "actions": {
            "light_th": 0,
            "light_cu": 1,
            "curtain_status": 1
        },
        "priority": 8,
        "cooldown": 180
    },

    # Away scene
    "away_mode": {
        "trigger_conditions": {
            "prediction_class": "Leave_Home",
            "confidence_min": 0.7
        },
        "actions": {
            "light_th": 0,
            "light_cu": 0,
            "curtain_status": 0
        },
        "priority": 10,
        "cooldown": 600  # 10 minutes
    },

    # Exercise scene
    "exercise_mode": {
        "trigger_conditions": {
            "prediction_class": "Exercise",
            "confidence_min": 0.6
        },
        "actions": {
            "light_th": 0,
            "light_cu": 0,
            "curtain_status": 1
        },
        "priority": 7,
        "cooldown": 180
    },

    # Relax scene
    "relax_mode": {
        "trigger_conditions": {
            "prediction_class": "Relax",
            "confidence_min": 0.6
        },
        "actions": {
            "light_th": 0,
            "light_cu": 1,
            "curtain_status": 1
        },
        "priority": 6,
        "cooldown": 180
    }
}

# Environmental threshold configuration (for threshold-based decisions)
ENVIRONMENT_THRESHOLDS = {
    "temperature": {
        "high": 28.0,
        "low": 22.0,
        "comfort_min": 22.0,
        "comfort_max": 26.0
    },
    "humidity": {
        "high": 70.0,
        "low": 40.0,
        "comfort_min": 40.0,
        "comfort_max": 60.0
    },
    "brightness": {
        "dark": 100.0,
        "bright": 400.0,
        "reading_min": 300.0
    }
}

# Logging configuration
LOG_LEVEL = "INFO"
LOG_INFERENCE_DETAILS = True
LOG_DEVICE_CONTROL = True

# Performance benchmarks
INFERENCE_LATENCY_TARGET_MS = 10.0  # Target inference latency
MEMORY_USAGE_TARGET_MB = 20.0  # Target memory usage
MODEL_SIZE_TARGET_KB = 50.0  # Target model size
