import json
import os
from time import time
from queue import Queue
import logging
from typing import List, Dict, Tuple
import threading
from datetime import datetime

from operation.exploration_controller import ExplorationController
from operation.inspection_controller import InspectionController
from operation.operation_events import OperationEvents
from operation.operation_status import OperationStatus
from interfaces.interfaces import IPathPlanner, ARobot
from structures.structures import Point2D
from configuration import operation as config

class OperationController:
    """
    High-level controller responsible for orchestrating the execution of an operation. 
    This includes coordinating the exploration and inspection phases, tracking operation
    status, and saving performance metrics.
    """

    def __init__(self, explorer_robot: ARobot, inspector_robot: ARobot, planner: IPathPlanner, base_positions_path: str) -> None:
        """
        Creates an OperationController instance.

        It loads the base positions from the specified JSON file, creates the ExplorationController and 
        InspectionController instances, creates the queue and events for communication between the two controllers,
        and creates the global dictionary to store all detected points and its status.
        It also initializes the operation status and timing variables and sets the callbacks for mission completion.

        Args:
            explorer_robot (ARobot): Robot responsible for the exploration phase.
            inspector_robot (ARobot): Robot responsible for the inspection phase.
            planner (IPathPlanner): Path planner used by the inspector robot.
            base_positions_path (str): Path to a JSON file containing the coordinates of the base stations for each mission.
        """        
        self.base_positions: List[Point2D] = self._load_base_positions(base_positions_path)
        self._n_missions: int = len(self.base_positions)
    
        self._queue: Queue[Dict[Point2D, bool]] = Queue(maxsize=len(self.base_positions))
        self.all_points: Dict[Point2D, Tuple[int, bool, float, float]] = {}
        self._events: OperationEvents = OperationEvents()
    
        self.explorer_robot: ARobot = explorer_robot
        self.inspector_robot: ARobot = inspector_robot

        self.status: OperationStatus = OperationStatus.NOT_STARTED
        self.start_time: float = None
        self.finished_time: float = None

        self.explorer_worker: ExplorationController = ExplorationController(explorer_robot, self.base_positions, self._queue, self.all_points, self._events)
        self.inspector_worker: InspectionController = InspectionController(inspector_robot, planner, len(self.base_positions), self._queue, self.all_points, self._events)

        self._lock: threading.Lock = threading.Lock()

        self._logger: logging.Logger = logging.getLogger("OperationController")

        self.explorer_worker._callback_onFinishAll = self._on_all_missions_finished
        self.inspector_worker._callback_onFinishAll = self._on_all_missions_finished

    # -------------------------------------------
    # Public methods
    # -------------------------------------------
    def start(self) -> None:
        """
        Starts the operation by launching both exploration and inspection threads
        and triggering the first exploration mission. It also records the start time and updates the operation status.
        """
        self.start_time = time()
        self.status = OperationStatus.RUNNING
        self.explorer_worker.start()
        self.inspector_worker.start()
        self._logger.info("Operation started. Triggering first mission...")
        self._events.trigger_start_next_exploration()

    def next_mission(self) -> None:
        """
        Signals the ExplorationController to start the exploration of its next mission.
        """
        self._logger.info("Triggering next exploration mission...")
        self.explorer_worker.start_next_exploration()

    def stop_inspection(self) -> None:
        """
        Signals the ExplorationController to stop the exploration phase of its current mission.
        """
        self._logger.info("Stopping current inspection...")
        self._events.trigger_stop_exploration()

    # ----------------------------------------
    # Private methods
    # ----------------------------------------
    def _load_base_positions(self, path: str) -> List[Point2D]:
        """
        Loads the coordinates of all base stations of the operation from a JSON file.

        Args:
            path (str): Path to the JSON file containing the coordinates of the base stations.
        Returns:
            List[Point2D]: List of Point2D of the base stations.
        """
        with open(path, "r") as f:
            data = json.load(f)
        base_positions = [Point2D(pos["x"], pos["y"]) for pos in data["base_positions"]]
        return base_positions
    
    def _on_all_missions_finished(self) -> None:
        """
        Callback executed when both the exploration and inspection controllers
        have completed all missions. Updates operation status and triggers metrics saving.
        """
        with self._lock:
            if self.explorer_worker.current_mission_id == self._n_missions-1 and self.explorer_worker.status == OperationStatus.FINISHED and self.inspector_worker.current_mission_id == self._n_missions-1 and self.inspector_worker.status == OperationStatus.FINISHED:
                self.finished_time = time()
                self.status = OperationStatus.FINISHED
                self._logger.info("Operation finished.")
                self._save_metrics()

    def _save_metrics(self) -> None:
        """
        Saves all collected metrics for the operation to a timestamped JSON file.
        Metrics include:
            - Operation start and end timestamps
            - Operation duration and status
            - Number of missions and points
            - For each mission:
                - Mission ID
                - Base station coordinates
                - Exploration and inspection start and end timestamps
                - Exploration and inspection durations
                - Exploration and inspection relative start and end times with respect to operation start time
            - For each detected point:
                - Point coordinates
                - Mission ID
                - Detection and inspection timestamps
                - Detection and inspection relative times with respect to operation start time  
                - Telemetry data (e.g., temperature)
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
            explorer_start, explorer_finish = self.explorer_worker.start_finish_times[mission_id]
            inspector_start, inspector_finish = self.inspector_worker.start_finish_times[mission_id]

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