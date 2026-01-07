from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Callable
from structures.structures import Frame, FrameWithTelemetry, Point2D, TelemetryData

class ITelemetry(ABC):
    """Interface for telemetry providers."""

    @abstractmethod
    def start(self) -> None:
        """Starts telemetry data acquisition."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops telemetry data acquisition."""
        pass

    @abstractmethod
    def get_telemetry(self) -> Optional[TelemetryData]:
        """
        Retrieves the current telemetry data.

        Returns:
            Optional[TelemetryData]: The current telemetry data, or None if unavailable.
        """
        pass

class IMovementSimulator(ABC):
    """Interface for movement simulators."""

    @abstractmethod
    def start(self) -> None:
        """Starts the movement simulator."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops the movement simulator."""
        pass

    @abstractmethod
    def get_xy(self) -> Optional[Point2D]:
        """
        Retrieves the current position.

        Returns:
            Optional[Point2D]: The current position, or None if unavailable.
        """
        pass

class ICamera(ABC):
    """Interface for frames providers."""

    @abstractmethod
    def start(self) -> None:
        """Starts the frame acquisition."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops the frame acquisition."""
        pass

    @abstractmethod
    def get_frame(self) -> Optional[Frame]:
        """
        Retrieves the current frame.

        Returns:
            Optional[Frame]: The current frame, or None if unavailable.
        """
        pass

    @abstractmethod
    def turn_on_flash(self) -> None:
        """Turns on the camera flash (if available)."""
        pass    

    @abstractmethod
    def turn_off_flash(self) -> None:
        """Turns off the camera flash (if available)."""
        pass

class IFrameConsumer(ABC):
    """Interface for components that process frames with telemetry."""

    @abstractmethod
    def start(self) -> None:
        """Starts consuming frames."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops consuming frames."""
        pass

    @abstractmethod
    def enqueue(self, fwt: FrameWithTelemetry) -> None:
        """
        Enqueues a FrameWithTelemetry object for processing.

        Args:
            fwt (FrameWithTelemetry): Frame data with associated telemetry to enqueue.
        """
        pass

class IRobot(ABC):
    """
    Interface for robots.
    
    Attributes:
        _callback_onPoint (Optional[Callable[[Point2D], None]]): Callback for when a point is reached.
        _callback_onFinish (Optional[Callable[[], None]]): Callback for when inspection finishes.
    """

    _callback_onPoint: Optional[Callable[[Point2D], None]] = None
    _callback_onFinish: Optional[Callable[[], None]] = None

    @abstractmethod
    def start_inspection(self, positions: Optional[List[Point2D]]) -> None:
        """
        Starts the inspection routine.

        Args:
            positions (Optional[List[Point2D]]): List of target points to inspect. If None, no targets are set.
        """
        pass

    @abstractmethod
    def stop_inspection(self) -> Optional[List[Point2D]]:
        """
        Stops the inspection routine.

        Returns:
            Optional[List[Point2D]]: List of detected points, or None if unavailable.
        """
        pass

    @abstractmethod
    def set_callback_onPoint(self, callback: Callable[[Point2D], None]) -> None:
        """
        Register a callback triggered when the robot reaches a target point.

        Args:
            callback (Callable[[Point2D], None]): Function to call when reaching a point. 
        """
        pass

    @abstractmethod
    def set_callback_onFinish(self, callback: Callable[[], None]) -> None:
        """
        Register a callback triggered when the inspection finishes.

        Args:
            callback (Callable[[], None]): Function to call when inspection finishes.
        """
        pass

    @abstractmethod
    def get_current_position(self) -> Optional[Point2D]:
        """
        Retrieves the current position of the robot.

        Returns:
            Optional[Point2D]: the current position, or None if unavailable.
        """
        pass

    def get_telemetry(self) -> Optional[Dict[str, float]]:
        """
        Retrieves the current telemetry data of the robot.

        Returns:
            Optional[Dict[str, float]]: the current telemetry data as a dictionary of sensor names to values, or None if unavailable.
        """
        pass

class IPathPlanner(ABC):
    """Interface for path planning algorithms."""

    def euclidean_distance(self, p1: Point2D, p2: Point2D) -> float:
        """
        Computes the Euclidean distance between two points.

        Args:
            p1 (Point2D): First point.
            p2 (Point2D): Second point.

        Returns:
            float: Euclidean distance between p1 and p2.
        """
        return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5

    @abstractmethod
    def plan_path(self, start: Point2D, points: List[Point2D]) -> List[Point2D]:
        """
        Plans a path from a starting position through a list of target points.
        
        Args:
            start (Point2D): Starting position.
            points (List[Point2D]): Target points.

        Returns:
            List[Point2D]: Ordered list of points representing the planned path.
        """
        pass
