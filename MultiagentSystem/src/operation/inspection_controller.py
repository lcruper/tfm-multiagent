import threading
import logging
from typing import Dict, Callable, List, Tuple
from queue import Queue
import winsound
from time import time

from operation.operation_status import OperationStatus
from operation.operation_events import OperationEvents
from structures.structures import Point2D
from interfaces.interfaces import IPathPlanner, ARobot

class InspectionController(threading.Thread):
    """
    Controller for managing the inspection phases of missions in a multi-agent operation.

    This class runs as a separate thread and orchestrates the execution of inspection
    phases performed by a inspector agent. It ensures that the execution of the inspection phases is sequential and it respects the order of the missions. 
    """

    def __init__(self, robot: ARobot, planner: IPathPlanner, n_missions: int, points_queue: Queue[Point2D], all_points: Dict[Point2D, Tuple[int, bool, float, float]], events: OperationEvents) -> None:
        """
        Creates an InspectionController instance.

        It creates and initializes all the internal status variables associated with a mission that is currently running
        and sets up the necessary callbacks.

        Args:
            robot (ARobot): Robot instance that performs the inspection.
            planner (IPathPlanner): Path planner used to generate inspection paths.
            n_missions (int): Total number of missions to perform.
            points_queue (Queue[Point2D]): Queue of points to inspect, shared with the ExplorationController.
            all_points (Dict[Point2D, Tuple[int, bool, float, float]]):Dictionary storing all detected points across missions, including:
                           (mission_id, processed_flag, detection_time, inspection_time)
            events (OperationEvents): Shared operation events for synchronizing exploration and inspection phases.
        """
        super().__init__(daemon=True)
        self._robot: ARobot = robot
        self._planner: IPathPlanner = planner
        self._n_missions: int = n_missions
        self._points_queue: Queue[Dict[Point2D, bool]] = points_queue
        self._all_points: Dict[Point2D, Tuple[int, bool, float, float]] = all_points
        self.points_temperatures: Dict[Point2D, float] = {}
        self._events: OperationEvents = events

        self.current_mission_id: int = 0
        self.status: OperationStatus = OperationStatus.NOT_STARTED
        self._start_time_current_mission: float = None
        self.start_finish_times: List[(float, float)] = []

        self._callback_onFinishAll: Callable[[], None] = None

        self._lock: threading.Lock = threading.Lock()

        self._logger: logging.Logger = logging.getLogger("InspectionController")

        self._robot.set_callback_onPoint(self._on_point)
        self._robot.set_callback_onFinish(self._on_finish)

    # ------------------------------------------------
    # Public methods
    # ------------------------------------------------
    def run(self) -> None:
        """
        Main thread execution loop.

        For each inspection:
            1. Retrieves points from the shared queue, if there are no points, it waits.
            2. Sets the status to RUNNING.
            3. Records the start time.
            4. Uses the path planner to compute an inspection path.
            5. Starts the robot's inspection routine along the planned path.
            6. Waits for the inspection routine to complete via the operation event `inspector_done`.

        Once all missions have been completed, the controller marks itself as FINISHED
        and triggers the optional completion callback.
        """
        while self.current_mission_id < self._n_missions - 1:
            points = self._points_queue.get()
            self._logger.info("Starting mission %d with %d points", self.current_mission_id, len(points))
            with self._lock:
                if self.status != OperationStatus.NOT_STARTED:
                    self.current_mission_id += 1
                self.status = OperationStatus.RUNNING
                self._start_time_current_mission = time()
            path = self._planner.plan_path(self._robot.get_current_position(), list(points))
            self._robot.start_routine(path)
            self._events.wait_for_inspector_done()
            self._events.clear_inspector_done()
            self._robot.stop_routine()

        with self._lock:
            self.status = OperationStatus.FINISHED
        self._logger.info("All missions finished.")

        if self._callback_onFinishAll:
            self._callback_onFinishAll()

    # ------------------------------------------
    # Private methods
    # ------------------------------------------
    def _on_point(self, point: Point2D) -> None:
        """
        Internal callback triggered when the robot reaches a point.

        Updates the status of the point to inspected and records the temperature if available.

        Args:
            point (Point2D): The point reached by the robot during inspection.
        """
        self._logger.info("Reached point %s in mission %d. Beeping...", point, self.current_mission_id)
        winsound.Beep(1000, 200)

        with self._lock:
            if point in self._all_points:
                mission_idx, _, _, _ = self._all_points[point]
                if mission_idx == self.current_mission_id:
                    self._all_points[point] = (mission_idx, True, self._all_points[point][2], time())
                    self.points_temperatures[point] = self._robot.get_telemetry().get("temperature", None)

    def _on_finish(self) -> None:
        """
        Internal callback triggered when the robot finishes the current inspection routine.

        Updates the mission status, records finish time, signals the event to release waiting threads,
        and marks the points queue task as done.
        """
        with self._lock:
            finish_time = time()
            self.status = OperationStatus.FINISHED
            self.start_finish_times.append((self._start_time_current_mission, finish_time))  
            self._logger.info("Finished mission %d", self.current_mission_id)
            self._start_time_current_mission = None
            self._events.trigger_inspector_done()
            self._points_queue.task_done()