import struct
from typing import Final

DRONE_IP: Final[str] = "192.168.43.42"
"""IP address of the drone telemetry server."""

DRONE_PORT: Final[int] = 2390
"""UDP port where the drone sends telemetry packets."""

LOCAL_PORT: Final[int] = 2391
"""Local UDP port used to receive telemetry data."""

PACKET_ID_BATTERY: Final[int] = 0x01
"""Packet ID for battery telemetry packets."""

PACKET_ID_POSE: Final[int] = 0x02
"""Packet ID for pose telemetry packets."""

STRUCT_BATTERY: Final[struct.Struct] = struct.Struct("<f")
"""Struct format for unpacking battery telemetry packets."""

STRUCT_POSE: Final[struct.Struct] = struct.Struct("<6f")
"""Struct format for unpacking pose telemetry packets."""

DRONE_UDP_BUFFER_SIZE: Final[int] = 128
"""Maximum UDP packet size for telemetry messages."""

DRONE_UDP_TIMEOUT: Final[float] = 0.5
"""Timeout (in seconds) for UDP socket operations."""

DRONE_UDP_HANDSHAKE_RETRIES: Final[int] = 1
"""Number of retry attempts during telemetry handshake."""

HANDSHAKE_PACKET: Final[bytes] = b'\x01\x01'
"""Handshake packet sent to initiate telemetry communication."""

DRONE_UDP_HANDSHAKE_RETRY_DELAY: Final[float] = 0.5
"""Delay (in seconds) between handshake retry attempts."""