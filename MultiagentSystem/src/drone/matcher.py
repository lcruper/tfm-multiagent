from configuration import matcher as config
import threading
import logging
from time import sleep
from typing import List, Optional

from interfaces.interfaces import ICamera, AFrameConsumer, ITelemetry
from structures.structures import FrameWithTelemetry

class Matcher:
    """
    Synchronizes camera frames with drone telemetry and distributes them to registered consumers.

    The class continuously retrieves frames from a camera provider and telemetry data 
    from a telemetry provider. Each frame is associated with the exact telemetry data at the 
    moment of capture, forming a FrameWithTelemetry object. These objects are then distributed 
    to all registered consumers (instances of AFrameConsumer).
    """
    def __init__(self, telemetry: ITelemetry, camera: ICamera) -> None:
        """
        Creates a Matcher instance.

        Args:
            telemetry (ITelemetry): Telemetry provider.
            camera (ICamera): Camera provider.
        """
        self._telemetry: ITelemetry = telemetry
        self._camera: ICamera = camera

        self._consumers: List[AFrameConsumer] = []

        self._running: bool = False
        self._thread: Optional[threading.Thread] = None

        self._logger: logging.Logger = logging.getLogger("Matcher")

    # ----------------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        Starts the background matcher thread.

        The thread continuously retrieves frames and telemetry, creates FrameWithTelemetry objects,
        and dispatches them to all registered consumers.
        """
        if self._running:
            self._logger.warning("Already running.")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._match, daemon=True)
        self._thread.start()
        self._logger.info("Started.")

    def stop(self) -> None:
        """
        Stops the background matcher thread.
        """
        if not self._running:
            self._logger.warning("Already stopped.")
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            if self._thread.is_alive():
                self._logger.warning("Did not stop in time.")
            self._thread = None
        self._logger.info("Stopped.")

    def register_consumer(self, consumer: AFrameConsumer) -> None:
        """
        Registers a new consumer to receive FrameWithTelemetry objects.

        Args:
            consumer (IFrameConsumer): Consumer to register.
        """
        if consumer in self._consumers:
            self._logger.warning(
                "Consumer %s already registered.",
                type(consumer).__name__
            )
            return
        self._consumers.append(consumer)
        self._logger.info("Registered consumer: %s", type(consumer).__name__)

    # ----------------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------------
    def _match(self) -> None:
        """
        Background thread method that combines frames with telemetry and sends them to consumers.

        Retrieves a frame from the camera and telemetry from the telemetry provider,
        creates a FrameWithTelemetry object, and enqueues it to all registered consumers. 
        """
        while self._running:
            frame = self._camera.get_frame()
            if frame is None:
                sleep(config.MATCHER_SLEEP_TIME)
                continue
            self._logger.debug("Retrieved frame of shape %s", frame.data.shape)

            telemetry = self._telemetry.get_telemetry()
            self._logger.debug("Retrieved telemetry: %s", telemetry)

            fwt = FrameWithTelemetry(frame, telemetry)
            self._logger.debug(
                "Matched frame of shape %s with telemetry %s",
                frame.data.shape, telemetry
            )

            for consumer in self._consumers:
                try:
                    consumer.enqueue(fwt)
                except Exception as e:
                    self._logger.error(
                        "Error sending to consumer %s: %s",
                        type(consumer).__name__, e
                    )

            sleep(config.MATCHER_SLEEP_TIME)
