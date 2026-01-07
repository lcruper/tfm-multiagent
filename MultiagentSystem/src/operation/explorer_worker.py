"""
explorer Worker
----------------

Threaded explorer worker controlling missions for a robot.  

This worker listens for operation-level events to start/stop missions and 
pushes detected points into a queue for further processing.
"""

import threading
from typing import Dict, List, Callable
from queue import Queue
import logging
from time import time
import winsound

from configuration import operation as config
from operation.operation_status import Status
from operation.operation_events import OperationEvents
from interfaces.interfaces import ARobot
from structures.structures import Point2D


class ExplorerWorker(threading.Thread):
    """
    Threaded worker controlling missions for a robot explorer.

    The worker handles mission execution by starting the robot inspection, 
    recording detected points, and synchronizing with operation events.
    """

    def __init__(self, robot: ARobot, base_positions: List[Point2D], points_queue: Queue[Point2D], all_points: Dict[Point2D, (int, bool, float, float)], events: OperationEvents) -> None:
        """
        Creates a ExplorerWorker instance.

        Args:
            robot (IRobot): The robot to control.
            base_positions (List[Point2D]): List of base positions for missions.
            points_queue (Queue[Point2D]): Queue for detected points.
            all_points (Dict[Point2D, (int, bool, float, float)]): Dictionary of all points detected across missions with their processed status and timestamps when detected and inspected.
            events (OperationEvents): Shared operation synchronization events.
        """
        super().__init__(daemon=True)
        self._robot: ARobot = robot
        self._base_positions: List[Point2D] = base_positions
        self._points_queue: Queue[Point2D] = points_queue
        self._all_points: Dict[Point2D, (int, bool, float, float)] = all_points
        self._events: OperationEvents = events

        self._actual_points: List[Point2D] = []
        self.mission_id: int = 0
        self.status: Status = Status.NOT_STARTED

        self._start_time_actual_mission: float = None
        self.times: List[(float, float)] = []

        self._callback_onFinishAll: Callable[[], None] = None

        self._lock: threading.Lock = threading.Lock()

        self._logger: logging.Logger = logging.getLogger("ExplorerWorker")

        self._robot.set_callback_onPoint(self._on_point)
        self._robot.set_callback_onFinish(self._on_finish)

    # -------------------
    # Private methods
    # -------------------
    def _on_point(self, point: Point2D) -> None:
        """
        Callback triggered when the robot detects a point.

        The point is adjusted relative to the base position and stored
        in the actual_points dictionary if it is not too close to existing points.

        Args:
            point (Point2D): Detected relative point from the robot.
        """
        abs_point = Point2D(
            self._base_positions[self.mission_id].x + point.x,
            self._base_positions[self.mission_id].y + point.y
        )
        self._logger.info("Detected point at %s in mission %d. Beeping...", abs_point, self.mission_id)
        winsound.Beep(1000, 200)

        with self._lock:
            if not self._is_too_close(abs_point):
                self._actual_points.append(Point2D(abs_point.x, abs_point.y))
                self._all_points[Point2D(abs_point.x, abs_point.y)] = (self.mission_id, False, time(), 0.0)
            else:
                self._logger.info("Skipping point (too close) at %s in mission %d", abs_point, self.mission_id)

    def _on_finish(self) -> None:
        """
        Callback triggered when the robot finishes the current inspection.

        Stores collected points into the queue and clears the internal buffer.
        """
        with self._lock:
            finish_time = time()
            self.times.append((self._start_time_actual_mission, finish_time))
            self._logger.info("Finished mission %d with %d points", self.mission_id, len(self._actual_points))
            self.status = Status.FINISHED
            self._start_time_actual_mission = None
            self._points_queue.put(list(self._actual_points))
            self._actual_points.clear()

    def _is_too_close(self, new_point: Point2D) -> bool:
        """
        Determines if a point is too close to previously detected points.

        Args:
            new_point (Point2D): Candidate point to check.

        Returns:
            bool: True if the point is closer than INSPECTION_POINT_MIN_DIST to any existing point.
        """
        for pt in self._actual_points:
            dist = ((pt.x - new_point.x) ** 2 + (pt.y - new_point.y) ** 2) ** 0.5
            if dist < config.DRONE_VISIBILITY:
                return True
        return False

    # -------------------
    # Public methods
    # -------------------
    def run(self) -> None:
        """
        Main thread loop for mission execution.

        Waits for the next_mission event, starts inspection, and blocks until
        the stop_inspection event is triggered. The robot is then stopped, and
        the worker waits for the next mission.
        """
        while self.mission_id < len(self._base_positions) - 1:
            self._events.wait_for_next_mission()
            self._events.clear_next_mission()
            self._logger.info("Starting mission %d", self.mission_id)
            self.status = Status.RUNNING
            self._start_time_actual_mission = time() 
            self._events.clear_stop_inspection()
            self._robot.start_inspection()
            self._events.wait_for_stop_inspection()
            self._robot.stop_inspection()
            
        self.status = Status.ALL_FINISHED
        self._logger.info("All missions finished.")
        
        if self._callback_onFinishAll:
            self._callback_onFinishAll()

    def start_next_mission(self) -> None:
        """
        Signals the operation to start the next mission.
        """
        self.mission_id += 1
        self._events.trigger_next_mission()
