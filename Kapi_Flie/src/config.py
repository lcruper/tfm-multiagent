# config.py
"""
@file config.py
@brief Centralized configuration for the drone + robot dog system.
"""

from pathlib import Path
from typing import Final

# ============================================================
# Drone Telemetry
# ============================================================

#: @brief Base IP address of the drone.
DRONE_IP: Final[str] = "192.168.43.42"

#: @brief UDP port where the drone sends telemetry packets.
DRONE_PORT: Final[int] = 2390

#: @brief Local UDP port used by this system to receive telemetry.
LOCAL_PORT: Final[int] = 2391


#: @brief Maximum UDP packet size for telemetry messages.
DRONE_UDP_BUFFER_SIZE: Final[int] = 128

#: @brief Timeout for UDP socket operations.
DRONE_UDP_TIMEOUT: Final[float] = 0.5

#: @brief Number of retries when performing handshake with the drone.
DRONE_UDP_HANDSHAKE_RETRIES: Final[int] = 3

#: @brief Delay between handshake retry attempts.
DRONE_UDP_HANDSHAKE_RETRY_DELAY: Final[float] = 0.1


# ============================================================
# Spiral Movement Simulation
# ============================================================

#: @brief Radial growth per second for the spiral movement simulator.
SPIRAL_SIMULATOR_RADIAL_GROWTH: Final[float] = 0.16

#: @brief Angular velocity for the spiral movement simulation.
SPIRAL_SIMULATOR_ANGULAR_SPEED: Final[float] = 0.25


#: @brief Random jitter factor applied to the spiral movement simulation.
SPIRAL_SIMULATOR_JITTER: Final[float] = 0.02

#: @brief Exponential smoothing factor applied to radial changes in the spiral movement simulation.
SPIRAL_SIMULATOR_EXP_SMOOTH: Final[float] = 0.1


# ============================================================
# Constant Movement Simulation
# ============================================================

#: @brief Fixed X coordinate for constant position simulation.
CONSTANT_SIMULATOR_X: Final[float] = 10

#: @brief Fixed Y coordinate for constant position simulation.
CONSTANT_SIMULATOR_Y: Final[float] = 10


# ============================================================
# Camera
# ============================================================

#: @brief Delay before retrying to open the camera stream.
CAMERA_STREAM_RETRY_DELAY: Final[float] = 1.0

#: @brief Timeout for camera HTTP requests.
CAMERA_REQUEST_TIMEOUT: Final[float] = 1.0

#: @brief Flash intensity value used to turn ON the camera flash.
CAMERA_FLASH_INTENSITY_ON: Final[int] = 25

#: @brief Flash intensity value used to turn OFF the camera flash.
CAMERA_FLASH_INTENSITY_OFF: Final[int] = 0

#: @brief Sleep time between camera processing cycles.
CAMERA_SLEEP_TIME: Final[float] = 0.01


# ============================================================
# Matcher
# ============================================================

#: @brief Sleep time for each loop of the matcher module.
MATCHER_SLEEP_TIME: Final[float] = 0.01


# ============================================================
# Color Detection
# ============================================================

#: @brief Path to the YOLO neural network model file.
YOLO_MODEL_PATH: Final[str] = str(Path("yoloModels/yolov8n.pt"))

#: @brief Default target color name for detection.
COLOR_DETECTION_COLOR: Final[str] = "red"


#: @brief Maximum number of items stored in the color detection queue.
COLOR_DETECTION_MAX_QUEUE_SIZE: Final[int] = 100

#: @brief HSV color ranges used for color segmentation.
COLOR_DETECTION_COLORS: Final[dict] = {
    "red": {
        "lower1": [0, 80, 50],
        "upper1": [10, 255, 255],
        "lower2": [160, 80, 50],
        "upper2": [180, 255, 255],
    },
}

#: @brief Target input image size for the YOLO model.
COLOR_DETECTION_IMG_SIZE: Final[int] = 256

#: @brief Confidence threshold for YOLO detections.
COLOR_DETECTION_CONF_THRESH: Final[float] = 0.35

#: @brief Intersection-over-Union threshold for non-maximum suppression.
COLOR_DETECTION_IOU_THRESH: Final[float] = 0.45

#: @brief Minimum acceptable bounding box area for detected objects.
COLOR_DETECTION_MIN_BOX_AREA: Final[int] = 100

#: @brief Threshold for the final stage of color-based decision-making.
COLOR_DETECTION_THRESH: Final[float] = 0.30

#: @brief Sleep time between detection iterations.
COLOR_DETECTION_SLEEP_TIME: Final[float] = 0.01


# ============================================================
# Viewer
# ============================================================

#: @brief Maximum number of frames stored in the viewer queue.
VIEWER_MAX_QUEUE_SIZE: Final[int] = 100

#: @brief Alpha transparency for overlaying information on the viewer window.
VIEWER_OVERLAY_ALPHA: Final[float] = 0.45

#: @brief Height of the telemetry overlay bar.
VIEWER_BAR_HEIGHT: Final[int] = 75

#: @brief Font size used when drawing overlay text.
VIEWER_FONT_SIZE: Final[float] = 0.45

#: @brief Sleep time in the viewer loop.
VIEWER_SLEEP_TIME: Final[float] = 0.005


# ============================================================
# Robot Dog
# ============================================================

#: @brief Walking speed of the robot dog.
ROBOT_DOG_SPEED: Final[float] = 0.5


#: @brief Maximum distance to a target point considered as "reached".
ROBOT_DOG_REACHED_TOLERANCE: Final[float] = 0.05

#: @brief Delay between robot dog movement commands.
ROBOT_DOG_STEP_DELAY: Final[float] = 0.1


# ============================================================
# Mission
# ==========================================================

#: @brief Minimum distance between inspection points.
INSPECTION_POINT_MIN_DIST: Final[float] = 0.5
