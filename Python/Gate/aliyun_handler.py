"""Alibaba Cloud IoT Communication Module.

Responsible for uploading sensor data to Alibaba Cloud IoT platform via MQTT protocol.
"""

import hashlib
import hmac as hmac_mod
import json
import logging
import time
from typing import Any, Dict, Optional

import paho.mqtt.client as mqtt

from common.constants import (
    ALIYUN_MQTT_PORT,
    ALIYUN_UPLOAD_INTERVAL,
    FIELD_BRIGHTNESS,
    FIELD_CURTAIN_STATUS,
    FIELD_HUMIDITY,
    FIELD_LIGHT_CU,
    FIELD_LIGHT_TH,
    FIELD_TEMPERATURE,
)
from common.config import AliyunIotConfig

logger = logging.getLogger(__name__)


def hmacsha1(key: str, msg: str) -> str:
    """Compute HMAC-SHA1 signature.

    Args:
        key: Secret key.
        msg: Message content.

    Returns:
        Hexadecimal signature string.
    """
    return hmac_mod.new(key.encode("utf-8"), msg.encode("utf-8"), hashlib.sha1).hexdigest()


def create_mqtt_client(iot_config: AliyunIotConfig) -> Optional[mqtt.Client]:
    """Create Alibaba Cloud IoT MQTT client.

    Generates client credentials using HMAC-SHA1 authentication.

    Args:
        iot_config: Alibaba Cloud IoT configuration.

    Returns:
        Configured MQTT client, or None on failure.
    """
    timestamp = str(int(time.time()))
    client_id = f"paho.py|securemode=3,signmethod=hmacsha1,timestamp={timestamp}|"
    content_str = (
        f"clientIdpaho.py"
        f"deviceName{iot_config.device_name}"
        f"productKey{iot_config.product_key}"
        f"timestamp{timestamp}"
    )
    username = f"{iot_config.device_name}&{iot_config.product_key}"
    password = hmacsha1(iot_config.device_secret, content_str)

    try:
        client = mqtt.Client(client_id=client_id, clean_session=False)
        client.username_pw_set(username, password)
        return client
    except Exception as error:
        logger.error("Failed to create MQTT client: %s", error)
        return None


def on_connect(client, userdata, flags, rc):
    """MQTT connection callback."""
    logger.info("Alibaba Cloud IoT connection result: %d", rc)


def on_message(client, userdata, msg):
    """MQTT message callback."""
    logger.info("Alibaba Cloud IoT message received: %s %s", msg.topic, msg.payload)


def aliyun_upload_loop(
    iot_config: AliyunIotConfig,
    get_data_fn,
    wait_for_sensor_fn,
) -> None:
    """Alibaba Cloud data upload main loop (runs in a separate thread).

    Blocks until device node connects, then periodically uploads sensor data to Alibaba Cloud IoT.

    Args:
        iot_config: Alibaba Cloud IoT configuration.
        get_data_fn: Callback function to get sensor data snapshot.
        wait_for_sensor_fn: Callback function to wait for device node connection.
    """
    host = f"{iot_config.product_key}.iot-as-mqtt.{iot_config.region_id}.aliyuncs.com"
    pub_topic = (
        f"/sys/{iot_config.product_key}/{iot_config.device_name}/thing/event/property/post"
    )

    client = create_mqtt_client(iot_config)
    if client is None:
        logger.error("Unable to create MQTT client, Alibaba Cloud upload thread exiting")
        return

    client.on_connect = on_connect
    client.on_message = on_message

    logger.info("Alibaba Cloud upload thread started, waiting for device node connection...")
    wait_for_sensor_fn()
    logger.info("Starting to send data to Alibaba Cloud server")

    timestamp = 0
    while True:
        timestamp += 1
        try:
            client.reconnect()
            data = get_data_fn()

            payload_json = {
                "id": timestamp,
                "params": {
                    "Light_TH": data.get(FIELD_LIGHT_TH, 0),
                    "Temperature": data.get(FIELD_TEMPERATURE, 0),
                    "Humidity": data.get(FIELD_HUMIDITY, 0),
                    "Light_CU": data.get(FIELD_LIGHT_CU, 0),
                    "Brightness": data.get(FIELD_BRIGHTNESS, 0),
                    "Curtain_status": data.get(FIELD_CURTAIN_STATUS, 1),
                },
                "method": "thing.event.property.post",
            }

            client.publish(pub_topic, payload=json.dumps(payload_json), qos=1)
            logger.info("Sent to Alibaba Cloud IoT: %s", payload_json)

        except Exception as error:
            logger.error("Alibaba Cloud data upload failed: %s", error)

        time.sleep(ALIYUN_UPLOAD_INTERVAL)
