# movement_simulator.py
from math import cos, exp, pi, sin
from random import uniform
from time import time
from typing import Tuple

class MovementSimulator:
    """
    @brief Simulates 2D spiral movement for a drone.

    This class generates (x, y) coordinates following a polar spiral,
    allowing simulation of drone movement.
    """

    def __init__(self, b: float, w: float) -> None:
        """
        @brief Constructor.
        
        @param b Radial growth per second (meters/second)
        @param w Angular speed (radians/second)
        """
        self.b = b
        self.w = w

        self.active: bool = False   # Flag indicating if simulation is active
        self.t0: float = None       # Simulation start time

    # ----------------------------------------------------------------------
    # Simulation control
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        @brief Activates the movement simulation.

        Initializes the reference time for the spiral.
        """
        self.active = True
        self.t0 = time()

    def stop(self) -> None:
        """
        @brief Deactivates the movement simulation.

        Clears the start time and stops coordinate calculations.
        """
        self.active = False
        self.t0 = None

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
        r = self.b * (1 - exp(-0.1 * t))
        theta = self.w * t * 2 * pi

        # Convert polar to Cartesian with small jitter
        x = r * cos(theta) + uniform(-0.02, 0.02)
        y = r * sin(theta) + uniform(-0.02, 0.02)

        x = 10
        y = 10

        return x, y
