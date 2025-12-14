# structures.py
"""
@file structures.py
@brief Core data structures for the drone + robot dog system.
"""

from dataclasses import dataclass
from numpy import ndarray

# ============================================================
# Battery
# ============================================================

@dataclass
class Battery:
    """
    @brief Stores battery information.

    @var voltage
        Battery voltage in volts.
    """
    voltage: float

# ============================================================
# Position
# ============================================================

@dataclass
class Position:
    """
    @brief Represents a 3D coordinate in space.

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

# ============================================================
# Orientation
# ============================================================

@dataclass
class Orientation:
    """
    @brief Represents an orientation using Euler angles.

    @var roll
        Rotation around the X-axis in degrees.
    @var pitch
        Rotation around the Y-axis in degrees.
    @var yaw
        Rotation around the Z-axis in degrees.
    """
    roll: float
    pitch: float
    yaw: float

# ============================================================
# Pose
# ============================================================

@dataclass
class Pose:
    """
    @brief Combines a 3D position with Euler orientation.

    @var position
        3D position of the system.
    @var orientation
        Euler rotation angles (roll, pitch, yaw).
    """
    position: Position
    orientation: Orientation

# ============================================================
# Telemetry Data
# ============================================================

@dataclass
class TelemetryData:
    """
    @brief Aggregated telemetry information.

    @var pose
        Current system pose (position + orientation).
    @var battery
        Current battery status.
    """
    pose: Pose
    battery: Battery

# ============================================================
# Frame
# ============================================================

@dataclass
class Frame:
    """
    @brief Represents a single captured camera frame.

    @var data
        Image matrix as a NumPy array (H x W x 3), typically RGB.
    """
    data: ndarray

# ============================================================
# Frame With Telemetry
# ============================================================

@dataclass
class FrameWithTelemetry:
    """
    @brief Associates a camera frame with telemetry data.

    @var frame
        Captured camera frame.
    @var telemetry
        Telemetry information at the exact moment the frame was captured.
    """
    frame: Frame
    telemetry: TelemetryData

# ============================================================
# Point 2D
# ============================================================
@dataclass(frozen=True)
class Point2D:
    """
    @brief Represents a point in 2D space.

    @var x
        X coordinate.
    @var y
        Y coordinate.
    """
    x: float
    y: float