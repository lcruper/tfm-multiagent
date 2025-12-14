# interfaces.py
"""
@file interfaces.py
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

from structures.structures import Frame, FrameWithTelemetry, Point2D, TelemetryData

# -------------------------------
# Camera
# -------------------------------
class ICamera(ABC):
    """
    @brief Interface for camera classes.
    """
    @abstractmethod
    def get_frame(self) -> Frame:
        """
        @brief Retrieves a single camera frame.
        """
        pass

    @abstractmethod
    def turn_on_flash(self) -> None:
        """
        @brief Turns on the camera flash.
        """
        pass    

    @abstractmethod
    def turn_off_flash(self) -> None:
        """
        @brief Turns off the camera flash.
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """
        @brief Starts the camera.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        @brief Stops the camera.
        """
        pass

# -------------------------------
# Telemetry
# -------------------------------
class ITelemetry(ABC):
    """
    @brief Interface for telemetry classes.
    """
    @abstractmethod
    def get_telemetry(self) -> TelemetryData:
        """
        @brief Retrieves telemetry data.
        """
        pass

    @abstractmethod
    def start(self) -> None:
        """
        @brief Starts the telemetry.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        @brief Stops the telemetry.
        """
        pass

# -------------------------------
# FrameWithTelemetry consumer
# -------------------------------
class IFrameConsumer(ABC):
    """
    @brief Interface for FrameWithTelemetry consumer classes.
    """
    @abstractmethod
    def enqueue(self, fwt: FrameWithTelemetry) -> None:
        """
        @brief Enqueues a FrameWithTelemetry object for processing.
        """
        pass

# -------------------------------
# Movement Simulator
# -------------------------------
class IMovementSimulator(ABC):
    """
    @brief Interface for movement simulator classes.
    """
    @abstractmethod
    def start(self) -> None:
        """
        @brief Starts the movement simulator.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        @brief Stops the movement simulator.
        """
        pass

    @abstractmethod
    def get_xy(self) -> Tuple[Optional[float], Optional[float]]:
        """
        @brief Retrieves the current (x, y) position.
        """
        pass

# -------------------------------
# Robot
# -------------------------------
class IRobot(ABC):
    """
    @brief Interface for robot classes.
    """
    @abstractmethod
    def start_inspection(self, positions: Optional[List[Point2D]]) -> None:
        """
        @brief Starts the robot inspection.

        @param positions Optional list of target positions.
        """
        pass

    @abstractmethod
    def stop_inspection(self) -> Optional[List[Point2D]]:
        """
        @brief Stops the robot inspection.

        @return List of detected points or None.
        """
        pass

    @abstractmethod
    def set_callback_onPoint(self, callback: callable) -> None:
        """
        @brief Sets a callback function to be called when reaching each point.

        @param callback Function to call when reaching each point: fn(x: float, y: float)
        """
        pass

    @abstractmethod
    def set_callback_onFinish(self, callback: callable) -> None:
        """
        @brief Sets a callback function to be called when the inspection finishes.
        
        @param callback Function to call when inspection finishes: fn()
        """
        pass

    @abstractmethod
    def get_current_position(self) -> Point2D:
        """
        @brief Retrieves the current (x, y) position of the robot.

        @return Tuple of (x, y) coordinates or (None, None) if unavailable.
        """
        pass

# -------------------------------
# Path Planner
# -------------------------------
class IPathPlanner(ABC):
    """
    @brief Interface for path planner classes.
    """

    def euclidean_distance(self, p1: Point2D, p2: Point2D) -> float:
        """
        @brief Calculates the Euclidean distance between two points.

        @param p1 First point (x1, y1).
        @param p2 Second point (x2, y2).

        @return Euclidean distance between p1 and p2.
        """
        dx = p1.x - p2.x
        dy = p1.y - p2.y
        return (dx**2 + dy**2)**0.5

    @abstractmethod
    def plan_path(self, start: Point2D, points: List[Point2D]) -> List[Point2D]:
        """
        @brief Plans a path from start to multiple points.

        @param start Starting position (x, y).
        @param points List of target positions [(x1, y1), (x2, y2), ...].

        @return List of waypoints [(x1, y1), (x2, y2), ...] representing the planned path.
        """
        pass