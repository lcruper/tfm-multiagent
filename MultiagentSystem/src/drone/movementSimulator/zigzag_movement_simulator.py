from configuration import movement_simulator as config
import logging
from time import time
from typing import Optional

from structures.structures import Point2D
from interfaces.interfaces import IMovementSimulator

class ZigzagMovementSimulator(IMovementSimulator):
    """
    Simulates a 2D zigzag movement pattern on the horizontal plane.

    The simulated agent moves horizontally at constant speed between 0 and a maximum distance
    and reverses its direction upon reaching each limit.
    After completing each horizontal traversal, the agent advances vertically
    by a fixed step, producing a zigzag trajectory.

    This simulator is time-based as the current position is computed on demand from the elapsed time
    since the simulation started.
    """

    def __init__(self, max_horizontal_distance: float, speed: float) -> None:
        """
        Creates a ZigzagMovementSimulator instance.

        Args:
            max_horizontal_distance (float): Maximum horizontal distance (in meters) for each traversal.
                The agent moves between 0 and this value along the x-axis.
            speed (float): Constant linear speed of the movement (in meters per second).
        """
        self._max_horizontal_distance: float = max_horizontal_distance
        self._speed: float = speed

        self._active: bool = False
        self._start_t: Optional[float] = None

        self._logger: logging.Logger = logging.getLogger("ZigzagMovementSimulator")

    # ----------------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        Starts the zigzag movement simulation.

        Records the start time used as a reference to compute the simulated
        position.
        """
        if self._active:
            self._logger.warning("Already started.")
            return
        
        self._start_t = time()
        self._active = True
        self._logger.info("Started.")

    def stop(self) -> None:
        """
        Stops the zigzag movement simulation.

        Clears the internal timing state.
        """
        if not self._active:
            self._logger.warning("Already stopped.")
            return
        self._start_t = None
        self._active = False
        self._logger.info("Stopped.")

    def get_xy(self) -> Optional[Point2D]:
        """
        Returns the current (x, y) position of the simulated movement.

        The position is computed analytically from the elapsed time since
        the simulation was started.

        Returns:
            Optional[Point2D]: Current (x, y) coordinates.
            Returns None if the simulator is not active.
        """
        if not self._active:
            return None

        now = time()
        dt = now - self._start_t
        distance = self._speed * dt
        dy, dx = divmod(distance, self._max_horizontal_distance)
        x = dx if int(dy) % 2 == 0 else self._max_horizontal_distance - dx
        y = dy * config.ZIGZAG_SIMULATOR_VERTICAL_STEP

        return Point2D(x,y)