# camera_capture.py
from typing import Optional
import config
import cv2
import threading
import logging
import requests
from time import sleep
from copy import deepcopy
from numpy import ndarray

from structures.structures import Frame

class CameraCapture:
    """
    @brief Captures frames from a stream URL.

    Maintains the camera open, updates the last captured frame thread-safe, 
    and can recover if the stream temporarily fails.
    """

    def __init__(self, stream_url: str) -> None:
        """
        @brief Constructor.

        @param stream_url URL of the stream.
        """
        self.stream_url: str = stream_url
        self._flash_url: str = stream_url.replace(":81/stream", ":80/control")

        self._cap: Optional[cv2.VideoCapture] = None      # cv2.VideoCapture object
        self._frame: Optional[Frame] = None               # Last captured frame

        # Threading
        self._lock: threading.Lock = threading.Lock()           # Lock for thread-safe access to latest frame
        self._running: bool = False                             # Flag to control the background frames capture thread
        self._thread: Optional[threading.Thread] = None         # Frames capture thread

        # Logger
        self._logger: logging.Logger = logging.getLogger("CameraCapture")
    
    # ----------------------------------------------------------------------
    # Control
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        @brief Starts the frames capture thread.
        """
        if self._running:
            self._logger.warning("CameraCapture already running.")
            return

        self._logger.info(f"Starting frames capture...")
        self._running = True
        self._thread = threading.Thread(target=self._capture, daemon=True)
        self._thread.start()
        self._logger.info("Frames capture started.")

    def stop(self) -> None:
        """
        @brief Stops the frames capture thread and releases resources.
        """
        if not self._running:
            self._logger.warning("Frames capture already stopped.")
            return

        self._logger.info("Stopping frames capture...")
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            if self._thread.is_alive():
                self._logger.warning("Frame capture thread didn't stop in time")
            self._thread = None
        if self._cap:
            try:
                self._cap.release()
            except Exception:
                self._logger.exception("Error releasing VideoCapture")
            finally:
                self._cap = None
        self._logger.info("Camera capture stopped.")

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    def get_frame(self) -> Frame:
        """
        @brief Returns a copy of the latest captured frame.

        @return Frame A new Frame object with the last captured frame.
        """
        with self._lock:
            return deepcopy(self._frame)
        
    def turn_on_flash(self) -> None:
        """
        @brief Turns on the camera flash if supported.
        """
        try:
            requests.get(
                self._flash_url, 
                params={"var": "led_intensity", "val": config.CAMERA_FLASH_INTENSITY_ON}, 
                timeout=config.CAMERA_STREAM_OPEN_TIMEOUT
                )
            self._logger.debug("Flash turned on.")
        except:
            pass

    def turn_off_flash(self) -> None:
        """
        @brief Turns off the camera flash if supported. 
        """
        try:
            requests.get(
                self._flash_url, 
                params={"var": "led_intensity", "val": config.CAMERA_FLASH_INTENSITY_OFF}, 
                timeout=config.CAMERA_STREAM_OPEN_TIMEOUT
                )
            self._logger.debug("Flash turned off.")
        except:
            pass

    # ----------------------------------------------------------------------
    # Internal methods
    # ----------------------------------------------------------------------
    def _process_frame(self, data: ndarray) -> None:
        """
        @brief Processes a frame and updates the latest frame.

        @param data A frame
        """
        with self._lock:
            self._frame = Frame(data=data)
        self._logger.debug(f"Updated frame")

    def _open_stream(self) -> bool:
        """
        @brief Attempts to open the stream URL.

        @return bool True if the stream was opened successfully, False otherwise.
        """
        if self._cap:
            self._cap.release()
            self._cap = None

        self._logger.info("Opening stream URL %s", self.stream_url)
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
        @brief Background frames capture thread.
        """
        while self._running:
            if not self._cap or not self._cap.isOpened():
                if not self._open_stream():
                    sleep(config.CAMERA_STREAM_RETRY_DELAY)
                    continue

            # Capture frame
            ret, data = self._cap.read()
            if not ret:
                self._logger.warning("Failed to read frame. Retrying...")
                sleep(config.CAMERA_STREAM_RETRY_DELAY)
                continue

            self._logger.debug("Frame captured of size %s", data.shape)

            # Process frame
            self._process_frame(data)
            sleep(config.CAMERA_SLEEP_TIME)

        # Release capture on exit
        self._cap.release()
        self._cap = None