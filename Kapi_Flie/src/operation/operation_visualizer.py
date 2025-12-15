"""
Operation Visusualizer
---------------------

Provides a visual interface to monitor and control the operation execution.
"""

import matplotlib.pyplot as plt
from matplotlib import patches
import matplotlib.animation as animation
from matplotlib.widgets import Button
from numpy import array
from time import time
from typing import List

import config
from operation.operation_status import Status
from operation.operation_controller import OperationController
from structures.structures import Point2D


class OperationVisualizer:
    """
    Visualizer for operation execution.

    Displays the inspector and executor positions, 
    detected points, and allows controlling missions with buttons.
    """

    def __init__(self, controller: OperationController) -> None:
        """
        Creates an OperationVisualizer instance.
        Args:
            controller (OperationController): The operation controller to visualize.
        """
        self.controller: OperationController = controller
        self._inspector_positions: List[Point2D] = []
        self._executor_positions: List[Point2D] = []

    def _distance_traveled(self, path: List[Point2D]) -> float:
        """
        Computes the total distance traveled along a path.
        Args:
            path (List[Point2D]): List of points representing the path.
        Returns:
            float: Total distance traveled.
        """
        if len(path) < 2:
            return 0.0
        d = 0.0
        for i in range(1, len(path)):
            dx = path[i].x - path[i - 1].x
            dy = path[i].y - path[i - 1].y
            d += (dx ** 2 + dy ** 2) ** 0.5
        return d
    

    def start(self) -> None:
        fig = plt.figure(figsize=(12, 6))
        fig.canvas.manager.set_window_title("Operation Visualizer - Drone & Robot Dog")

        # ----------------------------
        # Operation map
        # ----------------------------
        ax_map = fig.add_subplot(1, 2, 1)
        ax_map.set_aspect('equal')
        ax_map.set_xlabel("X")
        ax_map.set_ylabel("Y")
        ax_map.set_title("Operation Map")

        base_positions = self.controller.inspector.base_positions
        ax_map.set_xlim(min(p.x for p in base_positions) - 5, max(p.x for p in base_positions) + 5)
        ax_map.set_ylim(min(p.y for p in base_positions) - 5, max(p.y for p in base_positions) + 5)

        # Base stations
        base_markers = []
        for idx, bp in enumerate(base_positions):
            color = 'lightblue' if idx == self.controller.inspector.mission_id else 'k'
            marker, = ax_map.plot(bp.x, bp.y, 's', color=color, markersize=8)
            ax_map.text(bp.x + 0.3, bp.y + 0.3, str(idx), fontsize=12)
            base_markers.append(marker)

        # Inspector and executor points and paths
        inspector_point, = ax_map.plot([], [], 'bo', markersize=8, label="Drone", zorder=5)
        inspector_visibility = patches.Circle((0, 0), config.DRONE_VISIBILITY, color='blue', alpha=0.2, zorder=3)
        ax_map.add_patch(inspector_visibility)
        executor_point, = ax_map.plot([], [], 'go', markersize=8, label="Robot Dog", zorder=5)
        inspector_path, = ax_map.plot([], [], 'b--', linewidth=1)
        executor_path, = ax_map.plot([], [], 'g--', linewidth=1)
        detected_scatter = ax_map.scatter([], [], s=50, zorder=4)

        ax_map.legend(loc='upper right')

        # ----------------------------
        # Information panel
        # ----------------------------
        ax_info = fig.add_subplot(1, 2, 2)
        ax_info.axis("off")
        text_info = ax_info.text(0.02, 0.98, "", va="top", fontsize=12)

        # ----------------------------
        # Buttons
        # ----------------------------
        ax_start = plt.axes([0.45, 0.01, 0.1, 0.05])
        start_button = Button(ax_start, "Start Operation")
        start_button.on_clicked(lambda event: self.controller.start())
        ax_start.set_visible(True)

        ax_stop = plt.axes([0.55, 0.01, 0.1, 0.05])
        stop_button = Button(ax_stop, "Stop Dron")
        stop_button.on_clicked(lambda event: self.controller.stop_inspection())
        ax_stop.set_visible(False)

        ax_next = plt.axes([0.65, 0.01, 0.1, 0.05])
        next_button = Button(ax_next, "Next mission")
        next_button.on_clicked(lambda event: self.controller.next_mission())
        ax_next.set_visible(False)

        fig.canvas.mpl_connect("close_event", lambda event: self.controller.shutdown())

        # ----------------------------
        # Animation update
        # ----------------------------
        def update(frame):
            mission_id = self.controller.inspector.mission_id
            base_position = base_positions[mission_id]

            # Update base markers
            for idx, marker in enumerate(base_markers):
                marker.set_color('lightblue' if idx == mission_id else 'k')

            # Inspector position
            ins_rel = self.controller.inspector.robot.get_current_position()
            ins_abs = Point2D(base_position.x + ins_rel.x, base_position.y + ins_rel.y)
            self._inspector_positions.append(ins_abs)
            inspector_visibility.center = (ins_abs.x, ins_abs.y)

            # Executor position
            exe_rel = self.controller.executor.robot.get_current_position()
            exe_abs = Point2D(exe_rel.x, exe_rel.y)
            self._executor_positions.append(exe_abs)

            # Update paths
            if self._inspector_positions:
                xs, ys = zip(*[(p.x, p.y) for p in self._inspector_positions])
                inspector_point.set_data([xs[-1]], [ys[-1]])
                inspector_path.set_data(xs, ys)

            if self._executor_positions:
                ex, ey = zip(*[(p.x, p.y) for p in self._executor_positions])
                executor_point.set_data([ex[-1]], [ey[-1]])
                executor_path.set_data(ex, ey)

            # Detected points
            points = list(self.controller.inspector.actual_points.keys())
            if points:
                coords = array([[p.x, p.y] for p in points])
                colors = ['green' if self.controller.inspector.actual_points[p] else 'red' for p in points]
                detected_scatter.set_offsets(coords)
                detected_scatter.set_color(colors)

            # Buttons visibility
            start_button.ax.set_visible(self.controller.status == Status.NOT_STARTED)
            stop_button.ax.set_visible(self.controller.inspector.status == Status.RUNNING)
            next_button.ax.set_visible(self.controller.status == Status.RUNNING and 
                                       self.controller.inspector.status == Status.FINISHED and
                                       mission_id + 1 < len(base_positions))

            # Info panel
            elapsed = time() - self.controller.start_time if self.controller.start_time else 0.0
            ins_dist = self._distance_traveled(self._inspector_positions)
            exe_dist = self._distance_traveled(self._executor_positions)
            points_text = "\n".join([f"• ({p.x:.2f},{p.y:.2f})" for p in points])

            info = f"""
            Time: {elapsed:.1f}s
            Operation Status: {self.controller.status.name}

            Drone Mission: {mission_id}
            Drone Mission Status: {self.controller.inspector.status.name}
            Drone Position: x={ins_abs.x:.2f}, y={ins_abs.y:.2f}
            Drone Distance: {ins_dist:.2f}

            Robot Dog Mission: {self.controller.executor.mission_id}
            Robot Dog Mission Status: {self.controller.executor.status.name}
            Robot Dog Position: x={exe_abs.x:.2f}, y={exe_abs.y:.2f}
            Robot Dog Distance: {exe_dist:.2f}

            Points Detected: {len(points)}
            {points_text}
            """
            text_info.set_text(info)
            text_info.set_color('black')

            return inspector_point, executor_point, detected_scatter

        ani = animation.FuncAnimation(fig, update, interval=100, blit=False, cache_frame_data=False)
        plt.show()
