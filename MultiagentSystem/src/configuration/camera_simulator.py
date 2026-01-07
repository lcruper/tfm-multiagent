from typing import Final

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
"""Sleep duration (in seconds) between camera simulator cycles."""
