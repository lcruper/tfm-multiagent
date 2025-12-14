import threading

class MissionEvents:
    def __init__(self) -> None:
        self.stop_inspector = threading.Event()
        self.next_mission = threading.Event()
        self.executor_done = threading.Event()