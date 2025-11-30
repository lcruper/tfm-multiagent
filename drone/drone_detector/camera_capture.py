# camera_capture.py
import cv2
import threading
import logging

from time import sleep
from copy import deepcopy
from numpy import ndarray
from structures import Frame

class CameraCapture:
    """
    @brief Captures frames from a stream URL.

    Maintains the camera open, updates the last captured frame thread-safe, 
    and can recover if the stream temporarily fails.
    """
    RETRY_DELAY = 1.0  # Seconds to wait before retrying to open the stream if it fails.
    
    def __init__(self, stream_url: str) -> None:
        """
        @brief Constructor.

        @param stream_url URL of the stream.
        """
        self.stream_url = stream_url

        self._cap = None        # cv2.VideoCapture object
        self._frame = None      # Last captured frame

        # Threading
        self._lock = threading.Lock()   # Lock for thread-safe access to latest frame
        self._running = False           # Flag to control the background frames capture thread
        self._thread = None             # Frames capture thread

        # Logger
        self._logger = logging.getLogger("CameraCapture")

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
            self._thread = None
        if self._cap:
            self._cap.release()
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

    # ----------------------------------------------------------------------
    # Internal methods
    # ----------------------------------------------------------------------
    def _process_frame(self, frame: ndarray) -> None:
        """
        @brief Processes a frame and updates the latest frame.

        @param frame A frame
        """
        with self._lock:
            self._frame = Frame(data=frame)
        self._logger.debug(f"Updated frame")

    def _open_stream(self) -> bool:
        """
        @brief Attempts to open the stream URL.

        @return bool True if the stream was opened successfully, False otherwise.
        """
        if self._cap:
            self._cap.release()
            self._cap = None

        self._logger.info(f"Opening stream URL: {self.stream_url}")
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
                    sleep(self.RETRY_DELAY)
                    continue

            # Capture frame
            ret, frame = self._cap.read()
            if not ret:
                self._logger.warning("Failed to read frame. Retrying...")
                sleep(self.RETRY_DELAY)
                continue

            self._logger.debug(f"Frame captured of size {frame.shape}")

            # Process frame
            self._process_frame(frame)
            sleep(0.01)

        # Release capture on exit
        self._cap.release()
        self._cap = None