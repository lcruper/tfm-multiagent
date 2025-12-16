import numpy as np
import cv2
import time
from interfaces.interfaces import ICamera
from structures.structures import Frame


class CameraSimulator(ICamera):
    """
    Simulated camera that generates images with red objects.
    """

    def __init__(self, stream_url: str, flash_url: str) -> None:
        self._running = False

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False

    def get_frame(self) -> Frame:
        if not self._running:
            return None

        # Black background
        image = np.zeros((480, 640, 3), dtype=np.uint8)

        if (np.random.rand() < 0.3):
            # Random red circle
            center = (
                np.random.randint(100, 640 - 100),
                np.random.randint(100, 480 - 100)
            )
            radius = np.random.randint(30, 100)

            cv2.circle(
                image,
                center,
                radius,
                (0, 0, 255),  # 🔴 RED in BGR
                -1
            )

        time.sleep(1)
        return Frame(image)

    def turn_on_flash(self) -> None:
        pass

    def turn_off_flash(self) -> None:
        pass
