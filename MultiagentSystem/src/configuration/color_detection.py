from pathlib import Path
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
"""Absolute path to the project root directory."""

YOLO_MODEL_PATH: Final[Path] = PROJECT_ROOT / "yoloModels" / "yolov8n.pt"
"""Absolute path to the YOLO model file."""

COLOR_DETECTION_COLOR: Final[str] = "red"
"""Target color for detection."""

COLOR_DETECTION_MAX_QUEUE_SIZE: Final[int] = 100
"""Maximum size of the color detection processing queue."""

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
"""Sleep duration (in seconds) between color detection processing cycles."""

