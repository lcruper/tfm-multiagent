"""
RobotDog Module
---------------

Simulated robot dog that follows a list of 2D coordinates.
Provides a unified API to start/stop movement and set callbacks for reached points and finish events.
"""

import logging
import threading
import time
from math import hypot
from typing import Dict, List, Optional, Callable
from numpy.random import normal

from configuration import robot_dog as config
from interfaces.interfaces import IRobot
from structures.structures import Point2D


class RobotDog(IRobot):
    """
    Simulated robot dog.

    Moves sequentially along a list of 2D coordinates at a fixed speed. 
    Supports callbacks for reached points and when the full path is completed.
    """

    def __init__(self, speed: float) -> None:
        """
        Create a RobotDog instance.

        Args:
            speed (float): Movement speed of the robot dog (in m/s).
        """
        self.speed = speed

        self._current_position: Point2D = Point2D(0.0, 0.0)
        self._waypoints: List[Point2D] = []

        self._running: bool = False
        self._thread: Optional[threading.Thread] = None

        self._logger = logging.getLogger("RobotDog")

    # ---------------------------------------------------
    # Public methods
    # ---------------------------------------------------
    def start_inspection(self, positions: List[Point2D]) -> None:
        """
        Start moving along the given list of positions.

        Args: 
            positions (List[Point2D]): List of target positions.
        """
        if self._running:
            self._logger.warning("Already running.")
            return
        
        self._waypoints = positions
        self._running = True
        self._thread = threading.Thread(target=self._move, daemon=True)
        self._thread.start()
        self._logger.info("Started.")

    def stop_inspection(self) -> None:
        """
        Stop the movement.
        """
        if not self._running:
            self._logger.warning("Already stopped.")
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            if self._thread.is_alive():
                self._logger.warning("Did not stop in time.")
            self._thread = None
        self._logger.info("Stopped.")

    def set_callback_onPoint(self, callback: Callable[[Point2D], None]) -> None:
        """
        Set a callback to be called when a point is reached.

        Args:
            callback (Callable[[Point2D], None]): Function called with the reached point.
        """
        self._callback_onPoint = callback

    def set_callback_onFinish(self, callback: Callable[[], None]) -> None:
        """
        Set a callback to be called when all points are reached.

        Args:
            callback (Callable[[], None]): Function called when movement finishes.  
        """
        self._callback_onFinish = callback

    def get_current_position(self) -> Point2D:
        """
        Get the current 2D position.

        Returns:   
            Point2D: Current position as Point2D.   
        """
        return Point2D(self._current_position.x, self._current_position.y)  
    
    def get_telemetry(self) -> Optional[Dict[str, float]]:
        """
        Retrieves the current telemetry data of the robot. In this case, it returns the current temperature.

        Returns:
            Optional[Dict[str, float]]: Current telemetry data, or None if unavailable.
        """
        return {"temperature": self._get_temperature()}

    # ---------------------------------------------------
    # Internal methods
    # ---------------------------------------------------
    def _get_temperature(self) -> float:
        """
        Get the current temperature of the ambient environment.
    
        It simulates temperature readings using a normal distribution.
        Returns:
            float: Current temperature in Celsius.
        """
        return normal(config.ROBOT_DOG_MEAN_TEMPERATURE, config.ROBOT_DOG_TEMPERATURE_STDDEV)
    
    def _move(self) -> None:
        """
        Internal movement loop.

        Moves sequentially through the waypoints, triggering callbacks as needed.
        """
        for target in self._waypoints:
            if not self._running:
                break

            tx = target.x
            ty = target.y
            self._logger.debug("Moving toward (%.2f, %.2f)...", tx, ty)

            while self._running:
                cx = self._current_position.x
                cy = self._current_position.y
                dist = hypot(tx - cx, ty - cy)
                if dist < config.ROBOT_DOG_REACHED_TOLERANCE:
                    self._current_position = Point2D(tx, ty)
                    self._logger.info("Reached (%.2f, %.2f)", tx, ty)

                    if self._callback_onPoint:
                        try:
                            self._callback_onPoint(Point2D(tx, ty))
                        except Exception as e:
                            self._logger.error("Callback onPoint failed: %s", e)
                    break

                step = min(dist, self.speed * config.ROBOT_SLEEP_TIME)
                ratio = step / dist
                nx = cx + (tx - cx) * ratio
                ny = cy + (ty - cy) * ratio
                self._current_position = Point2D(nx, ny)

                time.sleep(config.ROBOT_SLEEP_TIME)

        if self._callback_onFinish:
            try:
                self._callback_onFinish()
            except Exception as e:
                self._logger.error("Callback onFinish failed: %s", e)

        self._logger.info("Finished all target positions.")
        self._running = False
