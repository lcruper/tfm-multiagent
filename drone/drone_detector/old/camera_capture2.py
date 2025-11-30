# camera_capture.py
import cv2
import threading
import logging
from queue import Empty, Queue
from drone_telemetry_listener import DroneTelemetryListener
from structures import FrameWithPosition

class CameraCapture:
    """
    @brief Captures frames from a camera inside the drone LAN
    and associates each frame with the current drone position.

    @note Frames are stored in an internal queue for thread-safe consumption.
    """
    def __init__(self, telemetry_listener: DroneTelemetryListener, max_queue_size: int = 10):
        """
        @brief Constructor.
        
        @param telemetry_listener   DroneTelemetryListener instance for getting current position.
        @param max_queue_size       Maximum number of frames to store in the queue.
        """
        self.telemetry_listener = telemetry_listener
        self.max_queue_size = max_queue_size

        # Camera setup
        self._camera_urls = self._create_camera_urls()      # List of candidate camera stream URLs
        self._active_url = None                             # Currently active camera URL
        self._cap = None                                    # CV2 VideoCapture object
        self._frame_queue = Queue(maxsize=max_queue_size)   # Queue to hold captured frames

        # Threading
        self._running = False                               # Flag to control the background camera capture thread
        self._thread = None                                 # Camera capture thread
        
        # Logger
        self._logger = logging.getLogger("CameraCapture")

    # ----------------------------------------------------------------------
    # Control
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        @brief Starts the background camera capture thread.
        """
        if self._running:
            self._logger.warning("Camera capture already running.")
            return
        
        self._logger.info("Starting camera capture...")
        self._running = True
        self._thread = threading.Thread(target=self._capture, daemon=True)
        self._thread.start()
        self._logger.info("Camera capture started.")

    def stop(self) -> None:
        """
        @brief Stops the camera capture and releases the resources
        """
        if not self._running:
            self._logger.warning("Camera capture already stopped.")
            return
        
        self._logger.info("Stopping camera capture...")
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
    def get_frame(self) -> FrameWithPosition | None:
        """
        @brief Retrieves the next captured frame along with its position.

        @return FrameWithPosition object or None if the queue is empty.
        """
        try:
            return self._frame_queue.get_nowait()
        except Empty:
            return None

    # ----------------------------------------------------------------------
    # Internal methods
    # ----------------------------------------------------------------------
    def _create_camera_urls(self) -> list[str]:
        """
        @brief Creates a list of potential camera stream URLs.

        @return List of camera stream URLs.
        """
        ip_base = self.telemetry_listener.drone_ip
        base_parts = ip_base.split(".")
        base_prefix = ".".join(base_parts[:-1])
        last_octet = int(base_parts[-1])

        self._camera_urls = [
            f"http://{base_prefix}.{last_octet + i}:81/stream"
            for i in range(1, 11)
        ]

    def _check_camera(self, url: str) -> bool:
        """
        @brief  Checks if a camera stream exists at the given URL.

        @param url Camera stream URL.
        @return True if successful, False otherwise.
        """
        self._logger.info(f"Checking camera stream: {url}")
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            self._logger.info(f"Camera stream detected at: {url}")
            return True

        self._logger.warning(f"Camera stream cannot be opened: {url}")
        cap.release()
        return False
    
    def _find_working_camera(self) -> None:
        """
        @brief Searches for a valid camera stream URL.
        """
        self._logger.info("Searching for a working camera stream URL...")
        for url in self._camera_urls:
            if self._check_camera(url):
                self._active_url = url
                self._logger.info(f"Active camera URL set to: {url}")
                return
            
        self._logger.error("No valid camera URLs found.")
        self._cap = None

    def _capture(self) -> None:
        """
        @brief Background camera capture thread.

        Each captured frame is associated with the current drone position and
        pushed into the internal queue.
        """
        # Find a working camera
        while self._running and not self._active_url:
            self._find_working_camera()
            if not self._active_url:
                self._logger.error("Camera not found. Retrying in 1s...")
                threading.Event().wait(1.0)

        # Ensure the active URL is open
        if self._active_url:
            self._check_camera(self._active_url)

        while self._running:
            if not self._cap or not self._cap.isOpened():
                self._logger.warning("Camera feed lost. Reconnecting...")
                self._check_camera(self._active_url)
                threading.Event().wait(0.5)
                continue

            ret, frame = self._cap.read()
            if not ret:
                self._logger.warning("Failed to read frame from camera.")
                continue
            self._logger.debug(f"Captured frame from camera of shape {frame.shape}")

            # Get current drone position 
            position = self.telemetry_listener.get_position()

            # Create FrameWithPosition object
            frame_with_pos = FrameWithPosition(frame=frame, position=position)

            # Add frame with position to queue
            if not self._frame_queue.full():
                self._frame_queue.put(frame_with_pos)
                self._logger.debug(f"Captured frame at position: x={position.x:.2f}, y={position.y:.2f}, z={position.z:.2f}")
            else:
                self._logger.warning("Frame queue full. Dropping frame.")
