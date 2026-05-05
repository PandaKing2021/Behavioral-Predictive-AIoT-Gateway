"""IoT Gateway Communication Protocol Codec Module.

All TCP communications use JSON format uniformly, with messages separated by ``\\n`` (LF).

Protocol Structure (Command/Response Class)::

    {"op": "operation_code", "data": <payload>, "status": <status_code>}

The old protocol ``"op|data|status"`` has been completely replaced by JSON format.
The old user data format ``"user+pwd+key"`` has been replaced by JSON object ``{"username":...,"password":...,"device_key":...}``.

This module retains the four core function signatures and return value formats for compatibility with upper-layer calls.
"""

from common.protocol import (
    pack_command,
    unpack_command,
    pack_user_data,
    unpack_user_data,
)


def format_comm_data_string(operation: str, data, status_code) -> dict:
    """Construct command JSON object (compatible with old interface name).

    Pack operation code, data code, and status code into ``{"op":..., "data":..., "status":...}`` JSON object.

    Args:
        operation: Operation code (e.g., ``"add_new_user"``, ``"check_userconfig_illegal"``).
        data: Payload data.
        status_code: Status code.

    Returns:
        Command dictionary (can be serialized directly with ``json.dumps()``).
    """
    return pack_command(operation, data, status_code)


def format_userdata_string(username: str, password: str, device_key: str) -> dict:
    """Construct user information JSON object (compatible with old interface name).

    Args:
        username: Username.
        password: Password.
        device_key: Device key.

    Returns:
        User information dictionary.
    """
    return pack_user_data(username, password, device_key)


def decode_comm_data(message) -> tuple:
    """Unpack command JSON object (compatible with old interface name).

    Args:
        message: Command dictionary or parsed JSON object.

    Returns:
        Tuple ``(operation, data, status_code)``.

    Raises:
        ValueError: Data format error.
    """
    return unpack_command(message)


def decode_user_data(data) -> tuple:
    """Unpack user information JSON object (compatible with old interface name).

    Args:
        data: User information dictionary.

    Returns:
        Tuple ``(username, password, device_key)``.

    Raises:
        ValueError: Data format error.
    """
    return unpack_user_data(data)
