import threading
from typing import Dict, List
from queue import Queue
import logging
import winsound

import config
from mission.mission_state import RobotStatus
from interfaces.interfaces import IRobot
from structures.structures import Point2D

class InspectorWorker(threading.Thread):
    def __init__(self, 
                 robot: IRobot, 
                 base_positions: List[Point2D], 
                 points_queue: Queue[Dict[Point2D, bool]]) -> None:
        
        super().__init__(daemon=True)
        self.robot = robot
        self.base_positions = base_positions
        self.points_queue = points_queue

        self.actual_points: Dict[Point2D, bool] = {}
        self.mission_id = 0
        self.status = RobotStatus.STOPPED

        self.stop_event = threading.Event()
        self.next_event = threading.Event()
        self.lock = threading.Lock()

        self.robot.set_callback_onPoint(self._on_point)
        self.robot.set_callback_onFinish(self._on_finish)

        self.logger = logging.getLogger("InspectorWorker")


    def _on_point(self, Point: Point2D) -> None:
        bx, by = self.base_positions[self.mission_id]
        abs_point = Point2D(bx + Point.x, by + Point.y)
        self.logger.info("%d.Inspector. Detected point at %s. Beeping...",  self.mission_id, abs_point)
        winsound.Beep(1000, 200) 
        with self.lock:
            if not self._is_too_close(abs_point):
                self.actual_points[abs_point] = False
            else:
                self.logger.info("%d.Inspector skipping point (too close): %s", self.mission_id, abs_point)

    def _on_finish(self) -> None:
        with self.lock:
            self.logger.info("%d.Inspector finished with %d points", self.mission_id, len(self.actual_points))
            self.status = RobotStatus.STOPPED
            self.points_queue.put(dict(self.actual_points))
            self.actual_points.clear()
            self.stop_event.set()

    def _is_too_close(self, new_point: Point2D) -> bool:
        for pt in self.actual_points.keys():
            dist = ((pt.x - new_point.x)**2 + (pt.y - new_point.y)**2)**0.5
            if dist < config.INSPECTION_POINT_MIN_DIST:
                return True
        return False


    def run(self):
        while self.mission_id < len(self.base_positions):
            self.next_event.wait()
            self.next_event.clear()
            self.logger.info("%d.Inspector starting", self.mission_id)
            self.status = RobotStatus.RUNNING
            self.robot.start_inspection()
            self.stop_event.wait()
            self.robot.stop_inspection()


    def start_next(self):
        self.mission_id += 1
        self.next_event.set()