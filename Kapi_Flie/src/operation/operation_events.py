"""
Operation Events
----------------

Thread-safe synchronization primitives used to coordinate the execution
of missions.
"""

import threading

class OperationEvents:
    """
    Container for threading events used during an operation execution.

    These events allow safe synchronization between the operation controller and 
    mission executors.
    """

    def __init__(self) -> None:
        """
        Initializes all operation-level synchronization events.
        """
        self.stop_inspection: threading.Event = threading.Event()
        self.next_mission: threading.Event = threading.Event()
        self.executor_done: threading.Event = threading.Event()