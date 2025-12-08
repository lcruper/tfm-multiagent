# interfaces.py
"""
@file interfaces.py
@brief This module defines interfaces for camera, telemetry, frame consumer,
movement simulator, and robot classes.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

from structures.structures import Frame, FrameWithTelemetry, TelemetryData

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
    def start_inspection(self, positions: Optional[List[Dict[str, float]]]) -> None:
        """
        @brief Starts the robot inspection.

        @param positions Optional list of target positions.
        """
        pass

    @abstractmethod
    def stop_inspection(self) -> Optional[List[Dict[str, float]]]:
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
    def get_current_position(self) -> Tuple[Optional[float], Optional[float]]:
        """
        @brief Retrieves the current (x, y) position of the robot.

        @return Tuple of (x, y) coordinates or (None, None) if unavailable.
        """
        pass