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
    Captures frames from a camera web server and provides access to the latest frame.

    This class connects to the camera via a HTTP-based stream, retrieves video frames continuously
    in a background thread, and maintains the most recent frame in a thread-safe manner. Additionally,
    it supports controlling the integrated camera flash through HTTP requests.
    """

    def __init__(self, stream_url: str, flash_url: str) -> None:
        """
        Creates a CameraCapture instance.

        Args:
            stream_url (str): HTTP URL of the camera video stream.
            flash_url (str):  HTTP URL for controlling the camera flash.
        """
        self._stream_url: str = stream_url
        self._flash_url: str = flash_url 

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
        """
        Starts the background thread to capture frames from the camera stream.

        The thread creates an OpenCV VideoCapture object that continuously reads frames from the stream URL,
        decodes them, and updates the last available frame in a thread-safe manner.
        """
        if self._running:
            self._logger.warning("Already running.")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._capture, daemon=True)
        self._thread.start()
        self._logger.info("Started.")

    def stop(self) -> None:
        """
        Stops the background capture thread and releases resources.

        Signals the thread to stop, waits briefly for termination, and releases the OpenCV
        VideoCapture object. Ensures that the capture process is safely terminated even
        in case of errors.
        """
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
        Returns a deep copy of the latest captured frame.

        The returned frame is safe for concurrent access from multiple threads.

        Returns:
            Optional[Frame]: The latest captured frame, or None if unavailable.
        """
        with self._lock:
            return deepcopy(self._frame)

    def turn_on_flash(self) -> None:
        """
        Activates the camera's integrated flash.

        Sends an HTTP GET request to the camera's flash control with a predefined intensity value.
        """
        try:
            requests.get(
                self._flash_url,
                params={"var": "led_intensity", "val": config.CAMERA_FLASH_INTENSITY_ON},
                timeout=config.CAMERA_REQUEST_TIMEOUT
            )
            self._logger.debug("Flash turned on.")
        except Exception:
            self._logger.warning("Failed to turn on flash.")

    def turn_off_flash(self) -> None:
        """
        Deactivates the camera's integrated flash.

        Sends an HTTP GET request to the camera's flash control endpoint with the intensity set to zero.
        """
        try:
            requests.get(
                self._flash_url,
                params={"var": "led_intensity", "val": config.CAMERA_FLASH_INTENSITY_OFF},
                timeout=config.CAMERA_REQUEST_TIMEOUT
            )
            self._logger.debug("Flash turned off.")
        except Exception:
            self._logger.warning("Failed to turn off flash.")

    # ----------------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------------
    def _update_frame(self, data: ndarray) -> None:
        """
        Updates the latest captured frame in a thread-safe manner.

        Encapsulates the raw frame array into a Frame object and stores it as the
        most recent frame.

        Args:
            data (ndarray): Raw frame data captured from the camera stream.
        """
        with self._lock:
            self._frame = Frame(data=data)
        self._logger.debug("Updated frame.")

    def _open_stream(self) -> bool:
        """
        Opens a connection to the camera's video stream URL.

        Uses OpenCV's VideoCapture to attempt opening the stream. If successful,
        stores the VideoCapture object internally; otherwise releases resources
        and returns False.

        Returns:
            bool: True if the stream was successfully opened, False otherwise.
        """
        if self._cap:
            self._cap.release()
            self._cap = None

        cap = cv2.VideoCapture(self._stream_url)
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
        Background thread that continuously captures and stores frames.

        Repeatedly reads frames from the video stream. On failure to read or open
        the stream, retries after a configurable delay. Successfully captured frames
        are decoded, wrapped in a Frame object, and stored as the latest frame.
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
            self._update_frame(data)
            sleep(config.CAMERA_SLEEP_TIME)

        if self._cap:
            self._cap.release()
            self._cap = None
