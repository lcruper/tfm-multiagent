# movement_drone_simulator.py
import config
import logging
from math import cos, exp, pi, sin
from random import uniform
from time import time
from typing import Optional, Tuple

class MovementDroneSimulator:
    """
    @brief Simulates 2D spiral movement for a drone.

    This class generates (x, y) coordinates following a polar spiral,
    allowing simulation of drone movement.
    """

    def __init__(self, rg: float, w: float) -> None:
        """
        @brief Constructor.
        
        @param rg Radial growth per second (meters/second)
        @param w Angular speed (radians/second)
        """
        self.rg = rg
        self.w = w

        self.active: bool = False               # Flag indicating if simulation is active
        self.t0: Optional[float] = None         # Simulation start time

        self._logger = logging.getLogger("MovementSimulator")

    # ----------------------------------------------------------------------
    # Simulation control
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        @brief Activates the movement simulation.

        Initializes the reference time for the spiral.
        """
        if self.active:
            self._logger.warning("Movement simulator already started.")
            return
        self.active = True
        self.t0 = time()
        self._logger.info("Movement simulator started.")

    def stop(self) -> None:
        """
        @brief Deactivates the movement simulation.

        Clears the start time and stops coordinate calculations.
        """
        if not self.active:
            self._logger.warning("Movement simulator already stopped.")
            return
        self.active = False
        self.t0 = None
        self._logger.info("Movement simulator stopped.")
    # ----------------------------------------------------------------------
    # Coordinate retrieval
    # ----------------------------------------------------------------------
    def get_xy(self) -> Tuple[float, float]:
        """
        @brief Returns the current (x, y) coordinates of the spiral.

        Calculates the position based on the elapsed time since
        the simulation started.

        @return tuple(float, float) x and y coordinates of the spiral.
        Returns (None, None) if the simulation is not active.
        """
        if not self.active:
            return None, None

        t = time() - self.t0
        
         # Smooth radius growth
        r = self.rg * (1 - exp(-config.SIMULATOR_EXP_SMOOTH * t))
        theta = self.w * t * 2 * pi

        # Convert polar to Cartesian with small jitter
        x = r * cos(theta) + uniform(-config.SIMULATOR_JITTER, config.SIMULATOR_JITTER)
        y = r * sin(theta) + uniform(-config.SIMULATOR_JITTER, config.SIMULATOR_JITTER)

        x = 10
        y = 10

        return x, y
