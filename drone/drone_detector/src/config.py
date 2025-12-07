# config.py
"""
@brief Centralized configuration for the drone + robot dog system.
"""

from pathlib import Path
from typing import Final

# ----------------------------
# Logging
# ----------------------------
LOG_LEVEL: Final[str] = "INFO"                                                     # Logging level: DEBUG, INFO, WARNING, ERROR
LOG_FORMAT: Final[str] = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"     # Log message format

# ----------------------------
# Drone Listener
# ----------------------------
DRONE_IP: Final[str] = "192.168.43.42"                     # Base IP of the drone
DRONE_PORT: Final[int] = 2390                              # UDP port for the drone telemetry
LOCAL_PORT: Final[int] = 2391                              # UDP port for receiving telemetry

DRONE_UDP_BUFFER_SIZE: Final[int] = 128                    # Max UDP packet size
DRONE_UDP_TIMEOUT: Final[float] = 0.5                      # Socket timeout in seconds
DRONE_UDP_HANDSHAKE_RETRIES: Final[int] = 3                # Number of handshake attempts
DRONE_UDP_HANDSHAKE_RETRY_DELAY: Final[float] = 0.1        # Delay between handshake attempts in seconds

# ----------------------------
# Drone Simulation
# ----------------------------
SIMULATOR_RADIAL_GROWTH: Final[float] = 0.3       # Radio growth per second
SIMULATOR_ANGULAR_SPEED: Final[float] = 0.1       # Angular speed in radians per second

SIMULATOR_JITTER: Final[float] = 0.02             # Jitter factor for simulation
SIMULATOR_EXP_SMOOTH: Final[float] = 0.1          # Smoothing factor for radius
# ----------------------------
# Camera
# ----------------------------
CAMERA_STREAM_RETRY_DELAY: Final[float] = 1.0              # Seconds to wait before retrying to open the stream if it fails
CAMERA_STREAM_OPEN_TIMEOUT: Final[float] = 1.0             # Timeout for opening the stream
CAMERA_FLASH_INTENSITY_ON: Final[int] = 255                # Intensity value to turn on the flash
CAMERA_FLASH_INTENSITY_OFF: Final[int] = 0                 # Intensity value to turn off the flash
CAMERA_SLEEP_TIME: Final[float] = 0.01                     # Sleep time between camera cycles

# ----------------------------
# Matcher
# ----------------------------
MATCHER_QUEUE_MAX_SIZE: Final[int] = 100               # Maximum size of the matcher queue
MATCHER_QUEUE_DROP_ON_FULL: Final[bool] = True         # If True, drops the oldest item when the queue is full
MATCHER_SLEEP_TIME: Final[float] = 0.01                # Sleep time in the matcher loop

# ----------------------------
# Color Detection 
# ----------------------------
YOLO_MODEL_PATH: Final[str] = str(Path("yoloModels/yolov8n.pt"))                # Path to YOLO model
COLOR_DETECTION_COLOR: Final[str] = "red"                                       # Color to detect

COLOR_DETECTION_COLORS: Final[dict] = {                                               # HSV color ranges for detection
    "red": {"lower1": [0, 80, 50], "upper1": [10, 255, 255],
            "lower2": [160, 80, 50], "upper2": [180, 255, 255]},    
}                                                                                                               
COLOR_DETECTION_IMG_SIZE: Final[int] = 256                                 # Image size for model input
COLOR_DETECTION_CONF_THRESH: Final[float] = 0.35                           # Confidence threshold for detections
COLOR_DETECTION_IOU_THRESH: Final[float] = 0.45                            # IoU threshold for NMS
COLOR_DETECTION_MIN_BOX_AREA: Final[int] = 100                             # Minimum area of detected bounding boxes
COLOR_DETECTION_THRESH: Final[float] = 0.30                                # Threshold for color detection
COLOR_DETECTION_SLEEP_TIME: Final[float] = 0.01                            # Sleep time between detection cycles
# ----------------------------
# Viewer
# ----------------------------
VIEWER_OVERLAY_ALPHA: Final[float] = 0.45                      # Alpha for overlay transparency
VIEWER_BAR_HEIGHT: Final[int] = 75                             # Height of the telemetry overlay bar
VIEWER_SLEEP_TIME: Final[float] = 0.005                        # Sleep time in the viewer loop
VIEWER_FONT_SIZE: Final[float] = 0.45                          # Font size for overlay text

# ----------------------------
# Robot Dog
# ----------------------------
ROBOT_DOG_SPEED: Final[float] = 0.3                    # Speed in units per second
ROBOT_DOG_REACHED_TOLERANCE: Final[float] = 0.05       # How close to point is considered "reached"
ROBOT_DOG_STEP_DELAY: Final[float] = 0.1               # Sleep time in dog movement loop