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
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

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
        self._stop_visualizer = True 

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
        points = [
            {
                "x": self.base_position[0] + p["x"],
                "y": self.base_position[1] + p["y"]
            }
            for p in points
        ]

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

    # ---------------------------------------------------------
    # Visualization
    # ---------------------------------------------------------
    def visualizer(self) -> None:
        """
        @brief Launch a real-time visualizer showing inspector and executor paths.
        """
        fig, ax = plt.subplots()
        ax.set_aspect('equal')
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title("Mission Visualizer")
        ax.set_xlim(self.base_position[0] - 10, self.base_position[0] + 10)
        ax.set_ylim(self.base_position[1] - 10, self.base_position[1] + 10)

        # Base station
        base_x, base_y = self.base_position
        ax.plot(base_x, base_y, 'ks', markersize=10, label="Base Station")

        # Paths and points
        inspector_positions = []
        executor_positions = []
        detected_points_history = []

        inspector_point, = ax.plot([], [], 'bo', markersize=8, label="Inspector")
        executor_point, = ax.plot([], [], 'go', markersize=8, label="Executor")
        inspector_path, = ax.plot([], [], 'b--', linewidth=1)
        executor_path, = ax.plot([], [], 'g--', linewidth=1)
        detected_points_scatter = ax.scatter([], [], c="red", s=60, label="Detected Points")

        last_detected_count = 0
        blink_counter = 0

        def update(frame):
            nonlocal blink_counter, last_detected_count
            
            # Relative position of inspector
            inspector_rel_x, inspector_rel_y = self.inspector.get_current_position()
            # Absolute position of inspector
            inspector_x = base_x + inspector_rel_x
            inspector_y = base_y + inspector_rel_y

            inspector_positions.append((inspector_x, inspector_y))

            # Absolute position of executor
            executor_x, executor_y = self.executor.get_current_position()
            executor_positions.append((executor_x, executor_y))

            if inspector_positions:
                dx, dy = zip(*inspector_positions)
                inspector_point.set_data(dx[-1], dy[-1])
                inspector_path.set_data(dx, dy)
            if executor_positions:
                ex, ey = zip(*executor_positions)
                executor_point.set_data(ex[-1], ey[-1])
                executor_path.set_data(ex, ey)

            # Update detected points
            detected = getattr(self.inspector, "_detected_points", [])
            if detected:
                if len(detected) > last_detected_count:
                    new_points = detected[last_detected_count:]
                    for p in new_points:
                        detected_points_history.append((p['x'] + base_x, p['y'] + base_y))
                    last_detected_count = len(detected)

            if detected_points_history:
                detected_points_scatter.set_offsets(detected_points_history)
                detected_points_scatter.set_color('red')
            else:
                detected_points_scatter.set_offsets(np.empty((0, 2)))

            if blink_counter > 0:
                blink_counter -= 1

            return inspector_point, executor_point, inspector_path, executor_path, detected_points_scatter

        ani = animation.FuncAnimation(fig, update, interval=100, cache_frame_data=False)
        ax.legend()
        plt.show()
