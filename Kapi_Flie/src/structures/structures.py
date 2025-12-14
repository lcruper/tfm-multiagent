"""
Core Data Structures for the Drone and Robot Dog System
-------------------------------------------------------

This module defines immutable data containers used across the system
to exchange telemetry, perception data, and geometric information.
"""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


# ============================================================
# Battery
# ============================================================

@dataclass(frozen=True)
class Battery:
    """Battery status snapshot.

    Attributes:
        voltage (int): Battery voltage in volts.
    """
    voltage: float


# ============================================================
# Position
# ============================================================

@dataclass(frozen=True)
class Position:
    """3D position in space.

    Attributes:
        x (float): X coordinate in meters.
        y (float): Y coordinate in meters.
        z (float): Z coordinate in meters.
    """
    x: float
    y: float
    z: float


# ============================================================
# Orientation
# ============================================================

@dataclass(frozen=True)
class Orientation:
    """Orientation expressed as Euler angles.

    Attributes:
        roll (float): Rotation around the X-axis in degrees.
        pitch (float): Rotation around the Y-axis in degrees.
        yaw (float): Rotation around the Z-axis in degrees.
    """
    roll: float
    pitch: float
    yaw: float


# ============================================================
# Pose
# ============================================================

@dataclass(frozen=True)
class Pose:
    """Full 6-DOF pose.

    Combines position and orientation.

    Attributes:
        position (Position): 3D position.
        orientation (Orientation): Euler orientation.
    """
    position: Position
    orientation: Orientation


# ============================================================
# Telemetry
# ============================================================

@dataclass(frozen=True)
class TelemetryData:
    """Aggregated telemetry snapshot.

    Attributes:
        pose (Pose): System pose.
        battery (Battery): Battery status.
    """
    pose: Pose
    battery: Battery


# ============================================================
# Frame
# ============================================================

@dataclass(frozen=True)
class Frame:
    """Captured camera frame.

    Attributes:
        data (np.ndarray): Image array with shape (H, W, C).
              Typically uint8 RGB or BGR.
    """
    data: np.ndarray


# ============================================================
# Frame with Telemetry
# ============================================================

@dataclass(frozen=True)
class FrameWithTelemetry:
    """Camera frame synchronized with telemetry.

    Attributes:
        frame (Frame): Captured camera frame.
        telemetry (TelemetryData): Telemetry snapshot at capture time.
    """
    frame: Frame
    telemetry: TelemetryData


# ============================================================
# Point 2D
# ============================================================

@dataclass(frozen=True)
class Point2D:
    """2D point.

    Attributes:
        x (float): X coordinate in meters.
        y (float): Y coordinate in meters.
    """
    x: float
    y: float
