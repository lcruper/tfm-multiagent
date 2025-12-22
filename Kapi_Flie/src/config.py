"""
Centralized Configuration Module for the Drone and Robot Dog System
-------------------------------------------------------------------

This module defines all parameters and global constants used across the project.
All values are intended to be read-only and should not be modified
at runtime.
"""

from pathlib import Path
import struct
from typing import Final

# ============================================================
# Drone Telemetry
# ============================================================

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

STRUCT_POSE: Final[struct.Struct] = struct.Struct("<6f")
"""Struct format for unpacking pose telemetry packets."""

STRUCT_BATTERY: Final[struct.Struct] = struct.Struct("<f")
"""Struct format for unpacking battery telemetry packets."""


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


# ============================================================
# Spiral Movement Simulation
# ============================================================

SPIRAL_SIMULATOR_RADIAL_GROWTH: Final[float] = 0.16
"""Radial growth rate (m/s) for spiral movement simulation."""

SPIRAL_SIMULATOR_LINEAR_SPEED: Final[float] = 0.25
"""Linear speed (m/s) of the spiral movement."""


SPIRAL_SIMULATOR_JITTER: Final[float] = 0.02
"""Random jitter factor applied to spiral motion."""

SPIRAL_SIMULATOR_EXP_SMOOTH: Final[float] = 0.1
"""Exponential smoothing factor for radial changes."""

# ============================================================
# Camera
# ============================================================

CAMERA_STREAM_URL: Final[str] = "http://192.168.43.44:81/stream"
"""URL of the camera video stream."""

CAMERA_FLASH_URL: Final[str] = CAMERA_STREAM_URL.replace("81/stream", "80/control")
"""URL to control the camera flash."""


CAMERA_STREAM_RETRY_DELAY: Final[float] = 5.0
"""Delay before retrying to open the camera stream (seconds)."""

CAMERA_REQUEST_TIMEOUT: Final[float] = 1.0
"""Timeout for camera HTTP requests (seconds)."""

CAMERA_FLASH_INTENSITY_ON: Final[int] = 25
"""Flash intensity used to turn the camera flash ON."""

CAMERA_FLASH_INTENSITY_OFF: Final[int] = 0
"""Flash intensity used to turn the camera flash OFF."""

CAMERA_SLEEP_TIME: Final[float] = 0.01
"""Sleep duration between camera processing cycles."""

# ============================================================
# Camera Simulator
# ============================================================

CAMERA_SIMULATOR_COLOR_PROBABILITY: Final[float] = 0.3
"""Probability of generating a `COLOR_DETECTION_COLOR` object in the simulated camera frame."""

CAMERA_SIMULATOR_COLOR_DICT: Final[dict] = {
    "red": [0, 0, 255],
    "green": [0, 255, 0],
    "blue": [255, 0, 0],
    "yellow": [0, 255, 255],
    "orange": [0, 165, 255],
    "purple": [255, 0, 255],
    "cyan": [255, 255, 0],
    "pink": [255, 192, 203],
}
"""BGR color values for different target colors used in the camera simulator."""

CAMERA_SIMULATOR_MIN_RADIUS: Final[int] = 50
"""Minimum radius of objects generated in the simulated camera frame."""

CAMERA_SIMULATOR_MAX_RADIUS: Final[int] = 100
"""Maximum radius of objects generated in the simulated camera frame."""

CAMERA_SIMULATOR_FRAME_PERIOD: Final[float] = 2.0
"""Time period (in seconds) between frames in the camera simulator."""

CAMERA_SIMULATOR_SLEEP_TIME: Final[float] = 0.01
"""Sleep duration between camera simulator cycles."""

# ============================================================
# Matcher
# ============================================================

MATCHER_SLEEP_TIME: Final[float] = 0.01
"""Sleep duration between matcher processing cycles."""

# ============================================================
# Color Detection
# ============================================================

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
"""Absolute path to the project root directory."""

YOLO_MODEL_PATH: Final[Path] = PROJECT_ROOT / "yoloModels" / "yolov8n.pt"
"""Absolute path to the YOLO model file."""

COLOR_DETECTION_COLOR: Final[str] = "red"
"""Default target color for detection."""


COLOR_DETECTION_MAX_QUEUE_SIZE: Final[int] = 100
"""Maximum size of the color detection result queue."""

COLOR_DETECTION_COLORS: Final[dict] = {
    "red": {
        "lower1": [0, 80, 50],
        "upper1": [10, 255, 255],
        "lower2": [160, 80, 50],
        "upper2": [180, 255, 255],
    },
    "green": {
        "lower1": [40, 50, 50],
        "upper1": [80, 255, 255],
    },
    "blue": {
        "lower1": [100, 150, 50],
        "upper1": [140, 255, 255],
    },
    "yellow": {
        "lower1": [20, 100, 100],
        "upper1": [30, 255, 255],
    },
    "orange": {
        "lower1": [10, 100, 20],
        "upper1": [25, 255, 255],
    },
    "purple": {
        "lower1": [130, 50, 50],
        "upper1": [160, 255, 255],
    },
    "cyan": {
        "lower1": [80, 50, 50],
        "upper1": [100, 255, 255],
    },
    "pink": {
        "lower1": [145, 50, 50],
        "upper1": [170, 255, 255],
    },
}
"""HSV color ranges used for color segmentation."""

COLOR_DETECTION_IMG_SIZE: Final[int] = 256
"""Input image size used for YOLO inference."""

COLOR_DETECTION_CONF_THRESH: Final[float] = 0.35
"""Confidence threshold for YOLO detections."""

COLOR_DETECTION_IOU_THRESH: Final[float] = 0.45
"""Intersection-over-Union threshold for non-maximum suppression."""

COLOR_DETECTION_MIN_BOX_AREA: Final[int] = 100
"""Minimum acceptable bounding box area for detected objects."""

COLOR_DETECTION_THRESH: Final[float] = 0.30
"""Final threshold for color-based decision making."""

COLOR_DETECTION_SLEEP_TIME: Final[float] = 0.01
"""Sleep duration between color detection processing cycles."""


# ============================================================
# Viewer
# ============================================================

VIEWER_MAX_QUEUE_SIZE: Final[int] = 100
"""Maximum number of frames stored in the viewer queue."""

VIEWER_OVERLAY_ALPHA: Final[float] = 0.45
"""Alpha transparency used for overlay rendering."""

VIEWER_BAR_HEIGHT: Final[int] = 75
"""Height (in pixels) of the telemetry overlay bar."""

VIEWER_FONT_SIZE: Final[float] = 0.45
"""Font scale used for overlay text rendering."""

VIEWER_SLEEP_TIME: Final[float] = 0.005
"""Sleep duration in the viewer loop."""


# ============================================================
# Robot Dog
# ============================================================

ROBOT_DOG_SPEED: Final[float] = 0.5
"""Default walking speed of the robot dog."""


ROBOT_DOG_REACHED_TOLERANCE: Final[float] = 0.05
"""Distance threshold to consider a target point reached."""

ROBOT_SLEEP_TIME: Final[float] = 0.1
"""Sleep duration between robot dog movement steps."""

ROBOT_DOG_MEAN_TEMPERATURE: Final[float] = 25.0
"""Mean ambient temperature measured by the robot dog (Celsius)."""

ROBOT_DOG_TEMPERATURE_STDDEV: Final[float] = 5.0
"""Standard deviation of ambient temperature measured by the robot dog (Celsius)."""

# ============================================================
# Operation
# ============================================================

DRONE_VISIBILITY: Final[float] = 1.0
"""Maximum visibility radius of the drone."""
