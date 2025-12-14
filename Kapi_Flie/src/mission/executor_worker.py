import threading
import logging

from typing import Dict
from queue import Queue
import winsound
from mission.mission_state import RobotStatus
from structures.structures import Point2D
from interfaces.interfaces import IPathPlanner, IRobot

class ExecutorWorker(threading.Thread):
    def __init__(self, 
                 robot: IRobot, 
                 planner: IPathPlanner, 
                 points_queue: Queue[Dict[Point2D, bool]]) -> None:
        super().__init__(daemon=True)

        self.robot = robot
        self.planner = planner
        self.points_queue = points_queue

        self.done_event = threading.Event()
        self.mission_id = 0
        self.status = RobotStatus.STOPPED

        self.robot.set_callback_onPoint(self._on_point)
        self.robot.set_callback_onFinish(self._on_finish)

        self.logger = logging.getLogger("ExecutorWorker")

    def _on_point(self, point: Point2D) -> None:
        self.logger.info("%d.Executor reached point: %s. Beeping...", self.mission_id, point)
        winsound.Beep(1000, 200)

    def _on_finish(self) -> None:
        self.logger.info("%d.Executor finished", self.mission_id)
        self.status = RobotStatus.STOPPED
        self.done_event.set()


    def run(self):
        while True:
            points = self.points_queue.get()
            if points is None:
                break
            if not points:
                self.logger.info("%d.Executor skipping empty mission", self.mission_id)
                self.mission_id += 1
                self.points_queue.task_done()
                continue

            self.logger.info("%d.Executor starting mission with %d points", self.mission_id, len(points))
            self.status = RobotStatus.RUNNING
            path = self.planner.plan_path(self.robot.get_current_position(), list(points.keys()))
            self.robot.start_inspection(path)
            self.done_event.wait()
            self.robot.stop_inspection()
            self.mission_id += 1
            self.points_queue.task_done()