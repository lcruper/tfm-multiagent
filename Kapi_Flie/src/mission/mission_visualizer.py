import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.widgets import Button
from numpy import array
from time import time

from mission.mission_controller import MissionController
from structures.structures import Point2D
from typing import List

class MissionVisualizer:
    def __init__(self, controller: MissionController) -> None:
        self.controller: MissionController = controller
        self.inspector_positions: List[Point2D] = []
        self.executor_positions: List[Point2D] = []
        self.start_time: float = None

    def _distance_traveled(self, path: List[Point2D]) -> float:
        if len(path) < 2:
            return 0.0
        d = 0.0
        for i in range(1, len(path)):
            dx = path[i].x - path[i-1].x
            dy = path[i].y - path[i-1].y
            d += (dx**2 + dy**2)**0.5
        return d

    def start(self) -> None:
        # Create the figure  ---------------------------------------
        fig = plt.figure(figsize=(12, 6))

        # Operation map subplot --------------------------------------
        ax_map = fig.add_subplot(1, 2, 1)
        ax_map.set_aspect('equal')
        ax_map.set_xlabel("X")
        ax_map.set_ylabel("Y")
        ax_map.set_title("Operation Map")

        base_positions = self.controller.inspector.base_positions
        ax_map.set_xlim(min(x for x, _ in base_positions) - 5,
                        max(x for x, _ in base_positions) + 5)
        ax_map.set_ylim(min(y for _, y in base_positions) - 5,
                        max(y for _, y in base_positions) + 5)

        # Base stations
        base_markers = []
        for idx, (bx, by) in enumerate(base_positions):
            color = 'lightblue' if idx == self.controller.inspector.mission_id else 'k'
            marker, = ax_map.plot(bx, by, 's', color=color, markersize=8)
            ax_map.text(bx + 0.3, by + 0.3, str(idx), fontsize=12)
            base_markers.append(marker)

        # Points and paths 
        inspector_point, = ax_map.plot([], [], 'bo', markersize=8, label="Dron", zorder=5)
        executor_point, = ax_map.plot([], [], 'go', markersize=8, label="Robot dog", zorder=5)
        inspector_path, = ax_map.plot([], [], 'b--', linewidth=1)
        executor_path, = ax_map.plot([], [], 'g--', linewidth=1)
        detected_scatter = ax_map.scatter([], [], s=50, zorder=4)

        # Legend
        ax_map.plot([], [], 'bo', label="Dron")
        ax_map.plot([], [], 'go', label="Robot dog")
        ax_map.legend(loc='upper right')

        # Information subplot --------------------------------------
        ax_info = fig.add_subplot(1, 2, 2)
        ax_info.axis("off")
        text_info = ax_info.text(0.02, 0.98, "", va="top", fontsize=12)

        # Buttons -----------------------------------------------------
        ax_start = plt.axes([0.45, 0.01, 0.1, 0.05])
        start_button = Button(ax_start, "Start Operation")
        start_button.on_clicked(lambda event: self.controller.start())
        start_button.ax.set_visible(True)

        ax_stop = plt.axes([0.45, 0.01, 0.1, 0.05])
        stop_button = Button(ax_stop, "Stop Dron")
        stop_button.on_clicked(lambda event: self.controller.inspector.)
        stop_button.ax.set_visible(False)

        ax_next = plt.axes([0.45, 0.01, 0.1, 0.05])
        next_button = Button(ax_next, "Next mission")
        next_button.on_clicked(lambda event: self.controller.next_mission())
        next_button.ax.set_visible(False)

        self.start_time = time()

        # Update function for animation ------------------------------
        def update(frame):
            mission_id = self.controller.inspector.mission_id
            base_position = base_positions[mission_id]
            base_position_x = base_position.x   
            base_position_y = base_position.y

            # Base stations markers
            for idx, marker in enumerate(base_markers):
                marker.set_color('lightblue' if idx == mission_id else 'k')

            # Inspector position
            ins_rel = self.controller.inspector.robot.get_current_position()
            ins_abs = Point2D(base_position_x + ins_rel.x, base_position_y + ins_rel.y)
            self.inspector_positions.append(ins_abs)

            # Executor position
            exe_rel = self.controller.executor.robot.get_current_position()
            exe_abs = Point2D(exe_rel.x, exe_rel.y)
            self.executor_positions.append(exe_abs)

            # Update path
            if self.inspector_positions:
                xs, ys = zip(*self.inspector_positions)
                inspector_point.set_data([xs[-1]], [ys[-1]])
                inspector_path.set_data(xs, ys)
            if self.executor_positions:
                ex, ey = zip(*self.executor_positions)
                executor_point.set_data([ex[-1]], [ey[-1]])
                executor_path.set_data(ex, ey)

            # Detected points
            points = list(self.controller.inspector.actual_points.keys())
            if points:
                coords = array([[p.x, p.y] for p in points])
                colors = ['green' if self.controller.inspector.actual_points[p] else 'red' for p in points]
                detected_scatter.set_offsets(coords)
                detected_scatter.set_color(colors)

            # Buttons
            start_button.ax.set_visible(self.controller.inspector.status.name == "Stopped")
            stop_button.ax.set_visible(self.controller.inspector.status.name == "Running")
            next_button.ax.set_visible(
                self.controller.inspector.status.name == "Stopped" and
                mission_id + 1 < len(base_positions)
            )

            # Information
            elapsed = time() - self.start_time
            ins_dist = self._distance_traveled(self.inspector_positions)
            exe_dist = self._distance_traveled(self.executor_positions)
            points_text = "\n".join([f"• ({p.x:.2f},{p.y:.2f})" for p in points])

            info = f"""
            Time: {elapsed:.1f}s

            Inspector Mission: {mission_id}
            Inspector Status: {self.controller.inspector.status.name}
            Inspector Position: x={ins_abs[0]:.2f}, y={ins_abs[1]:.2f}
            Inspector Distance: {ins_dist:.2f}

            Executor Mission: {self.controller.executor.mission_id}
            Executor Status: {self.controller.executor.status.name}
            Executor Position: x={exe_abs[0]:.2f}, y={exe_abs[1]:.2f}
            Executor Distance: {exe_dist:.2f}

            Points Detected: {len(points)}
            {points_text}
            """
            text_info.set_text(info)
            text_info.set_color('black')

            return inspector_point, executor_point, detected_scatter

        ani = animation.FuncAnimation(fig, update, interval=100, cache_frame_data=False)
        plt.show()
