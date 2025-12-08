# mission.py
"""
@file mission.py
@brief Mission module orchestrating inspector and executor robots.
"""
import logging
import threading
import time
from typing import Tuple, Optional
import winsound

from interfaces.interfaces import IRobot


class Mission:
    """
    @brief Represents a mission where:
           1. The inspector robot inspects for a time window.
           2. Collects detected points.
           3. The executor robot executes the path.
    """
    def __init__(self,
                 inspector: IRobot,
                 executor: IRobot,
                 base_position: Tuple[float, float],
                 inspection_duration: float) -> None:
        """
        @brief Constructor.

        @param inspector Robot interface for performing inspection
        @param executor Robot interface for executing the detected path
        @param base_position (x, y) coordinates of the mission base position
        @param inspection_duration Duration in seconds for the inspector to run
        """
        self.inspector: IRobot = inspector
        self.executor: IRobot = executor
        self.base_position: Tuple[float, float] = base_position
        self.inspection_duration: float = inspection_duration

        # Synchronization
        self._mission_thread: Optional[threading.Thread] = None
        self._finished: bool = False

        # Logger
        self._logger: logging.Logger = logging.getLogger("Mission")

    # ---------------------------------------------------------
    # Internal Callbacks
    # ---------------------------------------------------------
    def _on_executor_finished(self):
        """
        @brief Callback executed when the executor completes the assigned path.
        """
        self._finished = True

    def _on_executor_point_reached(self, x: float, y: float):
        """
        @brief Callback executed when the executor reaches each waypoint.

        @param x X coordinate of the reached waypoint
        @param y Y coordinate of the reached waypoint
        """
        self._logger.info("Executor reached waypoint at (%.2f, %.2f). Beeping...", x, y)
        winsound.Beep(1000, 200)  # Beep on reaching point

    # ---------------------------------------------------------
    # Mission lifecycle
    # ---------------------------------------------------------
    def start(self) -> None:
        """
        @brief Start the mission in a background thread.
        """
        self._logger.info("Starting mission...")
        self._mission_thread = threading.Thread(target=self._run, daemon=True)
        self._mission_thread.start()

    def wait_until_finished(self) -> None:
        """
        @brief Blocks until the mission is completely done.
        """
        if self._mission_thread:
            self._mission_thread.join()

    # ---------------------------------------------------------
    # Mission core logic
    # ---------------------------------------------------------
    def _run(self) -> None:
        """
        @brief Orchestrates the full mission workflow.
        """
        # Step 1 — Start inspector
        self._logger.info("Mission: Starting inspector for %.2f seconds at %s...",
                          self.inspection_duration, self.base_position)

        self.inspector.start_inspection()  # Inspector starts collecting points

        # Inspection time window
        time.sleep(self.inspection_duration)

        # Step 2 — Stop inspector
        self._logger.info("Mission: Stopping inspector.")
        points = self.inspector.stop_inspection()

        # Step 3 — Send detected points to executor
        if not points:
            self._logger.warning("Mission completed. No points detected by inspector.")
            self._finished = True
            return

        self._logger.info("Mission: %d points detected. Sending path to executor.",
                          len(points))

        self.executor.set_callback_onPoint(self._on_executor_point_reached)
        self.executor.set_callback_onFinish(self._on_executor_finished)

        self.executor.start_inspection(points)

        # Step 4 — Wait for executor to finish
        self._logger.info("Mission: Waiting for executor to complete path.")
        while not self._finished:
            time.sleep(0.1)

        self.executor.stop_inspection()
        self._logger.info("Mission completed successfully.")
