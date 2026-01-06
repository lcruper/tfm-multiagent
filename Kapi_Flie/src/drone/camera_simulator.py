"""
Camera Simulator Module
-----------------------

This module simulates a camera that captures colored stop signs.

The stop signs are octagons with "STOP" text at the center. Each frame is generated 
with a random position, size, and color. The simulator can produce frames at a 
configurable period, and can optionally generate stop signs of the configured target color.
"""

import logging
import numpy as np
import cv2
import time
from typing import Optional
import threading
from copy import deepcopy

from configuration import camera_simulator as config
from configuration import color_detection as config_color_detection
from interfaces.interfaces import ICamera
from structures.structures import Frame


class CameraSimulator(ICamera):
    """
    Simulated camera producing frames with stop signs.
    """

    def __init__(self, stream_url: str, flash_url: str) -> None:
        """
        Creates a CameraSimulator instance.

        Args:
            stream_url (str): Stream URL (not used in simulator).
            flash_url (str): Flash control URL (not used in simulator).
        """
        self._frame: Optional[Frame] = None
        self._frame_time: float = 0.0

        self._lock: threading.Lock = threading.Lock()
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None

        self._logger: logging.Logger = logging.getLogger("CameraSimulator")

    # ----------------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """Starts the background thread to capture frames."""
        if self._running:
            self._logger.warning("Already running.")
            return

        self._running = True
        self._frame = None
        self._frame_time = 0.0
        self._thread = threading.Thread(target=self._generate, daemon=True)
        self._thread.start()
        self._logger.info("Started.")

    def stop(self) -> None:
        """Stops the background capture thread and clears the last frame ."""
        if not self._running:
            self._logger.warning("Already stopped.")
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            if self._thread.is_alive():
                self._logger.warning("Did not stop in time")
            self._thread = None
        self._frame = None

    def get_frame(self) -> Optional[Frame]:
        """
        Returns a copy of the latest generated frame.

        Returns:
            Frame: Latest generated from the camera. None if no frame is available.
        """
        with self._lock:
            return deepcopy(self._frame)

    def turn_on_flash(self) -> None:
        """Simulates turning on the camera flash (no-op)."""
        pass

    def turn_off_flash(self) -> None:
        """Simulates turning off the camera flash (no-op)."""
        pass

    # ----------------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------------
    def _generate_new_frame(self) -> Frame:
        """
        Generates a new frame with a stop sign.
        
        Returns:
            Frame: Generated frame with a stop sign.
        """
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        size = np.random.randint(config.CAMERA_SIMULATOR_MIN_RADIUS, config.CAMERA_SIMULATOR_MAX_RADIUS)
        center = (np.random.randint(size, 640 - size), np.random.randint(size, 480 - size))
        if np.random.rand() < config.CAMERA_SIMULATOR_COLOR_PROBABILITY:
            color = config.CAMERA_SIMULATOR_COLOR_DICT[config_color_detection.COLOR_DETECTION_COLOR]
        else:
            color = tuple(np.random.randint(0, 256, size=3).tolist())
        self._draw_stop_sign(image, center, size, color)
        return Frame(data=image)

    def _draw_stop_sign(self, image: np.ndarray, center: tuple[int, int], size: int, color: tuple[int, int, int]) -> None:
        """
        Draws a stop sign (octagon with 'STOP') on the image.

        Args:
            image (np.ndarray): Image where the stop sign will be drawn.
            center (tuple[int, int]): (x, y) coordinates of the stop sign center.
            size (int): Approximate size/radius of the stop sign.
            color (tuple[int, int, int]): BGR color of the stop sign.
        """
        octagon = []
        for i in range(8):
            angle_deg = 22.5 + i * 45
            angle_rad = np.deg2rad(angle_deg)
            x = int(center[0] + size * np.cos(angle_rad))
            y = int(center[1] + size * np.sin(angle_rad))
            octagon.append((x, y))
        cv2.fillPoly(image, [np.array(octagon)], color)
        font_scale = size / 60
        thickness = max(1, int(size / 15))
        text_size = cv2.getTextSize("STOP", cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
        text_x = center[0] - text_size[0] // 2
        text_y = center[1] + text_size[1] // 2
        cv2.putText(image, "STOP", (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

    def _generate(self) -> Frame:
        """
        Background thread that generates frames with stop signs if the frame is older than CAMERA_SIMULATOR_FRAME_PERIOD.
        """
        while self._running:
            now = time.time()
            if self._frame is None or now - self._frame_time >= config.CAMERA_SIMULATOR_FRAME_PERIOD:
                frame = self._generate_new_frame()
                with self._lock:
                    self._frame = frame
                    self._frame_time = now
            time.sleep(config.CAMERA_SIMULATOR_SLEEP_TIME)