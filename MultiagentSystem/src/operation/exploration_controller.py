import threading
from typing import Dict, List, Callable, Tuple
from queue import Queue
import logging
from time import time
import winsound

from configuration import operation as config
from operation.operation_status import OperationStatus
from operation.operation_events import OperationEvents
from interfaces.interfaces import ARobot
from structures.structures import Point2D

class ExplorationController(threading.Thread):
    """
    Controller for managing the exploration phases of missions in a the multi-agent operation.

    This class runs as a separate thread and orchestrates the execution of exploration
    phases performed by a explorer agent. It handles starting and stopping the
    exploration routine, recording detected points, and synchronizing with the operation-level
    events to ensure safe and ordered execution.
    """

    def __init__(self, robot: ARobot, base_positions: List[Point2D], points_queue: Queue[Point2D], all_points: Dict[Point2D, Tuple[int, bool, float, float]], events: OperationEvents) -> None:
        """
        Creates an ExplorationController instance.

        It creates and initializes all the internal status variables associated with a mission that is currently running
        and sets up the necessary callbacks.

        Args:
            robot (ARobot): Robot instance that performs the exploration.
            base_positions (List[Point2D]): List of positions corresponding to the base stations from which exploration phases start.
            points_queue (Queue[Point2D]): Queue for sending detected points during exploration to the inspection controller.
            all_points (Dict[Point2D, Tuple[int, bool, float, float]]): Dictionary storing all detected points across missions, including:
                           (mission_id, processed_flag, detection_time, inspection_time)
            events (OperationEvents): Shared operation events for synchronizing exploration and inspection phases.
        """
        super().__init__(daemon=True)
        self._robot: ARobot = robot
        self._base_positions: List[Point2D] = base_positions
        self._n_missions: int = len(base_positions)
        self._points_queue: Queue[Point2D] = points_queue
        self._all_points: Dict[Point2D, Tuple[int, bool, float, float]] = all_points
        self._events: OperationEvents = events

        self.current_mission_id: int = 0
        self.status: OperationStatus = OperationStatus.NOT_STARTED
        self.start_finish_times: List[(float, float)] = []

        self._points_current_mission: List[Point2D] = []

        self._callback_onFinishAll: Callable[[], None] = None

        self._lock: threading.RLock = threading.RLock()

        self._logger: logging.Logger = logging.getLogger("ExplorationController")

        self._robot.set_callback_onPoint(self._on_point)

    # -----------------------------------------------------------------
    # Public methods
    # -----------------------------------------------------------------
    def run(self) -> None:
        """
        Main thread execution loop.

        Waits for the `start_next_exploration` event to begin the exploration phase of each mission. 
        For each phase, it:
            1. Sets the status to RUNNING.
            2. Records the start time.
            3. Starts the robot's exploration routine.
            4. Waits for the `stop_exploration` event to stop the routine.
            5. Records the finish time.
            6. Sets status to FINISHED.
            7. Pushes the detected points (in absolute coordinates) to the shared queue.
        
        Once all missions have been completed, the controller marks itself as FINISHED
        and triggers the optional completion callback.
        """
        while self.current_mission_id < self._n_missions - 1:
            self._events.wait_for_start_next_exploration()
            self._events.clear_start_next_exploration()
            self._logger.info("Starting mission %d", self.current_mission_id)
            with self._lock:
                self.status = OperationStatus.RUNNING
            start_time = time() 
            self._robot.start_routine()
            self._events.wait_for_stop_exploration()
            self._events.clear_stop_exploration()
            self._robot.stop_routine()
            finish_time = time()
            with self._lock:
                self.status = OperationStatus.FINISHED
                self.start_finish_times.append((start_time, finish_time))
                self._points_queue.put(list(self._points_current_mission))
                self._logger.info("Finished mission %d with %d points", self.current_mission_id, len(self._points_current_mission))
                self._points_current_mission.clear()

        with self._lock:
            self.status = OperationStatus.FINISHED
        self._logger.info("All missions finished.")
        
        if self._callback_onFinishAll:
            self._callback_onFinishAll()

    def start_next_exploration(self) -> None:
        """
        Signals the controller to start the next exploration only if there are remaining missions and the current mission is not running.
        """
        with self._lock:
            if self.current_mission_id >= self._n_missions-1:
                self._logger.warning("All exploration missions have already been completed.")
                return
            if self.status == OperationStatus.RUNNING:
                self._logger.warning("Cannot start next exploration while current mission is still running.")
                return
            self.current_mission_id += 1
        self._events.trigger_start_next_exploration()


    # ----------------------------------------------------
    # Private methods
    # ----------------------------------------------------
    def _on_point(self, point: Point2D) -> None:
        """
        Internal callback triggered when the robot detects a point.

        Converts the detected point to absolute coordinates, checks for proximity to
        existing points, and stores it in both the current mission list and the global dictionary.

        Args:
            point (Point2D): Relative point detected by the robot.
        """
        x_abs = self._base_positions[self.current_mission_id].x + point.x
        y_abs = self._base_positions[self.current_mission_id].y + point.y
        self._logger.info("Detected point at (%s, %s) in mission %d. Beeping...", x_abs, y_abs, self.current_mission_id)
        winsound.Beep(1000, 200)

        with self._lock:
            if not self._is_too_close(x_abs, y_abs):
                point = Point2D(x_abs, y_abs)
                self._points_current_mission.append(point)
                self._all_points[point] = (self.current_mission_id, False, time(), 0.0)
            else:
                self._logger.info("Skipping point (too close) at (%s, %s) in mission %d", x_abs, y_abs, self.current_mission_id)


    def _is_too_close(self, x: float, y: float) -> bool:
        """
        Determines if a point is too close to previously recorded points in the current mission.

        Args:
            x (float): X coordinate of the point to check.
            y (float): Y coordinate of the point to check.

        Returns:
            bool: True if the point is closer than DRONE_VISIBILITY to any existing point.
        """
        with self._lock:
            for pt in self._points_current_mission:
                dist = ((pt.x - x) ** 2 + (pt.y - y) ** 2) ** 0.5
                if dist < config.DRONE_VISIBILITY:
                    return True
        return False