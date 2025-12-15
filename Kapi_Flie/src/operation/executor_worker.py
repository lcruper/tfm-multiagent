"""
Executor Worker
---------------

Threaded executor worker of a mission.  

This worker reads points from a queue, plans a path using a path planner, 
commands the robot to inspect the points, and signals completion events.
"""

import threading
import logging
from typing import Dict, Callable
from queue import Queue
import winsound

from operation.operation_status import Status
from operation.operation_events import OperationEvents
from structures.structures import Point2D
from interfaces.interfaces import IPathPlanner, IRobot


class ExecutorWorker(threading.Thread):
    """
    Threaded worker executing missions for a robot.
    """

    def __init__(self, robot: IRobot, planner: IPathPlanner, n_missions: int, points_queue: Queue[Dict[Point2D, bool]], events: OperationEvents) -> None:
        """
        Creates an ExecutorWorker instance.

        Args:
            robot (IRobot): The robot to control.
            planner (IPathPlanner): Planner to determine inspection order.
            n_missions (int): Number of missions to execute.
            points_queue (Queue[Dict[Point2D, bool]]): Queue with points to inspect.
            events (OperationEvents): Shared operation synchronization events.
        """
        super().__init__(daemon=True)
        self.robot: IRobot = robot
        self.planner: IPathPlanner = planner
        self.n_missions: int = n_missions
        self.points_queue: Queue[Dict[Point2D, bool]] = points_queue
        self.events: OperationEvents = events

        self.mission_id: int = 0
        self.status: Status = Status.NOT_STARTED
        self._callback_onFinishAll: Callable[[], None] = None

        self._logger: logging.Logger = logging.getLogger("ExecutorWorker")

        self.robot.set_callback_onPoint(self._on_point)
        self.robot.set_callback_onFinish(self._on_finish)

    # -------------------
    # Internal methods
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

    def _on_finish(self) -> None:
        """
        Callback triggered when the robot finishes inspecting all points.
        """
        self._logger.info("Finished mission %d", self.mission_id)
        self.status = Status.FINISHED
        self.events.executor_done.set()

    # -------------------
    # Public methods
    # -------------------
    def run(self) -> None:
        """
        Main thread loop executing missions.

        Waits for the next_mission event, plans the path, starts inspection, 
        and waits for the stop_inspection event before finishing the mission.
        """
        while self.mission_id < self.n_missions:
            points = self.points_queue.get()
            if points is None:
                break

            if not points:
                self._logger.info("Skipping empty mission %d", self.mission_id)
                self.status = Status.FINISHED
                self.events.executor_done.set()
                self.points_queue.task_done()
                if self.mission_id < self.n_missions - 1:
                    self.mission_id += 1
                    self.status = Status.NOT_STARTED
                else:
                    break
                continue

            self._logger.info("Starting mission %d with %d points", self.mission_id, len(points))
            self.status = Status.RUNNING
            self.events.executor_done.clear()
            path = self.planner.plan_path(self.robot.get_current_position(), list(points.keys()))
            self.robot.start_inspection(path)
            self.events.executor_done.wait()
            self.robot.stop_inspection()
            self.points_queue.task_done()
            if self.mission_id < self.n_missions - 1:
                self.mission_id += 1
                self.status = Status.NOT_STARTED
            else:
                break

        if self._callback_onFinishAll:
            self._logger.info("All missions completed.")
            self._callback_onFinishAll()