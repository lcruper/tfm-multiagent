"""
Operation Controller
-----------------------

Coordinates the explorer and inspector workers for an operation.
"""

import json
import os
from time import time
from queue import Queue
import logging
from typing import List, Dict
import threading
from datetime import datetime

from operation.explorer_worker import ExplorerWorker
from operation.inspector_worker import InspectorWorker
from operation.operation_events import OperationEvents
from operation.operation_status import Status
from interfaces.interfaces import IPathPlanner, ARobot
from structures.structures import Point2D
from configuration import operation as config


class OperationController:
    """
    Controller for coordinating explorer and inspector threads.
    """

    def __init__(self, explorer_robot: ARobot, inspector_robot: ARobot, planner: IPathPlanner, base_positions_path: str) -> None:
        """
        Creates an OperationController instance.

        Args:
            explorer_robot (IRobot): Robot for inspection.
            inspector_robot (IRobot): Robot for executing points.
            planner (IPathPlanner): Path planner for inspector robot.
            base_positions (List[Point2D]): Base positions for each mission.
        """        
        self.base_positions: List[Point2D] = self._load_base_positions(base_positions_path)
    
        self._queue: Queue[Dict[Point2D, bool]] = Queue(maxsize=len(self.base_positions))
        self.all_points: Dict[Point2D, (int, bool, time, time)] = {}
        self._events: OperationEvents = OperationEvents()
    
        self.explorer_robot: ARobot = explorer_robot
        self.inspector_robot: ARobot = inspector_robot

        self.status: Status = Status.NOT_STARTED
        self.start_time: float = None
        self.finished_time: float = None

        self.explorer_worker: ExplorerWorker = ExplorerWorker(explorer_robot, self.base_positions, self._queue, self.all_points, self._events)
        self.inspector_worker: InspectorWorker = InspectorWorker(inspector_robot, planner, len(self.base_positions), self._queue, self.all_points, self._events)

        self._lock: threading.Lock = threading.Lock()

        self._logger: logging.Logger = logging.getLogger("OperationController")

    # -------------------
    # Public methods
    # -------------------
    def start(self) -> None:
        """
        Starts both explorer and inspector threads and signals the first mission.
        """
        self.start_time = time()
        self.explorer_worker._callback_onFinishAll = self._on_all_missions_finished
        self.inspector_worker._callback_onFinishAll = self._on_all_missions_finished
        self.status = Status.RUNNING
        self.explorer_worker.start()
        self.inspector_worker.start()
        self._logger.info("Operation started. Triggering first mission...")
        self._events.trigger_next_mission()

    def next_mission(self) -> None:
        """
        Signals to start the next mission.
        """
        self._logger.info("Triggering next mission...")
        self.explorer_worker.start_next_mission()

    def stop_inspection(self) -> None:
        """
        Signals the explorer to stop the current mission.
        """
        self._logger.info("Stopping current inspection...")
        self._events.trigger_stop_inspection()

    # -------------------
    # Internal methods
    # -------------------
    def _load_base_positions(self, path: str) -> List[Point2D]:
        """
        Loads base positions from a JSON file.

        Args:
            path (str): Path to the JSON file.
        Returns:
            List[Point2D]: List of base positions.
        """
        with open(path, "r") as f:
            data = json.load(f)
        base_positions = [Point2D(pos["x"], pos["y"]) for pos in data["base_positions"]]
        return base_positions
    
    def _on_all_missions_finished(self) -> None:
        """
        Callback triggered when all missions are finished.
        """
        with self._lock:
            if self.explorer_worker.status == Status.ALL_FINISHED and self.inspector_worker.status == Status.ALL_FINISHED:
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
            "operation_start_timestamp": ts_to_iso(self.start_time),
            "operation_finished_timestamp": ts_to_iso(self.finished_time),
            "operation_duration": self.finished_time - self.start_time if self.finished_time else None,
            "status": self.status.name,
            "number_of_missions": len(self.base_positions),
            "number_of_points": len(self.explorer_worker._all_points),
            "missions": [],
            "points": []
        }

        for mission_id, base_pos in enumerate(self.base_positions):
            explorer_start, explorer_finish = self.explorer_worker.times[mission_id]
            inspector_start, inspector_finish = self.inspector_worker.times[mission_id]

            operation_data["missions"].append({
                "mission_id": mission_id,
                "mission_base_position": {
                    "x": base_pos.x, 
                    "y": base_pos.y
                },
                "explorer_info": {
                    "start_timestamp": ts_to_iso(explorer_start),
                    "finish_timestamp": ts_to_iso(explorer_finish),
                    "duration": explorer_finish - explorer_start,
                    "relative_start_time": explorer_start - self.start_time,
                    "relative_finish_time": explorer_finish - self.start_time
                },
                "inspector_info": {
                    "start_timestamp": ts_to_iso(inspector_start),
                    "finish_timestamp": ts_to_iso(inspector_finish),
                    "duration": inspector_finish - inspector_start,
                    "relative_start_time": inspector_start - self.start_time,
                    "relative_finish_time": inspector_finish - self.start_time
                }
            })


        for point, (mission_id, _, detected_time, finished_time) in self.explorer_worker._all_points.items():
            operation_data["points"].append({
                "point": {
                    "x": point.x,
                    "y": point.y
                },
                "mission_id": mission_id,
                "detected_timestamp": ts_to_iso(detected_time),
                "detected_relative_time": detected_time - self.start_time,
                "inspected_timestamp": ts_to_iso(finished_time),
                "inspected_relative_time": finished_time - self.start_time,
                "telemetry": {
                    "temperature": self.inspector_worker.points_temperatures.get(point, None)
                },
            })

        timestamp = datetime.fromtimestamp(self.start_time).strftime("%Y_%m_%d_%H_%M_%S")
        os.makedirs(config.METRICS_OUTPUT_FOLDER, exist_ok=True)
        path = f"{config.METRICS_OUTPUT_FOLDER}/{timestamp}.json"

        with open(path, "w") as f:
            json.dump(operation_data, f, indent=4)

        self._logger.info(f"Operation metrics saved to {os.path.abspath(path)}")