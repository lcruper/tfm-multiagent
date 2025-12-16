"""
Operation Controller
-----------------------

Coordinates the Inspector and Executor workers for an operation.
"""

from time import time
from queue import Queue
import logging
from typing import List, Dict
import threading

from operation.inspector_worker import InspectorWorker
from operation.executor_worker import ExecutorWorker
from operation.operation_events import OperationEvents
from operation.operation_status import Status
from interfaces.interfaces import IPathPlanner, IRobot
from structures.structures import Point2D


class OperationController:
    """
    Controller for coordinating inspector and executor threads.
    """

    def __init__(self, inspector_robot: IRobot, executor_robot: IRobot, planner: IPathPlanner, base_positions: List[Point2D]) -> None:
        """
        Creates an OperationController instance.

        Args:
            inspector_robot (IRobot): Robot for inspection.
            executor_robot (IRobot): Robot for executing points.
            planner (IPathPlanner): Path planner for executor robot.
            base_positions (List[Point2D]): Base positions for each mission.
        """        
        self._queue: Queue[Dict[Point2D, bool]] = Queue(maxsize=len(base_positions))
        self.all_points: Dict[Point2D, (int, bool)] = {}
        self._events: OperationEvents = OperationEvents()
    
        self.inspector_robot: IRobot = inspector_robot
        self.executor_robot: IRobot = executor_robot
        self.base_positions: List[Point2D] = base_positions

        self.status: Status = Status.NOT_STARTED
        self.start_time: float = None

        self.inspector_worker: InspectorWorker = InspectorWorker(inspector_robot, base_positions, self._queue, self.all_points, self._events)
        self.executor_worker: ExecutorWorker = ExecutorWorker(executor_robot, planner, len(base_positions), self._queue, self.all_points, self._events)

        self._lock: threading.Lock = threading.Lock()

        self._logger: logging.Logger = logging.getLogger("OperationController")

    # -------------------
    # Public methods
    # -------------------
    def start(self) -> None:
        """
        Starts both inspector and executor threads and signals the first mission.
        """
        self.start_time = time()
        self.inspector_worker._callback_onFinishAll = self._on_all_missions_finished
        self.executor_worker._callback_onFinishAll = self._on_all_missions_finished
        self.status = Status.RUNNING
        self.inspector_worker.start()
        self.executor_worker.start()
        self._logger.info("Operation started. Triggering first mission...")
        self._events.trigger_next_mission()

    def next_mission(self) -> None:
        """
        Signals to start the next mission.
        """
        self._logger.info("Triggering next mission...")
        self.inspector_worker.start_next_mission()

    def stop_inspection(self) -> None:
        """
        Signals the inspector to stop the current mission.
        """
        self._logger.info("Stopping current inspection...")
        self._events.trigger_stop_inspection()

    def shutdown(self) -> None:
        """Stops and safely shuts down the operation."""
        self._logger.info("Shutting down operation...")
        # TODO
        self._logger.info("Operation shut down safely.")
        
    # -------------------
    # Internal methods
    # -------------------
    def _on_all_missions_finished(self) -> None:
        """
        Callback triggered when all missions are finished.
        """
        with self._lock:
            if self.inspector_worker.mission_id == len(self.base_positions)-1 and self.executor_worker.mission_id == len(self.base_positions)-1:
                self.status = Status.FINISHED
                self._logger.info("Operation finished.")
