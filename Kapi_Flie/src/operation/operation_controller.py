"""
Operation Controller
-----------------------

Coordinates the Inspector and Executor workers for an operation.
"""

from time import time
from queue import Queue
import logging
from typing import List, Dict

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
        self._events: OperationEvents = OperationEvents()
    
        self.status: Status = Status.NOT_STARTED
        self.start_time: float = None

        self.inspector: InspectorWorker = InspectorWorker(inspector_robot, base_positions, self._queue, self._events)
        self.executor: ExecutorWorker = ExecutorWorker(executor_robot, planner, len(base_positions), self._queue, self._events)

        self._logger: logging.Logger = logging.getLogger("OperationController")

    # -------------------
    # Public methods
    # -------------------
    def start(self) -> None:
        """
        Starts both inspector and executor threads and signals the first mission.
        """
        self.start_time = time()
        self.inspector._callback_onFinishAll = self._on_all_missions_finished
        self.executor._callback_onFinishAll = self._on_all_missions_finished
        self.status = Status.RUNNING
        self.inspector.start()
        self.executor.start()
        self._logger.info("Operation started. Triggering first mission...")
        self._events.trigger_next_mission()

    def next_mission(self) -> None:
        """
        Signals to start the next mission.
        """
        self._logger.info("Triggering next mission...")
        self.inspector.start_next_mission()

    def stop_inspection(self) -> None:
        """
        Signals the inspector to stop the current mission.
        """
        self._logger.info("Stopping current inspection...")
        self._events.trigger_stop_inspection()

    def shutdown(self) -> None:
        """Stops and safely shuts down the operation."""
        self._logger.info("Shutting down operation...")
        self._events.trigger_stop_inspection()
        self._queue.put(None)
        if self.inspector.is_alive():
            self.inspector.join()
        if self.executor.is_alive():
            self.executor.join()
        self._logger.info("Operation shut down safely.")


    def _on_all_missions_finished(self) -> None:
        """
        Callback triggered when all missions are finished.
        """
        if self.inspector.status == Status.FINISHED and self.executor.status == Status.FINISHED:
            self.status = Status.FINISHED
            self._logger.info("Operation finished.")
