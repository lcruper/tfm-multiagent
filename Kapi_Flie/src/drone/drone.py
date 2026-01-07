"""
Drone Module
------------

Aggregates drone components: telemetry, camera, matcher, color detector, and viewer.
Provides a unified API to start/stop inspections and set callbacks for points detections and inspection finish.
"""

import logging
from typing import Dict, List, Optional, Callable

from interfaces.interfaces import ICamera, ITelemetry, IRobot
from drone.matcher import Matcher
from drone.color_detection import ColorDetection
from drone.viewer import Viewer
from structures.structures import Position, Point2D


class Drone(IRobot):
    """
    Aggregates all drone components.

    Provides a unified interface for inspection, detection and finish callbacks, and
    retrieval of detected points..
    """

    def __init__(self,
                 telemetry: ITelemetry,
                 camera: ICamera,
                 matcher: Matcher,
                 color_detector: ColorDetection,
                 viewer: Viewer) -> None:
        """
        Creates a Drone instance.

        Args:
            telemetry (ITelemetry): Telemetry interface for the drone.
            camera (ICamera): Camera interface for the drone.
            matcher (Matcher): Matcher instance for combining frames and telemetry.
            color_detector (ColorDetection): Color detector instance.
            viewer (Viewer): Viewer instance for displaying frames with telemetry overlay.
        """
        self.telemetry = telemetry
        self.camera = camera
        self.matcher = matcher
        self.color_detector = color_detector
        self.viewer = viewer

        self._detected_points: List[Point2D] = []
        self._active: bool = False

        self._logger = logging.getLogger("Drone")

        self.color_detector.set_callback(self._on_color_detected)
        self.matcher.register_consumer(self.color_detector)
        self.matcher.register_consumer(self.viewer)

    # ---------------------------------------------------
    # Public methods
    # ---------------------------------------------------
    def start_inspection(self) -> None:
        """
        Starts telemetry, camera, matcher, color detector, and viewer.

        Initializes the system and clears previous detections.
        """
        if self._active:
            self._logger.warning("Already running.")
            return

        self._active = True
        self._detected_points.clear()

        self.telemetry.start()
        simulator = getattr(self.telemetry, "simulator", None)
        if simulator:
            simulator.start()
        self.camera.start()
        self.matcher.start()
        self.color_detector.start()
        self.viewer.start()

        self._logger.info("Started.")

    def stop_inspection(self) -> List[Point2D]:
        """
        Stops all subsystems and returns detected points.

        Returns:
            List[Point2D]: Detected 2D points during the inspection.
        """
        if not self._active:
            self._logger.warning("Already stopped.")
            return []

        self._active = False

        self.viewer.stop()
        self.color_detector.stop()
        self.matcher.stop()
        self.camera.stop()
        simulator = getattr(self.telemetry, "simulator", None)
        if simulator:
            simulator.stop()
        self.telemetry.stop()

        if self._callback_onFinish:
            try:
                self._callback_onFinish()
            except Exception as e:
                self._logger.error("Callback onFinish failed: %s", e)

        self._logger.info("Stopped.")
        return self._detected_points.copy()

    def get_current_position(self) -> Optional[Point2D]:
        """
        Returns the current 2D position of the drone.

        Returns:
            Optional[Point2D]: Current (x, y) coordinates. None if unavailable.
        """
        try:
            telemetry = self.telemetry.get_telemetry()
            if telemetry:
                pos = telemetry.pose.position
                return Point2D(pos.x, pos.y)
        except Exception as e:
            self._logger.error("Failed to get current position: %s", e)
        return None
    
    def get_telemetry(self) -> Optional[Dict[str, float]]:
        """
        Retrieves the current telemetry data of the drone. Not implemented.
        
        Returns:
            Optional[Dict[str, float]]: Current telemetry data, or None if unavailable.
        """
        return None

    def get_detected_points(self) -> List[Point2D]:
        """
        Returns the list of detected 2D points.

        Returns:
            List[Point2D]: List of detected (x, y) coordinates.
        """
        return self._detected_points.copy()

    # ---------------------------------------------------
    # Internal methods
    # ---------------------------------------------------
    def _on_color_detected(self, position: Position) -> None:
        """
        Internal callback invoked by ColorDetection when a color object is detected.

        Stores the detection, flashes the camera, and triggers user callback.

        Args:
            position (Position): 3D position of detected object.
        """
        self._logger.debug(
            "Color detected at (%.2f, %.2f, %.2f)", position.x, position.y, position.z
        )

        try:
            self.camera.turn_on_flash()
            self.camera.turn_off_flash()
        except Exception as e:
            self._logger.error("Failed to flash camera: %s", e)

        self._detected_points.append(Point2D(position.x, position.y))

        if self._callback_onPoint:
            try:
                self._callback_onPoint(Point2D(position.x, position.y))
            except Exception as e:
                self._logger.error("Callback onPoint failed: %s", e)
