import logging
import threading
import time
from math import hypot
from typing import Dict, List, Optional
from numpy.random import normal

from configuration import robot_dog as config
from interfaces.interfaces import ARobot
from structures.structures import Point2D

class RobotDogSimulator(ARobot):
    """
    Simulated ground robot that follows a list of 2D waypoints.

    The robot moves sequentially through the provided positions at a fixed
    linear speed once an inspection routine is explicitly started. Movement
    is executed in a background thread, allowing the main program to continue
    running while the robot advances. During motion, callbacks are triggered
    when a waypoint is reached and when all waypoints have been processed.
    """

    def __init__(self, speed: float) -> None:
        """
        Creates a RobotDogSimulator instance.

        The robot starts at position (0, 0) and remains idle until an
        inspection routine is started by calling start_inspection().

        Args:
            speed (float): Linear movement speed of the robot dog (in m/s).
        """
        self._speed: float = speed

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
        Starts the inspection routine.

        This method assigns the list of target positions and launches a
        background thread that moves the robot sequentially toward each
        waypoint. If the robot is already running, the request is ignored.

        Args:
            positions (List[Point2D]): Ordered list of target positions to visit.
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
        Stops the inspection routine.

        This method signals the movement thread to stop and waits briefly for
        it to terminate.
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

    def get_current_position(self) -> Point2D:
        """
        Returns the current position of the robot.

        A copy of the internal position is returned to avoid external
        modification of the robot state.

        Returns:
            Point2D: Current 2D position of the robot.
        """
        return Point2D(self._current_position.x, self._current_position.y)  
    
    def get_telemetry(self) -> Optional[Dict[str, float]]:
        """
        Returns the current telemetry data of the robot.

        In this simulated implementation, telemetry consists only of a
        temperature reading generated from a normal distribution.

        Returns:
            Optional[Dict[str, float]]: Dictionary containing the current
            temperature value.
        """
        return {"temperature": self._get_temperature()}

    # ---------------------------------------------------
    # Private methods
    # ---------------------------------------------------
    def _get_temperature(self) -> float:
        """
        Generates a simulated ambient temperature reading.

        The temperature value is sampled from a normal distribution defined
        by configuration parameters.

        Returns:
            float: Simulated temperature (in degrees Celsius).
        """
        return normal(config.ROBOT_DOG_MEAN_TEMPERATURE, config.ROBOT_DOG_TEMPERATURE_STDDEV)
    
    def _move(self) -> None:
        """
        Executes the movement loop.

        This method runs in a background thread. The robot moves toward each
        waypoint incrementally, updating its position at fixed time intervals.
        When a waypoint is reached within a configured tolerance, the
        corresponding callback is triggered. Once all waypoints are processed,
        the finish callback is executed.
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

                step = min(dist, self._speed * config.ROBOT_SLEEP_TIME)
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
