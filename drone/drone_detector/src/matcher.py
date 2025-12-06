# matcher.py
import threading
import logging

from queue import Queue, Empty, Full
from time import sleep
from structures import FrameWithTelemetry
from drone_telemetry_listener import DroneTelemetryListener
from camera_capture import CameraCapture

class Matcher:
    """
    @brief Associates frames from a camera with the drone's telemetry data.

    Captures camera frames and drone telemetry data, combines them into FrameWithTelemetry objects,
    and distributes them to multiple registered consumer queues.
    """
    def __init__(self, drone_telemetry: DroneTelemetryListener, camera_capture: CameraCapture) -> None:
        """
        @brief Constructor.

        @param drone_telemetry DroneTelemetryListener object
        @param camera_capture CameraCapture object
        """
        self.drone: DroneTelemetryListener = drone_telemetry
        self.camera: CameraCapture = camera_capture

        # Queues for distributing FrameWithTelemetry objects to consumers
        self._queues: list[Queue] = []     

        # Threading
        self._running: bool = False             # Flag to control the background matcher thread
        self._thread: threading.Thread = None   # Matcher thread
        
        # Logger
        self._logger: logging.Logger = logging.getLogger("Matcher")
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
            if self._thread.is_alive():
                self._logger.warning("Matcher thread didn't stop in time")
            self._thread = None
        self._logger.info("Matcher stopped.")

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    def register_consumer(self, queue: Queue):
        """
        @brief Registers a consumer queue to receive FrameWithTelemetry objects.

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
            frame = self.camera.get_frame()
            if frame is None:
                sleep(0.01)
                continue
            self._logger.debug("Retrieved frame of shape %s", frame.data.shape)

            # Get drone telemetry
            telemetry = self.drone.get_telemetry()
            self._logger.debug("Retrieved telemetry %s", telemetry)
            # Create FrameWithTelemetry object
            fwt = FrameWithTelemetry(frame, telemetry)
            self._logger.debug("Matched frame of shape %s with telemetry %s", frame.data.shape, telemetry)

            # Distribute to all consumer queues
            for q in self._queues:
                try:
                    q.put_nowait(fwt)
                except Full:
                    try:
                        q.get_nowait()
                    except Empty:
                        pass
                    q.put_nowait(fwt)

            sleep(0.01)  