"""
Operation Controller
-----------------------

Coordinates the Inspector and Executor workers for an operation.
"""

import json
import os
from time import time
from queue import Queue
import logging
from typing import List, Dict
import threading
from datetime import datetime

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
        self.all_points: Dict[Point2D, (int, bool, time, time)] = {}
        self._events: OperationEvents = OperationEvents()
    
        self.inspector_robot: IRobot = inspector_robot
        self.executor_robot: IRobot = executor_robot
        self.base_positions: List[Point2D] = base_positions

        self.status: Status = Status.NOT_STARTED
        self.start_time: float = None
        self.finished_time: float = None

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

    # -------------------
    # Internal methods
    # -------------------
    def _on_all_missions_finished(self) -> None:
        """
        Callback triggered when all missions are finished.
        """
        with self._lock:
            if self.inspector_worker.status == Status.ALL_FINISHED and self.executor_worker.status == Status.ALL_FINISHED:
                self.finished_time = time()
                self.status = Status.FINISHED
                self._logger.info("Operation finished.")
                self._save_metrics()

    def _save_metrics(self) -> None:
        """
        Saves all the collected metrics to a JSON file.
        """
        def ts_to_iso(ts: float) -> str:
            return datetime.fromtimestamp(ts).isoformat() if ts else None

        operation_data = {
            "operation_start_time": ts_to_iso(self.start_time),
            "operation_finished_time": ts_to_iso(self.finished_time),
            "operation_duration": self.finished_time - self.start_time if self.finished_time else None,
            "status": self.status.name,
            "number_of_missions": len(self.base_positions),
            "number_of_points": len(self.inspector_worker._all_points),
            "missions": [],
            "points": []
        }

        for mission_id, base_pos in enumerate(self.base_positions):
            inspector_start, inspector_finish = self.inspector_worker.times[mission_id]
            executor_start, executor_finish = self.executor_worker.times[mission_id]

            operation_data["missions"].append({
                "mission_id": mission_id,
                "mission_base_position": {
                    "x": base_pos.x, 
                    "y": base_pos.y
                },
                "inspector_info": {
                    "start_time": ts_to_iso(inspector_start),
                    "finish_time": ts_to_iso(inspector_finish),
                    "duration": inspector_finish - inspector_start,
                    "relative_start_time": inspector_start - self.start_time,
                    "relative_finish_time": inspector_finish - self.start_time
                },
                "executor_info": {
                    "start_time": ts_to_iso(executor_start),
                    "finish_time": ts_to_iso(executor_finish),
                    "duration": executor_finish - executor_start,
                    "relative_start_time": executor_start - self.start_time,
                    "relative_finish_time": executor_finish - self.start_time
                }
            })


        for point, (mission_id, _, detected_time, finished_time) in self.inspector_worker._all_points.items():
            operation_data["points"].append({
                "point": {
                    "x": point.x,
                    "y": point.y
                },
                "mission_id": mission_id,
                "detected_time": ts_to_iso(detected_time),
                "inspected_time": ts_to_iso(finished_time),
                "telemetry": {
                    "temperature": self.executor_worker.points_temperatures.get(point, None)
                },
            })

        timestamp = datetime.fromtimestamp(self.start_time).strftime("%Y_%m_%d_%H_%M_%S")
        os.makedirs("results", exist_ok=True)
        path = f"results/{timestamp}.json"

        with open(path, "w") as f:
            json.dump(operation_data, f, indent=4)

        self._logger.info(f"Operation metrics saved to {os.path.abspath(path)}")