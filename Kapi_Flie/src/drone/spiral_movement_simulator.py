"""
Spiral Movement Simulator Module
--------------------------------

This module implements a 2D spiral movement simulator with constant linear speed.

It generates (x, y) coordinates following an Archimedean spiral:
    r = rg * theta
"""

import configuration.config as config
import logging
from math import cos, sin
from random import uniform
from time import time
from typing import Optional

from structures.structures import Point2D
from interfaces.interfaces import IMovementSimulator


class SpiralMovementSimulator(IMovementSimulator):
    """
    Simulates 2D spiral movement with constant linear speed.
    """

    def __init__(self, rg: float, v: float) -> None:
        """
        Creates a SpiralMovementSimulator instance.

        Args:
            rg (float): Radial growth per unit angle (in m/rad)
            v (float): Linear speed (in ms/s).
        """
        self.rg: float = rg
        self.v: float = v

        self._theta: float = 0.0

        self._active: bool = False
        self._last_t: Optional[float] = None

        self._logger: logging.Logger = logging.getLogger("SpiralMovementSimulator")

    # ----------------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        Activates the spiral movement simulation.
        """
        if self._active:
            self._logger.warning("Already started.")
            return
        self._theta = 0.0
        self._last_t = time()
        self._active = True
        self._logger.info("Started.")

    def stop(self) -> None:
        """
        Deactivates the spiral movement simulation.
        """
        if not self._active:
            self._logger.warning("Already stopped.")
            return
        self._active = False
        self._last_t = None
        self._logger.info("Stopped.")

    def get_xy(self) -> Optional[Point2D]:
        """
        Returns the current (x, y) coordinates of the spiral.

        Calculates the position based on elapsed time since the simulation started.
        Adds random jitter.

        Returns:
            Optional[Point2D]: Current x and y coordinates.
            Returns None if the simulator is not active.
        """
        if not self._active or self._last_t is None:
            return None

        now = time()
        dt = now - self._last_t
        self._last_t = now

        if dt <= 0.0:
            return None
        
        dtheta = (self.v * dt) /  max(self.rg * (1.0 + self._theta**2)**0.5, 1e-6)
        self._theta += dtheta

        r = self.rg * self._theta
        x = r * cos(self._theta) + uniform(-config.SPIRAL_SIMULATOR_JITTER, config.SPIRAL_SIMULATOR_JITTER)
        y = r * sin(self._theta) + uniform(-config.SPIRAL_SIMULATOR_JITTER, config.SPIRAL_SIMULATOR_JITTER)

        return Point2D(x, y)
