# mission.py

from numpy import array
from time import time, sleep
import logging
import threading
from typing import Dict, Tuple, Optional, List
import winsound
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button

import config 
from interfaces.interfaces import IPathPlanner, IRobot

class Mission:
    def __init__(self,
                 inspector: IRobot,
                 executor: IRobot,
                 base_positions: List[Tuple[float, float]],
                 planner: IPathPlanner) -> None:
        
        self.inspector: IRobot = inspector
        self.executor: IRobot = executor
        self.base_positions: List[Tuple[float, float]] = base_positions
        self.planner: IPathPlanner = planner

        self._id_missionInspector: int = 0
        self._id_missionExecutor: int = 0

        self._status: str = "Not started"
        self._inspectorStatus = "Stopped"
        self._executorStatus = "Stopped"

        self._absolute_points: Dict[Tuple[float,float], bool] = {}  

        # Synchronization
        self._mission_thread: Optional[threading.Thread] = None
        self._stop_inspection_flag: Optional[threading.Event] = None    

        # Logger
        self._logger: logging.Logger = logging.getLogger("Mission")

    # ---------------------------------------------------------
    # Internal Callbacks
    # ---------------------------------------------------------
    def _on_inspector_point_detected(self, x: float, y: float):
        abs_x = self.base_positions[self._id_missionInspector][0] + x
        abs_y = self.base_positions[self._id_missionInspector][1] + y
        self._absolute_points[(abs_x, abs_y)] = False
        self._logger.info("Inspector detected point in mission %d at (%.2f, %.2f). Beeping...", self._id_missionInspector, abs_x, abs_y)
        winsound.Beep(1000, 200) 
        
    def _on_inspector_finished(self):
        self._inspectorStatus = "Stopped"
        self._logger.info("Inspector has finished mission %d.", self._id_missionInspector)

    def _on_executor_point_reached(self, x: float, y: float):
        self._absolute_points[(x, y)] = True
        self._logger.info("Executor reached waypoint in mission %d at (%.2f, %.2f). Beeping...", self._id_missionExecutor, x, y)
        winsound.Beep(1000, 200)  

    def _on_executor_finished(self):
        self._executorStatus = "Stopped"
        self._logger.info("Executor has finished mission %d.", self._id_missionExecutor)

    # ---------------------------------------------------------
    # Button Callbacks
    # ---------------------------------------------------------
    def start(self, event) -> None:
        self._logger.info("Starting mission...")
        
        self._status = "Started"
        self.inspector.set_callback_onPoint(self._on_inspector_point_detected)
        self.inspector.set_callback_onFinish(self._on_inspector_finished)
        self.executor.set_callback_onPoint(self._on_executor_point_reached)
        self.executor.set_callback_onFinish(self._on_executor_finished)

        self._stop_inspection_flag = threading.Event()
        self._mission_thread = threading.Thread(target=self._run, daemon=True)
        self._mission_thread.start()

    def _stop_inspector(self, event) -> None:
        if not self._stop_inspection_flag.is_set():
            self._logger.info("Stopping inspector at mission %d...", self._id_missionInspector)
            self._stop_inspection_flag.set()
            self._inspectorStatus = "Stopped"

    def _start_next_mission(self, event) -> None:
        if self._stop_inspection_flag.is_set() and self._id_missionInspector + 1 < len(self.base_positions):
            self._logger.info("Starting next mission %d...", self._id_missionInspector)
            self._id_missionInspector += 1 
            self._stop_inspection_flag.clear()  
            self.inspector.start_inspection()
            self._inspectorStatus = "Running"


    # ---------------------------------------------------------
    # Path Planning
    # ---------------------------------------------------------
    def _reorder_points(self):
        """
        @brief Reorder detected points to minimize path length.
        Updates self._absolute_points to follow optimal tour order.
        """
        if not self._absolute_points:
            return

        points = list(self._absolute_points.keys())
        start_pos = self.executor.get_current_position()

        try:
            ordered_points = self.planner.plan_path(start_pos, points)
            self._absolute_points = {pt: self._absolute_points[pt] for pt in ordered_points}
            self._logger.info("Points reordered using %s planner.", self.planner.__class__.__name__)
        except Exception as e:
            self._logger.error("Error while reordering points: %s", str(e))

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------

    def wait_until_finished(self) -> None:
        if self._mission_thread:
            self._mission_thread.join()

    # ---------------------------------------------------------
    # Mission core logic
    # ---------------------------------------------------------
    def _run(self) -> None:
        while self._id_missionInspector < len(self.base_positions):
            while self._stop_inspection_flag is not None and self._stop_inspection_flag.is_set():
                sleep(config.MISSION_SLEEP_TIME)
                continue

            if self._id_missionInspector >= len(self.base_positions):
                break

            base_idx = self._id_missionInspector
            self._logger.info("Starting inspector in mission %d...", base_idx)
            self._inspectorStatus = "Running"
            self.inspector.start_inspection()

            while not self._stop_inspection_flag.is_set():
                sleep(config.MISSION_SLEEP_TIME)

            self.inspector.stop_inspection()
            self._inspectorStatus = "Stopped"
            self._logger.info("Inspector stopped in mission %d.", base_idx)

        # Execution phase
        if not self._absolute_points:
            self._logger.warning("Mission completed. No points detected by inspector.")
            self._finished = True
            return

        self._logger.info("Mission: %d points detected. Sending path to executor.",
                          len(self._absolute_points))
        self._reorder_points()

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
        ax_map.set_xlim(min(x for x, _ in self.base_positions) - 5, max(x for x, _ in self.base_positions) + 5)
        ax_map.set_ylim(min(y for _, y in self.base_positions) - 5, max(y for _, y in self.base_positions) + 5)

        # Base stations
        base_markers = []
        for idx, (bx, by) in enumerate(self.base_positions):
            color = 'lightblue' if idx == self._id_missionInspector else 'k'
            marker, = ax_map.plot(bx, by, 's', color=color, markersize=8)
            ax_map.text(bx + 0.3, by + 0.3, str(idx), color='black', fontsize=12)
            base_markers.append(marker)

        # Info subplot
        ax_info = fig.add_subplot(1, 2, 2)
        ax_info.axis("off")
        text_info = ax_info.text(0.02, 0.98, "", va="top", fontsize=12)

        # Buttom Start
        ax_start = plt.axes([0.45, 0.01, 0.1, 0.05])
        start_button = Button(ax_start, "Start")
        start_button.on_clicked(self.start)
        start_button.ax.set_visible(True)

        # Buttom Stop Inspector
        ax_button = plt.axes([0.45, 0.01, 0.1, 0.05])
        stop_button = Button(ax_button, "Stop Inspector")
        stop_button.on_clicked(self._stop_inspector)
        stop_button.ax.set_visible(False)

        # Buttom Start Next Base
        ax_next_button = plt.axes([0.45, 0.01, 0.1, 0.05])
        next_button = Button(ax_next_button, "Next mission")
        next_button.on_clicked(self._start_next_mission)
        next_button.ax.set_visible(False)

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
            # Base station
            base_x, base_y = self.base_positions[self._id_missionInspector]
            for idx, marker in enumerate(base_markers):
                marker.set_color('lightblue' if idx == self._id_missionInspector else 'k')

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

            # Buttons
            start_button.ax.set_visible(self._inspectorStatus == "Stopped" and self._status == "Not started" and self._id_missionInspector + 1 < len(self.base_positions))
            stop_button.ax.set_visible(self._inspectorStatus == "Running")
            next_button.ax.set_visible(self._inspectorStatus == "Stopped" and self._status == "Started" and self._id_missionInspector + 1 < len(self.base_positions))

            # Status
            inspector_color = 'green' if self._inspectorStatus == "Running" else 'red'
            executor_color = 'green' if self._executorStatus == "Running" else 'red'

                # Time of mission
            elapsed = time() - start_time

            # Distance traveled
            ins_distance = distance_traveled(inspector_positions)
            exe_distance = distance_traveled(executor_positions)

            # Points
            points_text = "\n".join([f"• ({x:.2f}, {y:.2f})" for x, y in points])

            # Info
            info_text = f"""

            Time: {elapsed:.1f} s

            Drone ID Mission: {self._id_missionInspector}
            Drone Base Station: x={base_x:.2f}, y={base_y:.2f}
            Drone Status: {self._inspectorStatus}
            Drone Position: x={ins_abs[0]:.2f}, y={ins_abs[1]:.2f}
            Drone Distance: {ins_distance:.2f}

            Robot dog ID Mission: {self._id_missionExecutor}
            Robot dog Status: {self._executorStatus}
            Robot dog Position: x={exe_abs[0]:.2f}, y={exe_abs[1]:.2f}
            Robot dog Distance: {exe_distance:.2f}

            Points Detected: {len(points)}
            {points_text}
            """
            text_info.set_text(info_text)
            text_info.set_color('black')

            return inspector_point, executor_point, detected_scatter

        ani = animation.FuncAnimation(fig, update, interval=100, cache_frame_data=False)
        fig.tight_layout()
        plt.show()