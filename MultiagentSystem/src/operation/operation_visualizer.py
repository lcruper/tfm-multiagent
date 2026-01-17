"""
Operation Visualizer
---------------------

Provides a visual interface to monitor and control the operation execution.
"""

import matplotlib.pyplot as plt
from matplotlib import patches
import matplotlib.animation as animation
from matplotlib.widgets import Button
from numpy import array
from time import time
from typing import List, Dict

from configuration import operation as config
from operation.operation_status import OperationStatus
from operation.operation_controller import OperationController
from structures.structures import Point2D


class OperationVisualizer:
    """
    Visualizer for operation execution.

    Displays the explorer and inspector positions, 
    detected points, and allows controlling missions with buttons.
    """

    def __init__(self, controller: OperationController) -> None:
        """
        Creates an OperationVisualizer instance.
        Args:
            controller (OperationController): The operation controller to visualize.
        """
        self.controller: OperationController = controller
        self._explorer_positions: List[Point2D] = []
        self._inspector_positions: List[Point2D] = []

        self._points_by_mission: Dict[int, List[Point2D]] = {}

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

        base_positions = self.controller.base_positions
        ax_map.set_xlim(min(p.x for p in base_positions) - 5, max(p.x for p in base_positions) + 5)
        ax_map.set_ylim(min(p.y for p in base_positions) - 5, max(p.y for p in base_positions) + 5)

        # Base stations
        base_markers = []
        for idx, bp in enumerate(base_positions):
            color = 'lightblue' if idx == self.controller.explorer_worker.current_mission_id else 'k'
            marker, = ax_map.plot(bp.x, bp.y, 's', color=color, markersize=8)
            ax_map.text(bp.x + 0.3, bp.y + 0.3, str(idx), fontsize=12)
            base_markers.append(marker)

        # explorer and inspector points and paths
        explorer_point, = ax_map.plot([], [], 'bo', markersize=8, label="Drone", zorder=5)
        explorer_visibility = patches.Circle((0, 0), config.DRONE_VISIBILITY, color='blue', alpha=0.2, zorder=3)
        ax_map.add_patch(explorer_visibility)
        inspector_point, = ax_map.plot([], [], 'go', markersize=8, label="Robot Dog", zorder=5)
        explorer_path, = ax_map.plot([], [], 'b--', linewidth=1)
        inspector_path, = ax_map.plot([], [], 'g--', linewidth=1)
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
        stop_button.on_clicked(lambda event: self.controller.stop_routine())
        ax_stop.set_visible(False)

        ax_next = plt.axes([0.65, 0.01, 0.1, 0.05])
        next_button = Button(ax_next, "Next mission")
        next_button.on_clicked(lambda event: self.controller.next_mission())
        ax_next.set_visible(False)
        
        # ----------------------------
        # Animation update
        # ----------------------------
        def update(frame):
            mission_id = self.controller.explorer_worker.current_mission_id
            base_position = base_positions[mission_id]

            # Update base markers
            for idx, marker in enumerate(base_markers):
                marker.set_color('lightblue' if idx == mission_id else 'k')

            # explorer position
            ins_rel = self.controller.explorer_robot.get_current_position()
            ins_abs = Point2D(base_position.x + ins_rel.x, base_position.y + ins_rel.y)
            self._explorer_positions.append(ins_abs)
            explorer_visibility.center = (ins_abs.x, ins_abs.y)

            # inspector position
            exe_rel = self.controller.inspector_robot.get_current_position()
            exe_abs = Point2D(exe_rel.x, exe_rel.y)
            self._inspector_positions.append(exe_abs)

            # Update paths
            if self._explorer_positions:
                xs, ys = zip(*[(p.x, p.y) for p in self._explorer_positions])
                explorer_point.set_data([xs[-1]], [ys[-1]])
                explorer_path.set_data(xs, ys)

            if self._inspector_positions:
                ex, ey = zip(*[(p.x, p.y) for p in self._inspector_positions])
                inspector_point.set_data([ex[-1]], [ey[-1]])
                inspector_path.set_data(ex, ey)

            # Detected points
            self._points_by_mission.clear()
            all_points = []
            colors = []

            for point, (mid, reached, _, _) in self.controller.all_points.items():
                self._points_by_mission.setdefault(mid, []).append(point)
                all_points.append(point)
                colors.append("green" if reached else "red")

            if all_points:
                coords = array([[p.x, p.y] for p in all_points])
                detected_scatter.set_offsets(coords)
                detected_scatter.set_color(colors)

            # Buttons visibility
            start_button.ax.set_visible(self.controller.status == OperationStatus.NOT_STARTED)
            stop_button.ax.set_visible(self.controller.explorer_worker.status == OperationStatus.RUNNING)
            next_button.ax.set_visible(self.controller.status == OperationStatus.RUNNING and 
                                       self.controller.explorer_worker.status == OperationStatus.FINISHED and
                                       mission_id + 1 < len(base_positions))

            # Info panel
            if self.controller.status == OperationStatus.NOT_STARTED:
                elapsed = 0.0
            elif self.controller.status == OperationStatus.RUNNING:
                elapsed = time() - self.controller.start_time
            else: 
                elapsed = self.controller.finished_time - self.controller.start_time 

            ins_dist = self._distance_traveled(self._explorer_positions)
            exe_dist = self._distance_traveled(self._inspector_positions)

            left_blocks = []
            right_blocks = []
            for mid in range(len(base_positions)):
                pts = self._points_by_mission.get(mid, [])
                block = [f"Mission {mid}: {len(pts)} points"]
                for p in pts:
                    if p in self.controller.inspector_worker.points_temperatures:
                        block.append(f"• ({p.x:.2f}, {p.y:.2f}) -> {self.controller.inspector_worker.points_temperatures[p]:.2f}°C")
                    else:
                        block.append(f"• ({p.x:.2f}, {p.y:.2f})")
                if mid % 2 == 0:
                    left_blocks.append(block)
                else:
                    right_blocks.append(block)

            missions_text = ""
            max_blocks = max(len(left_blocks), len(right_blocks))
            for i in range(max_blocks):
                left_block = left_blocks[i] if i < len(left_blocks) else []
                right_block = right_blocks[i] if i < len(right_blocks) else []
                max_lines = max(len(left_block), len(right_block))
                for j in range(max_lines):
                    left_line = left_block[j] if j < len(left_block) else ""
                    right_line = right_block[j] if j < len(right_block) else ""
                    missions_text += f"{left_line:<45} {right_line}\n"
                missions_text += "\n"
                
            info = f"""OPERATION:
- Time: {elapsed:.1f}s
- Operation Status: {self.controller.status.name}

DRONE:
- Drone Mission: {mission_id}
- Drone Mission Status: {self.controller.explorer_worker.status.name}
- Drone Position: x={ins_abs.x:.2f}, y={ins_abs.y:.2f}
- Drone Distance: {ins_dist:.2f}

ROBOT DOG:
- Robot Dog Mission: {self.controller.inspector_worker.current_mission_id}
- Robot Dog Mission Status: {self.controller.inspector_worker.status.name}
- Robot Dog Position: x={exe_abs.x:.2f}, y={exe_abs.y:.2f}
- Robot Dog Distance: {exe_dist:.2f}

POINTS DETECTED:
{missions_text}
"""
            text_info.set_text(info)
            text_info.set_color('black')

            return explorer_point, inspector_point, detected_scatter

        ani = animation.FuncAnimation(fig, update, interval=100, blit=False, cache_frame_data=False)
        plt.show()
