"""Device Node Communication Handler Module.

Responsible for TCP communication with IoT device nodes (sensors), including:
- Device node connection listening
- Device identity verification
- Sensor data reception and processing
- Control command dispatch
- Door security monitoring
- AI prediction-based intelligent decision making (new)
"""

import json
import logging
import socket
import threading
from typing import TYPE_CHECKING, Optional

from common.constants import (
    BUFFER_SIZE_MEDIUM,
    DOOR_DENIED,
    DOOR_GRANTED,
    FIELD_BRIGHTNESS,
    FIELD_CURTAIN_STATUS,
    FIELD_DEVICE_KEY,
    FIELD_DOOR_STATUS,
    FIELD_HUMIDITY,
    FIELD_LIGHT_CU,
    FIELD_LIGHT_TH,
    FIELD_TEMPERATURE,
    LISTEN_BACKLOG,
    SENSOR_RECV_INTERVAL,
    SENSOR_SEND_INTERVAL,
)
from common.protocol import send_json, recv_json, send_line, recv_line

if TYPE_CHECKING:
    from common.models import GatewayState

logger = logging.getLogger(__name__)

# Global prediction module instances (lazy initialization)
_prediction_engine = None
_precontroller = None
_data_collector = None
_data_preprocessor = None


def get_from_sensor(cs: socket.socket, state: "GatewayState") -> None:
    """Receive sensor data from device node (runs in a separate thread).

    Receives JSON format device data, updates gateway state, executes intelligent
    decision logic, and stores data in local database.

    Args:
        cs: Device node TCP socket.
        state: Gateway shared state object.
    """
    import time
    import database as db_module

    logger.info("Gateway receive thread started")

    try:
        while True:
            data_recv = recv_json(cs, BUFFER_SIZE_MEDIUM)

            # Parse device node data
            if not isinstance(data_recv, dict):
                logger.warning("Device data format error (expected dict): %s", type(data_recv).__name__)
                time.sleep(SENSOR_RECV_INTERVAL)
                continue

            state.update_data(data_recv)

            snapshot = state.get_data_snapshot()
            logger.info(
                "Received from device node: AC=%s, Temp=%s, Humidity=%s, Light=%s, Brightness=%s, Curtain=%s",
                snapshot.get(FIELD_LIGHT_TH),
                snapshot.get(FIELD_TEMPERATURE),
                snapshot.get(FIELD_HUMIDITY),
                snapshot.get(FIELD_LIGHT_CU),
                snapshot.get(FIELD_BRIGHTNESS),
                snapshot.get(FIELD_CURTAIN_STATUS),
            )

            # Store data in local database
            db_module.save_sensor_data(db_module._gate_db_conn, snapshot)

            # Gateway intelligent decision
            _process_smart_decision(state, snapshot)

            time.sleep(SENSOR_RECV_INTERVAL)

    except (ConnectionError, OSError) as error:
        logger.error("Device node receive connection disconnected: %s", error)
    except json.JSONDecodeError as error:
        logger.error("Device node data JSON parsing failed: %s", error)
    except Exception as error:
        logger.error("Device node receive data error: %s", error)


def send_to_sensor(cs: socket.socket, state: "GatewayState") -> None:
    """Send control commands to device node (runs in a separate thread).

    Sends device status data in JSON format.

    Args:
        cs: Device node TCP socket.
        state: Gateway shared state object.
    """
    import time

    logger.info("Gateway send thread started")

    try:
        while True:
            data_send = state.get_data_snapshot()
            send_json(cs, data_send)
            logger.info("Sent to device node: %s", data_send)
            time.sleep(SENSOR_SEND_INTERVAL)

    except (ConnectionError, OSError) as error:
        logger.error("Device node send connection disconnected: %s", error)


def sensor_client_handler(cs: socket.socket, state: "GatewayState") -> None:
    """Handle a single device node connection.

    Flow: Receive device ID → Door security verification → Device identity verification → Start send/receive threads.

    Args:
        cs: Device node TCP socket.
        state: Gateway shared state object.
    """
    import time

    try:
        # Get device node ID
        device_id = recv_line(cs).strip()

        # Door security verification
        if state.door_permission == DOOR_DENIED:
            listen_door_security(device_id, cs, state)

        if device_id != "0":
            if state.is_device_permitted(device_id) and state.door_permission == DOOR_GRANTED:
                logger.info("Device node '%s' connected to gateway", device_id)
                state.source_start_flag = 1
                send_line(cs, "start")

                recv_thread = threading.Thread(
                    target=get_from_sensor, args=(cs, state), daemon=True
                )
                send_thread = threading.Thread(
                    target=send_to_sensor, args=(cs, state), daemon=True
                )
                recv_thread.start()
                send_thread.start()
                recv_thread.join()
                send_thread.join()

            else:
                if not state.is_device_permitted(device_id):
                    logger.warning("Device node '%s' does not belong to this user, connection denied", device_id)
                elif state.door_permission == DOOR_DENIED:
                    logger.warning("Door security not activated, device node '%s' access denied", device_id)
        else:
            logger.warning("Device node connection denied")

    except (ConnectionError, OSError) as error:
        logger.error("Device node handler connection disconnected: %s", error)
    except Exception as error:
        logger.error("Device node handler exception: %s", error)
    finally:
        cs.close()


def sensor_handler(gate_config, state: "GatewayState") -> None:
    """Device node communication main listening thread.

    Listens for TCP connections from device nodes on the specified port.

    Args:
        gate_config: Gateway network configuration.
        state: Gateway shared state object.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((gate_config.ip, gate_config.source_port))
    s.listen(LISTEN_BACKLOG)
    logger.info("Device node communication port opened: %s:%d", gate_config.ip, gate_config.source_port)

    try:
        while True:
            cs, addr = s.accept()
            logger.info("Device node connected: %s", addr)
            thread = threading.Thread(
                target=sensor_client_handler, args=(cs, state), daemon=True
            )
            thread.start()

    except OSError as error:
        logger.error("Device node listening error: %s", error)


def listen_door_security(device_id: str, cs: socket.socket, state: "GatewayState") -> None:
    """Blocking door security status monitoring.

    If connected device is a door security device, wait for door verification;
    If non-door device, block and wait for door access.

    Args:
        device_id: Device identifier.
        cs: Device node TCP socket.
        state: Gateway shared state object.
    """
    import time

    if "security" in device_id:
        logger.info("Door security device detected")
        while True:
            try:
                recv_data = recv_json(cs)
                security_status = recv_data.get(FIELD_DOOR_STATUS, 0)

                if int(security_status) == DOOR_GRANTED:
                    logger.info("Door security access granted")
                    state.door_permission = DOOR_GRANTED
                    state.update_data(recv_data)
                    break
                else:
                    logger.info("Door security access denied")
                    time.sleep(1)
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning("Door security data parsing failed: %s", e)
                time.sleep(1)
            except (ConnectionError, OSError):
                logger.error("Door security device connection disconnected")
                break
    else:
        logger.info("Non-door security device detected, waiting for door access")
        # Use Event instead of busy waiting
        if not state.wait_for_sensor(timeout=None):
            logger.warning("Door security wait timed out")


def init_prediction_modules(db_conn) -> None:
    """Initialize prediction modules (lazy loading).

    Args:
        db_conn: Database connection object.
    """
    global _prediction_engine, _precontroller, _data_collector, _data_preprocessor

    try:
        from prediction import DataCollector, DataPreprocessor, ONNXModelInference, Precontroller
        from prediction.config import (
            EDGE_MODEL_PATH,
            SENTINEL_MODEL_PATH,
            SENTINEL_THRESHOLD,
            DATA_COLLECTION_WINDOW_HOURS,
            FEATURE_COLUMNS,
            NORMALIZATION_METHOD,
            SEQUENCE_LENGTH,
        )

        # Initialize data collector
        _data_collector = DataCollector(db_conn, cache_hours=DATA_COLLECTION_WINDOW_HOURS)
        logger.info("Data collector initialized successfully")

        # Initialize data preprocessor
        _data_preprocessor = DataPreprocessor(
            feature_columns=FEATURE_COLUMNS,
            normalization_method=NORMALIZATION_METHOD
        )
        logger.info("Data preprocessor initialized successfully")

        # Initialize ONNX inference engine
        import os
        model_dir = os.path.join(os.path.dirname(__file__), "models")

        edge_model_path = os.path.join(model_dir, "edge_1dcnn_lstm.onnx")
        sentinel_model_path = os.path.join(model_dir, "sentinel_lstm.onnx")

        # Check if model files exist
        if not os.path.exists(edge_model_path):
            logger.warning("Edge model file not found: %s, prediction will be disabled", edge_model_path)
            return

        # If sentinel model doesn't exist, use edge model only
        sentinel_path = sentinel_model_path if os.path.exists(sentinel_model_path) else None

        _prediction_engine = ONNXModelInference(
            edge_model_path=edge_model_path,
            sentinel_model_path=sentinel_path,
            threshold=SENTINEL_THRESHOLD
        )
        logger.info("ONNX inference engine initialized successfully")

        # Model warmup
        _prediction_engine.warmup()

        # Initialize pre-controller
        _precontroller = Precontroller()
        logger.info("Pre-controller initialized successfully")

        logger.info("All prediction modules initialized successfully")

    except Exception as error:
        logger.error("Prediction modules initialization failed: %s, will use threshold decision", error)
        _prediction_engine = None
        _precontroller = None


def _process_smart_decision(state: "GatewayState", snapshot: dict) -> None:
    """Gateway intelligent decision logic.

    Prioritizes AI prediction-driven decisions, falls back to threshold decisions on failure.

    Args:
        state: Gateway shared state object.
        snapshot: Current sensor data snapshot.
    """
    # Try AI prediction decision
    if _prediction_engine is not None and _precontroller is not None:
        try:
            commands = _process_prediction_decision(state, snapshot)
            if commands:
                state.update_status(commands)
                state.update_data(commands)
                logger.info("AI prediction decision triggered: %s", commands)
                return
        except Exception as error:
            logger.error("AI prediction decision failed: %s, falling back to threshold decision", error)

    # Fall back to threshold decision
    _process_threshold_decision(state, snapshot)


def _process_prediction_decision(state: "GatewayState", snapshot: dict) -> dict:
    """AI prediction-based intelligent decision logic.

    Flow:
    1. Update data cache
    2. Extract recent time-series data
    3. Data preprocessing
    4. Model inference
    5. Pre-controller generates control commands

    Args:
        state: Gateway shared state object.
        snapshot: Current sensor data snapshot.

    Returns:
        Device control command dictionary.
    """
    global _data_collector, _data_preprocessor, _prediction_engine, _precontroller

    if _data_collector is None or _data_preprocessor is None:
        logger.warning("Data collector or preprocessor not initialized")
        return {}

    # 1. Update data cache
    _data_collector.update_cache(incremental=True)

    # 2. Extract recent time-series data
    from prediction.config import SEQUENCE_LENGTH
    features = _data_collector.get_latest_samples(n_samples=SEQUENCE_LENGTH)
    if features is None:
        logger.warning("Insufficient cached data, unable to execute prediction")
        return {}

    # 3. Data preprocessing (normalization parameters need to be fitted first)
    # Simplified here; in practice, normalization parameters should be saved during training
    # Assume normalization parameters have been fitted
    if not _data_preprocessor.normalization_params:
        logger.warning("Normalization parameters not fitted, skipping prediction")
        return {}

    normalized_features = _data_preprocessor.transform(
        __import__('pandas').DataFrame(features, columns=_data_preprocessor.feature_columns)
    )

    # 4. Model inference
    input_data = normalized_features.reshape(1, SEQUENCE_LENGTH, -1)
    predictions, stats = _prediction_engine.predict(input_data, return_stats=True)
    prediction_result = float(predictions[0][0])

    logger.info(
        "AI prediction result: %.4f, inference latency: %.2f ms",
        prediction_result,
        stats.get("total_latency_ms", 0) if stats else 0
    )

    # 5. Pre-controller generates control commands
    context = {
        FIELD_TEMPERATURE: float(snapshot.get(FIELD_TEMPERATURE, 0)),
        FIELD_HUMIDITY: float(snapshot.get(FIELD_HUMIDITY, 0)),
        FIELD_BRIGHTNESS: float(snapshot.get(FIELD_BRIGHTNESS, 0)),
        FIELD_LIGHT_TH: int(snapshot.get(FIELD_LIGHT_TH, 0)),
        FIELD_LIGHT_CU: int(snapshot.get(FIELD_LIGHT_CU, 0)),
        FIELD_CURTAIN_STATUS: int(snapshot.get(FIELD_CURTAIN_STATUS, 1)),
    }

    control_commands = _precontroller.evaluate(prediction_result, context)

    return control_commands


def _process_threshold_decision(state: "GatewayState", snapshot: dict) -> None:
    """Threshold-based traditional decision logic.

    Automatically controls devices based on sensor data and thresholds:
    - Temperature/humidity exceeds threshold → Turn on AC (Light_TH=1), otherwise turn off
    - Brightness exceeds threshold → Turn off light and open curtain, otherwise reverse

    Args:
        state: Gateway shared state object.
        snapshot: Current sensor data snapshot.
    """
    threshold = state.threshold_data
    status_updates = {}

    # Temperature/humidity decision
    temp = float(snapshot.get(FIELD_TEMPERATURE, 0))
    humidity = float(snapshot.get(FIELD_HUMIDITY, 0))
    temp_threshold = float(threshold.get(FIELD_TEMPERATURE, 0))
    humidity_threshold = float(threshold.get(FIELD_HUMIDITY, 0))
    current_light_th = int(snapshot.get(FIELD_LIGHT_TH, 0))

    if temp >= temp_threshold and humidity >= humidity_threshold:
        if current_light_th == 0:
            status_updates[FIELD_LIGHT_TH] = 1
    else:
        if current_light_th == 1:
            status_updates[FIELD_LIGHT_TH] = 0

    # Brightness decision
    brightness = float(snapshot.get(FIELD_BRIGHTNESS, 0))
    brightness_threshold = float(threshold.get(FIELD_BRIGHTNESS, 0))
    current_light_cu = int(snapshot.get(FIELD_LIGHT_CU, 0))
    current_curtain = int(snapshot.get(FIELD_CURTAIN_STATUS, 1))

    if brightness >= brightness_threshold:
        if current_light_cu == 1 and current_curtain == 0:
            status_updates[FIELD_LIGHT_CU] = 0
            status_updates[FIELD_CURTAIN_STATUS] = 1
    else:
        if current_light_cu == 0 and current_curtain == 1:
            status_updates[FIELD_LIGHT_CU] = 1
            status_updates[FIELD_CURTAIN_STATUS] = 0

    if status_updates:
        state.update_status(status_updates)
        state.update_data(status_updates)
        logger.info("Threshold decision triggered: %s", status_updates)
