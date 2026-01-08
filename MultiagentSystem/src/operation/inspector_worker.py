"""

Threaded inspector worker of a mission.  

This worker reads points from a queue, plans a path using a path planner, 
commands the robot to inspect the points, and signals completion events.
"""

import threading
import logging
from typing import Dict, Callable, List
from queue import Queue
import winsound
from time import time

from operation.operation_status import Status
from operation.operation_events import OperationEvents
from structures.structures import Point2D
from interfaces.interfaces import IPathPlanner, ARobot


class InspectorWorker(threading.Thread):
    """
    Threaded worker executing missions for a robot.
    """

    def __init__(self, robot: ARobot, planner: IPathPlanner, n_missions: int, points_queue: Queue[Point2D], all_points: Dict[Point2D, (int, bool, float, float)], events: OperationEvents) -> None:
        """
        Creates an InspectorWorker instance.

        Args:
            robot (IRobot): The robot to control.
            planner (IPathPlanner): Planner to determine inspection order.
            n_missions (int): Number of missions to execute.
            points_queue (Queue[Point2D]): Queue with points to inspect.
            all_points (Dict[Point2D, (int, bool, float, float)]): Dictionary of all points detected across missions with their processed status and timestamps when detected and inspected.
            events (OperationEvents): Shared operation synchronization events.
        """
        super().__init__(daemon=True)
        self._robot: ARobot = robot
        self._planner: IPathPlanner = planner
        self._n_missions: int = n_missions
        self._points_queue: Queue[Dict[Point2D, bool]] = points_queue
        self._all_points: Dict[Point2D, (int, bool, float, float)] = all_points
        self.points_temperatures: Dict[Point2D, float] = {}
        self._events: OperationEvents = events

        self.mission_id: int = 0
        self.status: Status = Status.NOT_STARTED

        self._start_time_actual_mission: float = None
        self.times: List[(float, float)] = []

        self._callback_onFinishAll: Callable[[], None] = None

        self._lock: threading.Lock = threading.Lock()

        self._logger: logging.Logger = logging.getLogger("InspectorWorker")

        self._robot.set_callback_onPoint(self._on_point)
        self._robot.set_callback_onFinish(self._on_finish)

    # -------------------
    # Private methods
    # -------------------
    def _on_point(self, point: Point2D) -> None:
        """
        Callback triggered when the robot reaches a point.

        Beeps to signal detection.

        Args:
            point (Point2D): Reached point coordinates.
        """
        self._logger.info("Reached point %s in mission %d. Beeping...", point, self.mission_id)
        winsound.Beep(1000, 200)

        with self._lock:
            if point in self._all_points:
                mission_idx, _, _, _ = self._all_points[point]
                if mission_idx == self.mission_id:
                    self._all_points[point] = (mission_idx, True, self._all_points[point][2], time())
                    self.points_temperatures[point] = self._robot.get_telemetry().get("temperature", None)

    def _on_finish(self) -> None:
        """
        Callback triggered when the robot finishes inspecting all points.
        """
        with self._lock:
            finish_time = time()
            self.times.append((self._start_time_actual_mission, finish_time))  
            self._logger.info("Finished mission %d", self.mission_id)
            self.status = Status.FINISHED
            self._start_time_actual_mission = None
            self._events.trigger_inspector_done()
            self._points_queue.task_done()

    # -------------------
    # Public methods
    # -------------------
    def run(self) -> None:
        """
        Main thread loop executing missions.

        Waits for the next_mission event, plans the path, starts inspection, 
        and waits for the stop_inspection event before finishing the mission.
        """
        while self.mission_id < self._n_missions - 1:
            points = self._points_queue.get()
            if self.status == Status.FINISHED:
                self.mission_id += 1
            self._logger.info("Starting mission %d with %d points", self.mission_id, len(points))
            self._start_time_actual_mission = time()
            self.status = Status.RUNNING
            self._events.clear_inspector_done()
            path = self._planner.plan_path(self._robot.get_current_position(), list(points))
            self._robot.start_inspection(path)
            self._events.wait_for_inspector_done()
            self._robot.stop_inspection()

        self.status = Status.ALL_FINISHED
        self._logger.info("All missions finished.")
        if self._callback_onFinishAll:
            self._callback_onFinishAll()