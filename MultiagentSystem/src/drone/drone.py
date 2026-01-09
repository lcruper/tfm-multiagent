import logging
from typing import Dict, List, Optional

from interfaces.interfaces import ICamera, ITelemetry, ARobot
from drone.matcher import Matcher
from drone.color_detection import ColorDetection
from drone.viewer import Viewer
from structures.structures import Position, Point2D

class Drone(ARobot):
    """
    Central integration module of the drone.

    The class acts as the core coordinator of the drone,
    aggregating and managing all the main components of the exploration
    agent: telemetry, camera, data synchronization, visual processing,
    and visualization.

    It provides a high-level unified API to start and stop the exploration
    routine, as well as to notify user-defined callbacks when relevant
    events occur, such as the detection of points of interest or the
    completion of the exploration routine.
    """

    def __init__(self,
                 telemetry: ITelemetry,
                 camera: ICamera,
                 color_detection: ColorDetection
                 ) -> None:
        """
        Creates a Drone instance.

        Initializes the different componentes: a Matcher and Viewer objects are created, 
        the color detection and visualization modules are registered as frame consumers, 
        and an internal callback is set to handle visual detections.

        Args:
            telemetry (ITelemetry): Telemetry provider used to obtain the drone state.
            camera (ICamera): Camera provider used to capture image frames.
            color_detection (ColorDetection): Module responsible for visual color detection.
        """
        self._telemetry = telemetry
        self._camera = camera
        self._matcher = Matcher(self._telemetry, self._camera)
        self._color_detection = color_detection
        self._viewer = Viewer()

        self._detected_points: List[Point2D] = []
        self._active: bool = False

        self._logger = logging.getLogger("Drone")

        self._color_detection.set_callback(self._on_color_detected)
        self._matcher.register_consumer(self._color_detection)
        self._matcher.register_consumer(self._viewer)

    # ---------------------------------------------------
    # Public methods
    # ---------------------------------------------------
    def start_routine(self) -> None:
        """
        Starts the exploration routine.

        This method initializes and starts all the system subcomponents in
        a coordinated manner: telemetry acquisition, camera capture, frame/
        telemetry synchronization, visual color detection, and visualization.

        Before starting, the list of detected points is cleared.
        """
        if self._active:
            self._logger.warning("Already running.")
            return

        self._active = True
        self._detected_points.clear()
        self._telemetry.start()
        self._camera.start()
        self._matcher.start()
        self._color_detection.start()
        self._viewer.start()

        self._logger.info("Started.")

    def stop_routine(self) -> List[Point2D]:
        """
        Stops the exploration routine and all associated subcomponents.

        The subsystems are stopped in an orderly manner. Once the routine
        finishes, the user-defined completion callback is invoked, if it
        has been registered.

        Returns:
            List[Point2D]: Detected 2D points during the exploration routine.
        """
        if not self._active:
            self._logger.warning("Already stopped.")
            return []

        self._active = False
        self._viewer.stop()
        self._color_detection.stop()
        self._matcher.stop()
        self._camera.stop()
        self._telemetry.stop()

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
            telemetry = self._telemetry.get_telemetry()
            if telemetry:
                pos = telemetry.pose.position
                return Point2D(pos.x, pos.y)
        except Exception as e:
            self._logger.error("Failed to get current position: %s", e)
        return None
    
    def get_telemetry(self) -> Optional[Dict[str, float]]:
        """
        Retrieves the current telemetry data of the drone (no-op).
        """
        return None

    def get_detected_points(self) -> List[Point2D]:
        """
        Returns a list of the detected 2D points during the exploration routine.

        Returns:
            List[Point2D]: List of detected (x, y) coordinates.
        """
        return self._detected_points.copy()

    # ---------------------------------------------------
    # Private methods
    # ---------------------------------------------------
    def _on_color_detected(self, position: Position) -> None:
        """
        Internal callback invoked when a target-colored object is detected.

        This method is automatically called by the ColorDetection 
        module when a visual detection is confirmed. Its responsibilities are:

        - Briefly activating the camera flash as a visual signal.
        - Storing the detected position as a 2D point.
        - Invoking the user-defined point-detection callback, if present.

        Args:
            position (Position): 3D position associated with the frame where the
            detection occurred.
        """
        self._logger.debug(
            "Color detected at (%.2f, %.2f, %.2f)", position.x, position.y, position.z
        )

        try:
            self._camera.turn_on_flash()
            self._camera.turn_off_flash()
        except Exception as e:
            self._logger.error("Failed to flash camera: %s", e)

        self._detected_points.append(Point2D(position.x, position.y))

        if self._callback_onPoint:
            try:
                self._callback_onPoint(Point2D(position.x, position.y))
            except Exception as e:
                self._logger.error("Callback onPoint failed: %s", e)
