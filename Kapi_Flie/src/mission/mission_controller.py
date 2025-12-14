from queue import Queue
import logging
from typing import List

from mission.inspector_worker import InspectorWorker
from mission.executor_worker import ExecutorWorker
from interfaces.interfaces import IPathPlanner
from structures.structures import Point2D


class MissionController:
    def __init__(self, 
                 inspector: InspectorWorker, 
                 executor: ExecutorWorker, 
                 planner: IPathPlanner, 
                 base_positions: List[Point2D]) -> None:
        
        self.logger: logging.Logger = logging.getLogger("Mission")
        self.queue: Queue[List[Point2D]] = Queue()
        self.inspector: InspectorWorker = InspectorWorker(inspector, base_positions, self.queue)
        self.executor: ExecutorWorker = ExecutorWorker(executor, planner, self.queue)

    def start(self):
        self.inspector.start()
        self.executor.start()
        self.inspector.next_event.set()

    def next_mission(self):
        self.inspector.start_next()

    def stop_inspection(self):
        self.inspector.

    def wait_until_finished(self):
        self.inspector.join()
        self.executor.join()