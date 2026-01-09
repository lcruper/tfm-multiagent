import logging
import numpy as np
import cv2
import time
from typing import Optional
from time import time
from copy import deepcopy

from configuration import camera_simulator as config
from interfaces.interfaces import ICamera
from structures.structures import Frame


class CameraSimulator(ICamera):
    """
    Simulated camera producing synthetic frames with colored stop signs.

    This class provides on-demand generation of frames containing a colored stop sign over a black background.  
    The color can be forced to a target color with a specific probability 
    to facilitate evaluation of color-based detection algorithms.
    """

    def __init__(self) -> None:
        """
        Creates a CameraSimulator instance.
        """
        self._frame: Optional[Frame] = None
        self._frame_time: float = 0.0

        self._active: bool = False
        self._logger: logging.Logger = logging.getLogger("CameraSimulator")

    # ----------------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        Starts the simulator.
        
        Sets the simulator to an active state and resets the last generated frame and its timestamp.
        """
        if self._active:
            self._logger.warning("Already running.")
            return
        
        self._frame = None
        self._frame_time = 0.0
        self._active = True
        self._logger.info("Started.")

    def stop(self) -> None:
        """Stops the simulator.

        Clears the last generated frame and its timestamp and marks the simulator as inactive.
        """
        if not self._active:
            self._logger.warning("Already stopped.")
            return
        
        self._active = False
        self._frame = None
        self._frame = None

    def get_frame(self) -> Optional[Frame]:
        """
        Returns a copy of a new generated frame or the last one if within the frame period.

        Generates a new frame only if the minimum frame period has elapsed 
        since the last generation. In that case, the generated frame is stored.
        Otherwise, returns a copy of the previously generated frame.

        Returns:
            Frame: generated frame, or None if the simulator is not active.
        """
        if not self._active:
            return None
        
        now = time()
        if now - self._frame_time >= config.CAMERA_SIMULATOR_FRAME_PERIOD:
            frame = self._generate_new_frame()
            self._frame = frame
            self._frame_time = now
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
        Generates a frame containing a stop sign.

        The stop sign is drawn as an octagon with the word "STOP" centered. 
        The position and size are random within predefined ranges, and the color of the stop sign is randomized according 
        to the configuration parameters.

        Returns:
            Frame: A  Frame instance containing the generated stop sign image.
        """
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        size = np.random.randint(config.CAMERA_SIMULATOR_MIN_RADIUS, config.CAMERA_SIMULATOR_MAX_RADIUS)
        center = (np.random.randint(size, 640 - size), np.random.randint(size, 480 - size))
        if np.random.rand() < config.CAMERA_SIMULATOR_COLOR_PROBABILITY:
            color = config.CAMERA_SIMULATOR_COLOR_DICT[config.CAMERA_SIMULATOR_TARGET_COLOR]
        else:
            color = tuple(np.random.randint(0, 256, size=3).tolist())

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
        return Frame(data=image)