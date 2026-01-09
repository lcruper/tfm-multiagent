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
    mission inspectors.
    """

    def __init__(self) -> None:
        """
        Initializes all operation-level synchronization events.
        """
        self._stop_routine: threading.Event = threading.Event()
        """Event to signal stopping the inspection process."""
        self._next_mission: threading.Event = threading.Event()
        """Event to signal starting the next mission."""
        self._inspector_done: threading.Event = threading.Event()
        """Event to signal that the inspector has finished its mission."""

    def trigger_stop_routine(self) -> None:
        """
        Triggers the stop inspection event.
        """
        self._stop_routine.set()

    def trigger_next_mission(self) -> None:
        """
        Triggers the next mission event.
        """
        self._next_mission.set()

    def trigger_inspector_done(self) -> None:
        """
        Triggers the inspector done event.
        """
        self._inspector_done.set()

    def clear_stop_routine(self) -> None:
        """
        Clears the stop inspection event.
        """
        self._stop_routine.clear()

    def clear_next_mission(self) -> None:
        """
        Clears the next mission event.
        """
        self._next_mission.clear()  

    def clear_inspector_done(self) -> None:
        """
        Clears the inspector done event.
        """
        self._inspector_done.clear() 

    def wait_for_stop_routine(self) -> None:
        """
        Blocks until the stop inspection event is set.
        """
        self._stop_routine.wait()    

    def wait_for_next_mission(self) -> None:
        """
        Blocks until the next mission event is set.
        """
        self._next_mission.wait()

    def wait_for_inspector_done(self) -> None:
        """
        Blocks until the inspector done event is set.
        """
        self._inspector_done.wait()


    