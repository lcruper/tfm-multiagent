# constant_movement_simulator.py
"""
@file constant_movement_simulator.py
@brief Implements a simple 2D constant movement simulator.
"""
import logging
from typing import Optional, Tuple

from interfaces.interfaces import IMovementSimulator

class ConstantMovementSimulator(IMovementSimulator):
    """
    @brief Simulates 2D constant movement.

    This class generates (x, y) coordinates following a constant movement pattern,
    allowing simulation of movement.
    """

    def __init__(self, x: float, y: float) -> None:
        """
        @brief Constructor.
        
        @param x Initial x coordinate
        @param y Initial y coordinate
        """
        self.x = x                              
        self.y = y                              

        self.active: bool = False               # Flag indicating if simulation is active

        # Logger
        self._logger = logging.getLogger("ConstantMovementSimulator")

    # ----------------------------------------------------------------------
    # Control
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        @brief Activates the constant movement simulation.

        Initializes the reference time for the constant movement.
        """
        if self.active:
            self._logger.warning("Constant movement simulator already started.")
            return
        self.active = True
        self._logger.info("Constant movement simulator started.")

    def stop(self) -> None:
        """
        @brief Deactivates the constant movement simulation.

        Clears the start time and stops coordinate calculations.
        """
        if not self.active:
            self._logger.warning("Constant movement simulator already stopped.")
            return
        self.active = False
        self._logger.info("Constant movement simulator stopped.")

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    def get_xy(self) -> Tuple[Optional[float], Optional[float]]:
        """
        @brief Returns the current (x, y) coordinates of the constant movement.

        @return tuple(float, float) x and y coordinates of the constant movement.
        Returns (None, None) if the simulation is not active.
        """
        if not self.active:
            return None, None
        
        return self.x, self.y
