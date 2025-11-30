# matcher.py
import threading
import logging

from queue import Queue, Empty, Full
from structures import FrameWithPosition
from time import sleep

class Matcher:
    """
    @brief Associates frames from a camera with the drone's position.

    Captures frames and drone positions, combines them into FrameWithPosition objects,
    and distributes them to multiple registered consumer queues.
    """
    DEFAULT_PORT = 81       # Default port for stream capture
    MAX_IP_TRIES = 5        # Maximum number of tries to get stream URL
    REQUEST_TIMEOUT = 0.5   # Timeout for HTTP requests in seconds

    def __init__(self, drone_telemetry, camera_capture) -> None:
        """
        @brief Constructor.

        @param drone_telemetry DroneTelemetryListener object
        @param camera_capture CameraCapture object
        """
        self.drone = drone_telemetry
        self.camera = camera_capture

        # Queues for distributing FrameWithPosition objects to consumers
        self._queues = []     

        # Threading
        self._running = False   # Flag to control the background matcher thread
        self._thread = None     # Matcher thread
        
        # Logger
        self._logger = logging.getLogger("Matcher")

    # ----------------------------------------------------------------------
    # Control
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        @brief Starts the matcher thread.
        """
        if self._running:
            self._logger.warning("Matcher already running.")
            return
        
        self._logger.info(f"Starting matcher...")
        self._running = True
        self._thread = threading.Thread(target=self._match, daemon=True)
        self._thread.start()
        self._logger.info("Matcher started.")

    def stop(self) -> None:
        """
        @brief Stops the matcher thread and cleans up resources.
        """
        if not self._running:
            self._logger.warning("Matcher already stopped.")
            return
        
        self._logger.info("Stopping matcher...")
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        self._logger.info("Matcher stopped.")

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    def register_consumer(self, queue: Queue):
        """
        @brief Registers a consumer queue to receive FrameWithPosition objects.

        @param queue Queue object where matched frames will be sent
        """
        self._queues.append(queue)

    # ----------------------------------------------------------------------
    # Internal methods
    # ----------------------------------------------------------------------    
    def _match(self):
        """
        @brief Background matcher thread.
        """
        while self._running:
            # Get camera frame
            frame= self.camera.get_frame()
            if frame is None:
                sleep(0.01)
                continue

            # Get drone position
            position = self.drone.get_position()

            # Create FrameWithPosition object
            fwp = FrameWithPosition(frame, position)
            self._logger.debug(f"Matched frame of shape {frame.data.shape} with position {position}")

            # Distribute to all consumer queues
            for q in self._queues:
                try:
                    q.put_nowait(fwp)
                except Full:
                    try:
                        q.get_nowait()
                    except Empty:
                        pass
                    q.put_nowait(fwp)

            sleep(0.01)  