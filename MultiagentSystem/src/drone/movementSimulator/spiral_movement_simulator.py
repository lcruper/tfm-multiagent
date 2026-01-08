import logging
from math import cos, pi, sin, sqrt
from time import time
from typing import Optional

from structures.structures import Point2D
from interfaces.interfaces import IMovementSimulator

class SpiralMovementSimulator(IMovementSimulator):
    """
    Simulates a 2D an Archimedean spiral on the horizontal plane.

    The simulated agent moves in an equidistant spiral starting from the origin (0,0).
    The spiral has a fixed radial growth per turn, and the agent moves along the spiral 
    at a constant linear speed. 
    
    This simulator is time-based as the current position is computed on demand from the
    last angle recorded and the elapsed time since it.
    """

    def __init__(self, radial_growth: float, linear_speed: float) -> None:
        """
        Creates a SpiralMovementSimulator instance.

        Args:
            radial_growth (float): Radial growth per unit angle (m/rad), that is, the distance between turns.
            linear_speed (float): Linear speed of the movement (m/s).
        """
        self._radial_growth: float = radial_growth
        self._linear_speed: float = linear_speed

        self._active: bool = False
        self._last_t: Optional[float] = None
        self._theta: float = 0.0

        self._logger: logging.Logger = logging.getLogger("SpiralMovementSimulator")

    # ----------------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        Starts the spiral movement simulation.

        Records the start time as last updated time and sets the angle to 0.0.
        """
        if self._active:
            self._logger.warning("Already started.")
            return
        self._theta = 0.0
        self._last_t = time()
        self._theta = 0.0
        self._active = True
        self._logger.info("Started.")

    def stop(self) -> None:
        """
        Stops the spiral movement simulation.

        Resets the internal state including angular position and last computation time.
        """
        if not self._active:
            self._logger.warning("Already stopped.")
            return
        self._active = False
        self._last_t = None
        self._theta = 0.0   
        self._logger.info("Stopped.")

    def get_xy(self) -> Optional[Point2D]:
        """
        Returns the current (x, y) position of the simulated movement.

        The position is computed analytically from last angle record and the elapsed time since it.

        Returns:
            Optional[Point2D]: Current (x, y) coordinates.
            Returns None if the simulator is not active.
        """
        if not self._active:
            return None

        now = time()
        dt = now - self._last_t
        self._last_t = now

        ds = self._linear_speed * dt

        dr_dtheta = self._radial_growth / (2 * pi)

        r = dr_dtheta * self._theta
        dtheta = ds / sqrt(r**2 + dr_dtheta**2)
        self._theta += dtheta

        r = dr_dtheta * self._theta
        x = r * cos(self._theta)
        y = r * sin(self._theta)

        return Point2D(x, y)
