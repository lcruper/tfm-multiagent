from typing import Final

CAMERA_STREAM_URL: Final[str] = "http://192.168.43.44:81/stream"
"""URL of the camera video stream."""

CAMERA_FLASH_URL: Final[str] = CAMERA_STREAM_URL.replace("81/stream", "80/control")
"""URL to control the camera flash."""

CAMERA_STREAM_RETRY_DELAY: Final[float] = 5.0
"""Delay before retrying to open the camera stream (in seconds)."""

CAMERA_REQUEST_TIMEOUT: Final[float] = 1.0
"""Timeout for camera HTTP requests (in seconds)."""

CAMERA_FLASH_INTENSITY_ON: Final[int] = 25
"""Flash intensity used to turn the camera flash ON."""

CAMERA_FLASH_INTENSITY_OFF: Final[int] = 0
"""Flash intensity used to turn the camera flash OFF."""

CAMERA_SLEEP_TIME: Final[float] = 0.01
"""Sleep duration (in seconds) between camera processing cycles."""