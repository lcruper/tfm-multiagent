"""
Camera Capture Module
---------------------

This module implements a camera interface that captures frames from a stream URL and maintains
the latest frame in a thread-safe. It also allows turning the camera flash on and off.
"""

from typing import Optional
from configuration import camera_capture as config
import cv2
import threading
import logging
import requests
from time import sleep
from copy import deepcopy
from numpy import ndarray

from interfaces.interfaces import ICamera
from structures.structures import Frame


class CameraCapture(ICamera):
    """
    Captures frames from a camera stream URL.

    Maintains the camera open, updates the last captured frame and supports flash control.
    """

    def __init__(self, stream_url: str, flash_url: str) -> None:
        """
        Creates a CameraCapture instance.

        Args:
            stream_url (str): URL of the camera stream.
            flash_url (str): URL to control the camera flash.
        """
        self.stream_url: str = stream_url
        self.flash_url: str = flash_url 

        self._frame: Optional[Frame] = None

        self._cap: Optional[cv2.VideoCapture] = None

        self._lock: threading.Lock = threading.Lock()
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None

        self._logger: logging.Logger = logging.getLogger("CameraCapture")

    # ----------------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """Starts the background thread to capture frames."""
        if self._running:
            self._logger.warning("Already running.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._capture, daemon=True)
        self._thread.start()
        self._logger.info("Started.")

    def stop(self) -> None:
        """Stops the background capture thread and releases the camera."""
        if not self._running:
            self._logger.warning("Already stopped.")
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            if self._thread.is_alive():
                self._logger.warning("Did not stop in time")
            self._thread = None

        if self._cap:
            try:
                self._cap.release()
            except Exception:
                self._logger.exception("Error releasing VideoCapture")
            finally:
                self._cap = None

        self._logger.info("Stopped.")

    def get_frame(self) -> Optional[Frame]:
        """
        Returns a copy of the latest captured frame.

        Returns:
            Frame: Latest frame captured from the camera. None if no frame is available.
        """
        with self._lock:
            return deepcopy(self._frame)

    def turn_on_flash(self) -> None:
        """Turns on the camera flash if supported."""
        try:
            requests.get(
                self.flash_url,
                params={"var": "led_intensity", "val": config.CAMERA_FLASH_INTENSITY_ON},
                timeout=config.CAMERA_REQUEST_TIMEOUT
            )
            self._logger.debug("Flash turned on.")
        except Exception:
            self._logger.warning("Failed to turn on flash.")

    def turn_off_flash(self) -> None:
        """Turns off the camera flash if supported."""
        try:
            requests.get(
                self.flash_url,
                params={"var": "led_intensity", "val": config.CAMERA_FLASH_INTENSITY_OFF},
                timeout=config.CAMERA_REQUEST_TIMEOUT
            )
            self._logger.debug("Flash turned off.")
        except Exception:
            self._logger.warning("Failed to turn off flash.")

    # ----------------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------------
    def _process_frame(self, data: ndarray) -> None:
        """
        Processes a frame and updates the latest frame safely.

        Args:
            data (ndarray): Raw image frame captured from the camera.
        """
        with self._lock:
            self._frame = Frame(data=data)
        self._logger.debug("Updated frame.")

    def _open_stream(self) -> bool:
        """
        Attempts to open the camera stream URL.

        Returns:
            bool: True if the stream was successfully opened, False otherwise.
        """
        if self._cap:
            self._cap.release()
            self._cap = None

        cap = cv2.VideoCapture(self.stream_url)
        if cap.isOpened():
            self._cap = cap
            self._logger.info("Stream URL opened successfully.")
            return True
        else:
            self._logger.warning("Failed to open stream URL.")
            cap.release()
            return False

    def _capture(self) -> None:
        """
        Background thread that continuously captures frames from the stream.
        """
        while self._running:
            if not self._cap or not self._cap.isOpened():
                if not self._open_stream():
                    sleep(config.CAMERA_STREAM_RETRY_DELAY)
                    continue

            ret, data = self._cap.read()
            if not ret:
                self._logger.warning("Failed to read frame. Retrying...")
                sleep(config.CAMERA_STREAM_RETRY_DELAY)
                continue

            self._logger.debug("Frame captured of size %s", data.shape)
            self._process_frame(data)
            sleep(config.CAMERA_SLEEP_TIME)

        if self._cap:
            self._cap.release()
            self._cap = None
