# robot_dog.py
"""
@file robot_dog.py
@brief Simulated robot dog that follows a list of 2D coordinates.
"""
import config
import threading
import time
import logging
from math import hypot
from typing import Dict, List, Optional, Tuple

from interfaces.interfaces import IRobot

class RobotDog(IRobot):
    """
    @brief Simulated robot dog that follows a list of (x, y) coordinates sequentially.
    
    It moves at a constant speed and stops after reaching the final coordinate.
    """

    def __init__(self, speed: float) -> None:
        """
        @brief Constructor.

        @param speed Movement speed of the robot dog.
        """
        self.speed: float = speed

        self._callbackOnPoint: Optional[callable] = None
        self._callbackOnFinish: Optional[callable] = None

        self._waypoints: List[Tuple[float, float]] = []                 # List of (x, y) target positions
        self._current_position: Tuple[float, float] = (0.0, 0.0)        # Current (x, y) position
        
        # Threading
        self._running: bool = False                             # Flag to control the background robot dog movement thread
        self._thread: Optional[threading.Thread] = None         # Robot dog movement thread

        # Logger
        self._logger: logging.Logger = logging.getLogger("RobotDog")

    # ---------------------------------------------------------
    # Control
    # ---------------------------------------------------------
    def start_inspection(self, positions: List[Dict[str, float]]) -> None:
        """
        @brief Start the robot dog movement along a list of (x, y) coordinates.

        @param positions List of positions 
        """
        if self._running:
            self._logger.warning("Movement robot dog already running.")
            return
        
        if not positions:
            self._logger.warning("Received empty path. Robot dog will not move.")
            return

        self._waypoints = [(p["x"], p["y"]) for p in positions]
        self._running = True
        self._thread = threading.Thread(target=self._move, daemon=True)
        self._thread.start()
        self._logger.info("Movement robot dog started.")

    def stop_inspection(self):
        """
        @brief Stops the robot dog movement thread.
        """
        if not self._running:
            self._logger.warning("Movement robot dog already stopped.")
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            if self._thread.is_alive():
                self._logger.warning("Movement dog thread didn't stop in time")
            self._thread = None
        self._logger.info("Movement dog stopped.")
        return None
    
    def set_callback_onFinish(self, callback: callable) -> None:
        """
        @brief Sets a callback function to be called when the robot dog inspection finishes.

        @param callback Function to call when inspection finishes.
        """
        self._callbackOnFinish = callback

    def set_callback_onPoint(self, callback: callable) -> None:
        """
        @brief Sets a callback function to be called when the robot dog reaches each point.

        @param callback Function to call when reaching each point: fn(x: float, y: float)
        """
        self._callbackOnPoint = callback

    def get_current_position(self) -> Tuple[Optional[float], Optional[float]]:
        """
        @brief Retrieves the current (x, y) position of the robot dog.

        @return Tuple of (x, y) coordinates.
        """
        return self._current_position

    # ---------------------------------------------------------
    # Internal methods
    # ---------------------------------------------------------
    def _move(self) -> None:
        """
        @brief Moves the robot dog along the path.
        """
        for target in self._waypoints:
            if not self._running:
                break
            tx, ty = target
            self._logger.debug("Moving toward (%.2f, %.2f)...", tx, ty)

            while self._running:
                cx, cy = self._current_position
                # Distance to target
                dist = hypot(tx - cx, ty - cy)
                if dist < config.ROBOT_DOG_REACHED_TOLERANCE:  # consider reached
                    self._current_position = (tx, ty)
                    self._logger.info("Reached (%.2f, %.2f)", tx, ty)
                    if self._callbackOnPoint:
                        self._callbackOnPoint(tx, ty)   
                    break
                # Move step toward the target
                step = min(dist, self.speed * config.ROBOT_DOG_STEP_DELAY) 
                ratio = step / dist
                nx = cx + (tx - cx) * ratio
                ny = cy + (ty - cy) * ratio
                self._current_position = (nx, ny)

                time.sleep(config.ROBOT_DOG_STEP_DELAY) 

        if self._callbackOnFinish:
            self._callbackOnFinish()

        self._logger.info("Robot dog finished all target positions.")
        self._running = False
