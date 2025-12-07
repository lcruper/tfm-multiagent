# robot_dog.py
import config
import threading
import time
import logging
from math import hypot
from typing import List, Optional, Tuple


class RobotDog:
    """
    @brief Simulated robot dog that follows a list of (x, y) coordinates sequentially.
    
    It moves at a constant speed and stops after reaching the final coordinate.
    """

    def __init__(self, callbackOnPoint: callable, callbackOnFinish: callable) -> None:
        """
        @brief Constructor.

        @param callbackOnPoint  Function to call when reaching each point: fn(x: float, y: float) -> None
        @param callbackOnFinish Function to call when finishing the path: fn() -> None
        """
        self.callbackOnPoint: callable = callbackOnPoint
        self.callbackOnFinish: callable = callbackOnFinish


        self.waypoints: List[Tuple[float, float]] = []              # List of (x, y) target positions    
        self.current_position: Tuple[float, float] = (0.0, 0.0)     # Current (x, y) position
        
        # Threading
        self._running: bool = False                             # Flag to control the background dog movement thread
        self._thread: Optional[threading.Thread] = None         # Dog movement thread

        # Logger
        self._logger: logging.Logger = logging.getLogger("RobotDog")

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def load_path(self, positions: List[Tuple[float, float]]) -> None:
        """
        @brief Load a list of (x, y) coordinates for the dog to follow.

        @param positions List of (x, y) tuples
        """
        if not positions:
            self._logger.warning("Received empty path. Dog will not move.")
            return

        self.waypoints = list(positions)
        self._logger.debug("Loaded %d target positions for the dog.", len(self.waypoints))

    # ----------------------------------------------------------------------
    # Control
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        @brief Start dog movement thread.
        """
        if not self.waypoints:
            self._logger.warning("Cannot start dog: path is empty.")
            return

        if self._running:
            self._logger.warning("Movement dog already running.")
            return

        self._logger.info("Starting movement dog...")
        self._running = True
        self._thread = threading.Thread(target=self._move, daemon=True)
        self._thread.start()
        self._logger.info("Movement dog started.")

    def stop(self) -> None:
        """
        @brief Stops the dog movement thread.
        """
        if not self._running:
            self._logger.warning("Movement dog already stopped.")
            return
        
        self._logger.info("Stopping movement dog...")
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            if self._thread.is_alive():
                self._logger.warning("Movement dog thread didn't stop in time")
            self._thread = None
        self._logger.info("Movement dog stopped.")

    # ---------------------------------------------------------
    # Internal methods
    # ---------------------------------------------------------
    def _move(self) -> None:
        """
        @brief Moves the dog along the path.
        """
        for target in self.waypoints:
            if not self._running:
                break
            tx, ty = target
            self._logger.debug("Moving toward (%.2f, %.2f)...", tx, ty)

            while self._running:
                cx, cy = self.current_position
                # Distance to target
                dist = hypot(tx - cx, ty - cy)
                if dist < config.ROBOT_DOG_REACHED_TOLERANCE:  # consider reached
                    self.current_position = (tx, ty)
                    self.callbackOnPoint(tx, ty)
                    self._logger.debug("Reached (%.2f, %.2f)", tx, ty)
                    break
                # Move step toward the target
                step = min(dist, config.ROBOT_DOG_SPEED * config.ROBOT_DOG_STEP_DELAY) 
                ratio = step / dist
                nx = cx + (tx - cx) * ratio
                ny = cy + (ty - cy) * ratio
                self.current_position = (nx, ny)

                time.sleep(config.ROBOT_DOG_STEP_DELAY) 


        self.callbackOnFinish()
        self._logger.info("Dog finished all target positions.")
        self._running = False
