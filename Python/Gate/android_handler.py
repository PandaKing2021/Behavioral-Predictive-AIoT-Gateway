"""Mobile Application (Android) Communication Handler Module.

Responsible for TCP communication with Android mobile applications, including:
- Mobile application connection listening
- User login/registration
- Threshold settings
- Device data push
"""

import json
import logging
import socket
import threading
from typing import TYPE_CHECKING

from MyComm import format_comm_data_string, format_userdata_string, decode_comm_data
from common.constants import (
    DOOR_DENIED,
    FIELD_BRIGHTNESS,
    FIELD_HUMIDITY,
    FIELD_TEMPERATURE,
    LISTEN_BACKLOG,
    ANDROID_RECV_INTERVAL,
    ANDROID_SEND_INTERVAL,
)
from common.config import UserConfig, write_user_config, load_user_config
from common.protocol import send_json, recv_json, send_line, recv_line

if TYPE_CHECKING:
    from common.models import GatewayState

logger = logging.getLogger(__name__)


class AndroidHandler:
    """Mobile application communication handler.

    Encapsulates mobile application communication logic, holds database server socket reference.

    Attributes:
        db_socket: TCP socket to database server.
        config_dir: Configuration file directory.
    """

    def __init__(self, db_socket: socket.socket, config_dir) -> None:
        self.db_socket = db_socket
        self.config_dir = config_dir

    def android_handler(self, gate_network_config, state: "GatewayState") -> None:
        """Mobile application communication main listening thread.

        Args:
            gate_network_config: Gateway network configuration.
            state: Gateway shared state object.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((gate_network_config.ip, gate_network_config.android_port))
        s.listen(LISTEN_BACKLOG)
        logger.info("Mobile application communication port opened: %s:%d",
                     gate_network_config.ip, gate_network_config.android_port)

        while True:
            try:
                cs, addr = s.accept()
                logger.info("Mobile application connected: %s", addr)
                thread = threading.Thread(
                    target=self._client_handler, args=(cs, state), daemon=True
                )
                thread.start()
            except OSError as error:
                logger.error("Mobile application listening exception: %s", error)

    def _client_handler(self, cs: socket.socket, state: "GatewayState") -> None:
        """Handle a single mobile application connection.

        Args:
            cs: Mobile application TCP socket.
            state: Gateway shared state object.
        """
        try:
            recv_data = recv_json(cs)
            android_state, curr_user_json, status_code = decode_comm_data(recv_data)
            curr_user = curr_user_json if isinstance(curr_user_json, dict) else json.loads(curr_user_json)

            if android_state == "login":
                self._android_login(cs, curr_user, state)
            elif android_state == "register":
                self._android_register(cs, curr_user)

        except (json.JSONDecodeError, ValueError) as error:
            logger.error("Failed to parse mobile application data: %s", error)
        except (ConnectionError, OSError) as error:
            logger.error("Mobile application connection disconnected: %s", error)
        except Exception as error:
            logger.error("Mobile application communication exception: %s", error)
        finally:
            cs.close()

    def _android_login(self, cs: socket.socket, curr_user: dict, state: "GatewayState") -> None:
        """Handle user login.

        Args:
            cs: Mobile application TCP socket.
            curr_user: User info dict, must contain "account" and "password" keys.
            state: Gateway shared state object.
        """
        try:
            user_config = load_user_config(config_dir=self.config_dir)
        except FileNotFoundError:
            user_config = UserConfig()

        if user_config.username == curr_user["account"] and user_config.password == curr_user["password"]:
            send_json(cs, {"status": 1})
            state.login_status = 1
            logger.info("User '%s' login successful", curr_user["account"])

            # Wait for device node connection
            state.wait_for_sensor()

            # Start send/receive threads
            recv_thread = threading.Thread(
                target=self._get_from_android, args=(cs, state), daemon=True
            )
            send_thread = threading.Thread(
                target=self._send_to_android, args=(cs, state), daemon=True
            )
            recv_thread.start()
            send_thread.start()
            recv_thread.join()
            send_thread.join()
        else:
            send_json(cs, {"status": 0})
            state.login_status = 0
            logger.warning("User '%s' login failed", curr_user["account"])

    def _android_register(self, cs: socket.socket, given_user: dict) -> None:
        """Handle user registration.

        Flow: Send user info to database server → Update local configuration based on result.

        Args:
            cs: Mobile application TCP socket.
            given_user: User info dict, must contain "account", "password", "device_Key" keys.
        """
        logger.info("User registering: %s", given_user.get("account"))

        # Construct and send registration request to database server
        db_data_send = format_comm_data_string(
            "add_new_user",
            format_userdata_string(given_user["account"], given_user["password"], given_user["device_Key"]),
            1,
        )
        send_json(self.db_socket, db_data_send)
        logger.info("Sent to database server: %s", db_data_send)

        # Receive database server response
        try:
            db_data_recv = recv_json(self.db_socket)
            _, data, status_code = decode_comm_data(db_data_recv)

            if status_code == 1:
                write_user_config(
                    UserConfig(
                        username=given_user["account"],
                        password=given_user["password"],
                        device_key=given_user["device_Key"],
                    ),
                    config_dir=self.config_dir,
                )
                logger.info("Registration successful, user info updated")
                send_json(cs, {"status": 1})
            elif status_code in (0, 2):
                logger.warning("Registration failed: %s", data)
                send_json(cs, {"status": 0})
        except (ConnectionError, OSError) as error:
            logger.error("Registration connection disconnected: %s", error)
            send_json(cs, {"status": 0})
        except Exception as error:
            logger.error("Registration exception: %s", error)
            send_json(cs, {"status": 0})

    def _send_to_android(self, cs: socket.socket, state: "GatewayState") -> None:
        """Push device data to mobile application.

        Sends sensor data in JSON format.

        Args:
            cs: Mobile application TCP socket.
            state: Gateway shared state object.
        """
        import time

        logger.info("Mobile application send sub-thread started")

        try:
            while True:
                data = state.get_data_snapshot()
                send_json(cs, data)
                logger.info("Sent to mobile application: %s", data)
                time.sleep(ANDROID_SEND_INTERVAL)

        except (ConnectionError, ConnectionAbortedError, OSError) as error:
            logger.error("Mobile application send connection disconnected: %s", error)

    def _get_from_android(self, cs: socket.socket, state: "GatewayState") -> None:
        """Receive control commands from mobile application.

        Parses operation codes and updates threshold data:
        - light_th_open/close: Smart AC on/off
        - change_temperature_threshold: Temperature threshold
        - change_humidity_threshold: Humidity threshold
        - curtain_open/close: Curtain control
        - change_brightness_threshold: Brightness threshold

        Args:
            cs: Mobile application TCP socket.
            state: Gateway shared state object.
        """
        import time

        logger.info("Mobile application receive sub-thread started")

        try:
            while True:
                recv_data = recv_json(cs)
                operation, operation_value, _ = decode_comm_data(recv_data)

                if operation == "light_th_open":
                    state.set_threshold(FIELD_TEMPERATURE, -1)
                    state.set_threshold(FIELD_HUMIDITY, -1)
                    logger.info("Mobile app command: Smart AC light turned on")
                elif operation == "light_th_close":
                    state.set_threshold(FIELD_TEMPERATURE, 101)
                    state.set_threshold(FIELD_HUMIDITY, 101)
                    logger.info("Mobile app command: Smart AC light turned off")
                elif operation == "change_temperature_threshold":
                    state.set_threshold(FIELD_TEMPERATURE, operation_value)
                elif operation == "change_humidity_threshold":
                    state.set_threshold(FIELD_HUMIDITY, operation_value)
                elif operation == "curtain_close":
                    state.set_threshold(FIELD_BRIGHTNESS, 65535)
                    logger.info("Mobile app command: Curtain closed")
                elif operation == "curtain_open":
                    state.set_threshold(FIELD_BRIGHTNESS, -2)
                    logger.info("Mobile app command: Curtain opened")
                elif operation == "change_brightness_threshold":
                    state.set_threshold(FIELD_BRIGHTNESS, operation_value)

                threshold = state.threshold_data
                logger.info(
                    "Mobile app threshold updated: Temp=%s, Humidity=%s, Brightness=%s",
                    threshold.get(FIELD_TEMPERATURE),
                    threshold.get(FIELD_HUMIDITY),
                    threshold.get(FIELD_BRIGHTNESS),
                )

        except (ConnectionError, ConnectionAbortedError, OSError) as error:
            logger.error("Mobile application receive connection disconnected: %s", error)
        except (ValueError, json.JSONDecodeError) as error:
            logger.error("Failed to parse mobile application command: %s", error)
