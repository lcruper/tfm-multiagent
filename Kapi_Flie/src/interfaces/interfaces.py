"""
Core Interfaces for the Drone and Robot Dog System
--------------------------------------------------

This module defines the abstract interfaces for the system. It provides standardized contracts for 
key components.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Callable

from structures.structures import Frame, FrameWithTelemetry, Point2D, TelemetryData

# -------------------------------
# Camera Interface
# -------------------------------
class ICamera(ABC):
    """Interface for camera classes."""

    @abstractmethod
    def start(self) -> None:
        """Starts the camera."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops the camera."""
        pass

    @abstractmethod
    def get_frame(self) -> Optional[Frame]:
        """
        Retrieves a single camera frame.

        Returns:
            Optional[Frame]: The current camera frame, or None if unavailable.
        """
        pass

    @abstractmethod
    def turn_on_flash(self) -> None:
        """Turns on the camera flash."""
        pass    

    @abstractmethod
    def turn_off_flash(self) -> None:
        """Turns off the camera flash."""
        pass

# -------------------------------
# Telemetry Interface
# -------------------------------
class ITelemetry(ABC):
    """Interface for telemetry classes."""

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

# ----------------------------------------
# FrameWithTelemetry Consumer Interface
# ----------------------------------------
class IFrameConsumer(ABC):
    """Interface for classes consuming FrameWithTelemetry objects."""

    @abstractmethod
    def start(self) -> None:
        """Starts the frame processing."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stops the frame processing."""
        pass

    @abstractmethod
    def enqueue(self, fwt: FrameWithTelemetry) -> None:
        """
        Enqueues a FrameWithTelemetry object for processing.

        Args:
            fwt (FrameWithTelemetry): Frame data with telemetry.
        """
        pass

# -------------------------------
# Movement Simulator Interface
# -------------------------------
class IMovementSimulator(ABC):
    """Interface for movement simulator classes."""

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
            Optional[Point2D]: Current position, or None if unavailable.
        """
        pass

# -------------------------------
# Robot Interface
# -------------------------------
class IRobot(ABC):
    """Interface for robot classes."""

    @abstractmethod
    def start_inspection(self, positions: Optional[List[Point2D]]) -> None:
        """
        Starts the robot inspection.

        Args:
            positions (Optional[List[Point2D]]): List of target positions to inspect. If None, no targets are set.
        """
        pass

    @abstractmethod
    def stop_inspection(self) -> Optional[List[Point2D]]:
        """
        Stops the robot inspection.

        Returns:
            Optional[List[Point2D]]: List of detected points, or None if unavailable.
        """
        pass

    @abstractmethod
    def set_callback_onPoint(self, callback: Callable[[Point2D], None]) -> None:
        """
        Sets a callback to be called when reaching each point.

        Args:
            callback (Callable[[Point2D], None]): Function to call when reaching each point. 
        """
        pass

    @abstractmethod
    def set_callback_onFinish(self, callback: Callable[[], None]) -> None:
        """
        Sets a callback to be called when the inspection finishes.

        Args:
            callback (Callable[[], None]): Function to call when inspection finishes.
        """
        pass

    @abstractmethod
    def get_current_position(self) -> Optional[Point2D]:
        """
        Retrieves the current position of the robot.

        Returns:
            Optional[Point2D]: Current position, or None if unavailable.
        """
        pass


# -------------------------------
# Path Planner Interface
# -------------------------------
class IPathPlanner(ABC):
    """Interface for path planner classes."""

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
        Plans a path from start to multiple points.

        Args:
            start (Point2D): Starting position.
            points (List[Point2D]): Target positions.

        Returns:
            List[Point2D]: Planned path as a list of waypoints.
        """
        pass
