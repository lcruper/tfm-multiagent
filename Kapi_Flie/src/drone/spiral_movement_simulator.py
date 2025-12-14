"""
Spiral Movement Simulator Module
--------------------------------

This module implements a 2D spiral movement simulator.

It generates (x, y) coordinates following a polar spiral pattern.
"""

import config
import logging
from math import cos, sin
from random import uniform
from time import time
from typing import Optional

from structures.structures import Point2D
from interfaces.interfaces import IMovementSimulator


class SpiralMovementSimulator(IMovementSimulator):
    """
    Simulates 2D spiral movement.
    """

    def __init__(self, rg: float, w: float) -> None:
        """
        Creates a SpiralMovementSimulator instance.

        Args:
            rg (float): Radial growth per unit angle (in m/s)
            w (float): Angular speed (in rad/s).
        """
        self.rg: float = rg
        self.w: float = w

        self._active: bool = False
        self._t0: Optional[float] = None

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
        self._active = True
        self._t0 = time()
        self._logger.info("Started.")

    def stop(self) -> None:
        """
        Deactivates the spiral movement simulation.
        """
        if not self._active:
            self._logger.warning("Already stopped.")
            return
        self._active = False
        self._t0 = None
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
        if not self._active:
            return None

        t = time() - self._t0

        theta = self.w * t
        r = self.rg * theta

        x = r * cos(theta) + uniform(-config.SPIRAL_SIMULATOR_JITTER, config.SPIRAL_SIMULATOR_JITTER)
        y = r * sin(theta) + uniform(-config.SPIRAL_SIMULATOR_JITTER, config.SPIRAL_SIMULATOR_JITTER)

        return Point2D(x, y)
