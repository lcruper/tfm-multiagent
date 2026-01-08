from typing import Final
from configuration.operation import DRONE_VISIBILITY

SPIRAL_SIMULATOR_RADIAL_GROWTH: Final[float] = DRONE_VISIBILITY
"""Radial growth rate (in meters per radians) for spiral movement, that is, the distance between turns.
It is set to `DRONE_VISIBILITY`
"""

SPIRAL_SIMULATOR_LINEAR_SPEED: Final[float] = 0.25
"""Linear speed (in meters per second) of the spiral movement."""

ZIGZAG_SIMULATOR_MAX_HORIZONTAL_DISTANCE: Final[float] = 5.0
"""Maximum horizontal distance from origin (in meters) of the zigzag movement."""

ZIGZAG_SIMULATOR_VERTICAL_STEP: Final[float] = DRONE_VISIBILITY
"""Vertical step (in meters) each time the zigzag movement reaches a horizontal limit. 
It is set to `DRONE_VISIBILITY`."""

ZIGZAG_SIMULATOR_LINEAR_SPEED: Final[float] = 0.5
"""Linear speed (in meters per second) of the zigzag movement."""
