# structures.py
from dataclasses import dataclass
import numpy as np

@dataclass
class Battery:
    """
    @brief Represents the current battery status of the drone.

    @var voltage
        Battery voltage in volts.
    """
    voltage: float


@dataclass
class Position:
    """
    @brief Represents a 3D position in space.

    @var x
        X coordinate in meters.
    @var y
        Y coordinate in meters.
    @var z
        Z coordinate in meters.
    """
    x: float
    y: float
    z: float


@dataclass
class Orientation:
    """
    @brief Represents the orientation of the drone in Euler angles.

    @var roll
        Rotation around X-axis in degrees.
    @var pitch
        Rotation around Y-axis in degrees.
    @var yaw
        Rotation around Z-axis in degrees.
    """
    roll: float
    pitch: float
    yaw: float


@dataclass
class Pose:
    """
    @brief Represents a full pose of the drone, combining position and orientation.

    @var position
        Position of the drone (x, y, z).
    @var orientation
        Orientation of the drone (roll, pitch, yaw).
    """
    position: Position
    orientation: Orientation


@dataclass
class TelemetryData:
    """
    @brief Aggregates all telemetry information of the drone.

    @var pose
        Current pose (position + orientation) of the drone.
    @var battery
        Current battery status of the drone.
    """
    pose: Pose
    battery: Battery


@dataclass
class Frame:
    """
    @brief Represents a captured camera frame.

    @var data
        The image data as a NumPy array (H x W x 3).
    """
    data: np.ndarray

@dataclass
class FrameWithPosition:
    """
    @brief Associates a camera frame with a drone position.

    @var frame
        The captured image as a NumPy array (H x W x 3).
    @var position
        The position of the drone when the frame was captured.
    """
    frame: Frame
    position: Position
