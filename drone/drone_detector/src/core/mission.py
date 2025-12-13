# mission.py
"""
@file mission.py
@brief Mission module orchestrating inspector and executor robots.
"""

from numpy import array
from time import time, sleep
import logging
import threading
from typing import Dict, Tuple, Optional
import winsound
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button

import config 
from interfaces.interfaces import IPathPlanner, IRobot

class Mission:
    """
    @brief Represents a mission where:
           1. The inspector robot inspects an area.
           2. Collects detected points.
           3. The executor robot navigates to those points.
    """
    def __init__(self,
                 inspector: IRobot,
                 executor: IRobot,
                 base_position: Tuple[float, float],
                 planner: IPathPlanner) -> None:
        """
        @brief Constructor.

        @param inspector Robot interface for performing inspection
        @param executor Robot interface for executing the detected path
        @param base_position (x, y) coordinates of the mission base position
        @param planner Path planner to optimize the executor's path
        """
        self.inspector: IRobot = inspector
        self.executor: IRobot = executor
        self.base_position: Tuple[float, float] = base_position
        self.planner: IPathPlanner = planner

        self._absolute_points: Dict[Tuple[float,float], bool] = {}  # Detected points with reached status

        # Synchronization
        self._mission_thread: Optional[threading.Thread] = None
        self._stop_inspection_flag: Optional[threading.Event] = None              # Flag to stop inspection
        self._finished: bool = False
        self._status: str = "Not started"   # Status of the mission

        # Logger
        self._logger: logging.Logger = logging.getLogger("Mission")

    # ---------------------------------------------------------
    # Internal Callbacks
    # ---------------------------------------------------------
    def _on_inspector_point_detected(self, x: float, y: float):
        """
        @brief Callback executed when the inspector detects a new point.

        @param x X coordinate of the detected point
        @param y Y coordinate of the detected point
        """
        abs_x = self.base_position[0] + x
        abs_y = self.base_position[1] + y
        self._absolute_points[(abs_x, abs_y)] = False
        self._logger.info("Inspector detected point at (%.2f, %.2f). Beeping...", abs_x, abs_y)
        winsound.Beep(1000, 200)  # Beep on detecting point
        
    def _on_inspector_finished(self):
        """
        @brief Callback executed when the inspector finishes its inspection.
        """
        self._logger.info("Inspector has finished inspection.")

    def _on_executor_point_reached(self, x: float, y: float):
        """
        @brief Callback executed when the executor reaches each waypoint.

        @param x X coordinate of the reached waypoint
        @param y Y coordinate of the reached waypoint
        """
        self._absolute_points[(x, y)] = True
        self._logger.info("Executor reached waypoint at (%.2f, %.2f). Beeping...", x, y)
        winsound.Beep(1000, 200)  # Beep on reaching point

    def _on_executor_finished(self):
        """
        @brief Callback executed when the executor completes the assigned path.
        """
        self._finished = True
        self._status = "Finished"

    def _reorder_points(self):
        """
        @brief Reorder detected points using the eSHPSolver to minimize path length.
        Updates self._absolute_points to follow optimal tour order.
        """
        if not self._absolute_points:
            return

        points = list(self._absolute_points.keys())
        start_pos = self.executor.get_current_position()

        try:
            ordered_points = self.planner.plan_path(start_pos, points)
            self._absolute_points = {pt: self._absolute_points[pt] for pt in ordered_points}
            self._logger.info("Points reordered using %s planner.",
                            self.planner.__class__.__name__)
        except Exception as e:
            self._logger.error("Error while reordering points: %s", str(e))

    # ---------------------------------------------------------
    # Mission lifecycle
    # ---------------------------------------------------------
    def start(self) -> None:
        """
        @brief Start the mission in a background thread.
        """
        self._logger.info("Starting mission...")

        self._stop_inspection_flag = threading.Event()
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
        # Inspection phase
        self._logger.info("Mission: Starting inspector at %s...", self.base_position)
        self._status = "Inspector"

        self.inspector.set_callback_onPoint(self._on_inspector_point_detected)
        self.inspector.set_callback_onFinish(self._on_inspector_finished)

        self.inspector.start_inspection() 

        while not self._stop_inspection_flag.is_set():
            sleep(config.MISSION_SLEEP_TIME)

        self._logger.info("Mission: Stop button pressed. Stopping inspector.")
        self.inspector.stop_inspection()

        # Execution phase
        if not self._absolute_points:
            self._logger.warning("Mission completed. No points detected by inspector.")
            self._finished = True
            self._status = "Finished"
            return

        self._logger.info("Mission: %d points detected. Sending path to executor.",
                          len(self._absolute_points))
        self._reorder_points()
        self._status = "Executor"

        self.executor.set_callback_onPoint(self._on_executor_point_reached)
        self.executor.set_callback_onFinish(self._on_executor_finished)

        self.executor.start_inspection([(x,y) for x,y in self._absolute_points.keys()])

        self._logger.info("Mission: Waiting for executor to complete path.")
        while not self._finished:
            sleep(config.MISSION_SLEEP_TIME)

        self.executor.stop_inspection()
        self._logger.info("Mission completed successfully.")




    # ---------------------------------------------------------
    # Visualization
    # ---------------------------------------------------------
    def visualizer(self) -> None:
        fig = plt.figure(figsize=(10, 6))

        # Map subplot
        ax_map = fig.add_subplot(1, 2, 1)
        ax_map.set_aspect('equal')
        ax_map.set_xlabel("X")
        ax_map.set_ylabel("Y")
        ax_map.set_title("Mission Map")
        ax_map.set_xlim(self.base_position[0] - 5, self.base_position[0] + 5)
        ax_map.set_ylim(self.base_position[1] - 5, self.base_position[1] + 5)

        # Info subplot
        ax_info = fig.add_subplot(1, 2, 2)
        ax_info.axis("off")
        text_info = ax_info.text(0.02, 0.98, "", va="top", fontsize=12)

        # Buttom Stop Inspector
        ax_button = plt.axes([0.45, 0.01, 0.1, 0.05])
        stop_button = Button(ax_button, "Stop Inspector")

        def stop_inspector(event):
            self._stop_inspection_flag.set()
            stop_button.disconnect_events()  
        stop_button.on_clicked(stop_inspector)

        # Plot base station
        base_x, base_y = self.base_position
        ax_map.plot(base_x, base_y, 'ks', markersize=10, label="Base station")

        inspector_positions = []
        executor_positions = []

        inspector_point, = ax_map.plot([], [], 'bo', markersize=8, label="Inspector")
        executor_point, = ax_map.plot([], [], 'go', markersize=8, label="Executor")
        inspector_path, = ax_map.plot([], [], 'b--', linewidth=1)
        executor_path, = ax_map.plot([], [], 'g--', linewidth=1)

        detected_scatter = ax_map.scatter([], [], s=50)

        start_time = time()

        def distance_traveled(path):
            if len(path) < 2:
                return 0.0
            d = 0.0
            for i in range(1, len(path)):
                dx = path[i][0] - path[i-1][0]
                dy = path[i][1] - path[i-1][1]
                d += (dx**2 + dy**2)**0.5
            return d

        def update(frame):
            # Current positions
            ins_rel_x, ins_rel_y = self.inspector.get_current_position()
            ins_abs = (base_x + ins_rel_x, base_y + ins_rel_y)
            inspector_positions.append(ins_abs)

            exe_abs = self.executor.get_current_position()
            executor_positions.append(exe_abs)

            # Update inspector path
            if inspector_positions:
                xs, ys = zip(*inspector_positions)
                inspector_point.set_data(xs[-1], ys[-1])
                inspector_path.set_data(xs, ys)

            # Update executor path
            if executor_positions:
                ex, ey = zip(*executor_positions)
                executor_point.set_data(ex[-1], ey[-1])
                executor_path.set_data(ex, ey)

            # Detected points
            points = list(self._absolute_points.keys())
            if points:
                coords = array(points)
                colors = ['green' if self._absolute_points[p] else 'red' for p in points]
                detected_scatter.set_offsets(coords)
                detected_scatter.set_color(colors)

            # Time of mission
            elapsed = time() - start_time

            # Distance traveled
            ins_distance = distance_traveled(inspector_positions)
            exe_distance = distance_traveled(executor_positions)

            # Points
            points_text = "\n".join([f"• ({x:.2f}, {y:.2f})" for x, y in points])

            # Info
            info_text = f"""

            Base Position: x={base_x:.2f}, y={base_y:.2f}
            Mission Status: {self._status}
            Elapsed Time: {elapsed:.1f} s

            Inspector Position: x={ins_abs[0]:.2f}, y={ins_abs[1]:.2f}
            Inspector Distance Traveled: {ins_distance:.2f}

            Executor Position: x={exe_abs[0]:.2f}, y={exe_abs[1]:.2f}
            Executor Distance Traveled: {exe_distance:.2f}

            Points Detected: {len(points)}
            {points_text}
            """
            text_info.set_text(info_text)

            return inspector_point, executor_point, detected_scatter

        ani = animation.FuncAnimation(fig, update, interval=100, cache_frame_data=False)
        fig.tight_layout()
        plt.show()