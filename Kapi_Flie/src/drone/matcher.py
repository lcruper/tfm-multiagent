# matcher.py
"""
@file matcher.py
@brief Combines camera frames and telemetry into FrameWithTelemetry objects.
"""
import config
import threading
import logging
from time import sleep
from typing import List, Optional

from interfaces.interfaces import ICamera, IFrameConsumer, ITelemetry
from structures.structures import FrameWithTelemetry

class Matcher:
    """
    @brief Associates frames from a camera with telemetry data.

    Captures camera frames and telemetry data, combines them into FrameWithTelemetry objects,
    and distributes them to multiple registered consumer queues.
    """
    def __init__(self, 
                 telemetry: ITelemetry, 
                 camera: ICamera) -> None:
        """
        @brief Constructor.

        @param telemetry ITelemetry object
        @param camera ICamera object
        """
        self.telemetry: ITelemetry = telemetry
        self.camera: ICamera = camera

        # Consumers for distributing FrameWithTelemetry objects
        self._consumers: List[IFrameConsumer] = []

        # Threading
        self._running: bool = False                                 # Flag to control the background matcher thread
        self._thread: Optional[threading.Thread] = None             # Matcher thread
        
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
    def register_consumer(self, consumer: IFrameConsumer):
        """
        @brief Registers a consumer to receive FrameWithTelemetry objects.

        @param consumer IFrameConsumer object to receive matched frames
        """
        self._consumers.append(consumer)
        self._logger.info("Registered consumer: %s", type(consumer).__name__)
    
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
                sleep(config.MATCHER_SLEEP_TIME)
                continue
            self._logger.debug("Retrieved frame of shape %s", frame.data.shape)

            # Get telemetry
            telemetry = self.telemetry.get_telemetry()
            self._logger.debug("Retrieved telemetry %s", telemetry)
            # Create FrameWithTelemetry object
            fwt = FrameWithTelemetry(frame, telemetry)
            self._logger.debug("Matched frame of shape %s with telemetry %s", frame.data.shape, telemetry)

            # Distribute to all consumers
            for consumer in self._consumers:
                try:
                    consumer.enqueue(fwt)
                except Exception as e:
                    self._logger.error("Error sending to consumer %s: %s", type(consumer).__name__, e)

            sleep(config.MATCHER_SLEEP_TIME)  