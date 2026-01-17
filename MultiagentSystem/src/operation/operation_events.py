import threading

class OperationEvents:
    """
    Container class for all synchronization events used during the execution
    of an operation.

    This class encapsulates the threading events that coordinate the interaction
    between the explorer agent, the inspector agent, and the operation controller.
    It provides a thread-safe signaling mechanism to control the execution flow
    of exploration and inspection phases without introducing direct dependencies
    between threads.
    """

    def __init__(self) -> None:
        """
        Creates all operation-level synchronization events.
        """
        self._stop_exploration: threading.Event = threading.Event()
        """Event used to signal the explorer agent to stop the current exploration phase."""

        self._start_next_exploration: threading.Event = threading.Event()
        """Event used to signal the explorer agent to start the next exploration phase."""

        self._inspector_done: threading.Event = threading.Event()
        """Event used to signal that the inspector agent has completed the current inspection phase."""

    def trigger_stop_exploration(self) -> None:
        """
        Activates the stop exploration event.
        """
        self._stop_exploration.set()

    def trigger_start_next_exploration(self) -> None:
        """
        Activates the start next exploration event.
        """
        self._start_next_exploration.set()

    def trigger_inspector_done(self) -> None:
        """
        Activates the inspector done event.
        """
        self._inspector_done.set()

    def clear_stop_exploration(self) -> None:
        """
        Clears the stop exploration event.
        """
        self._stop_exploration.clear()

    def clear_start_next_exploration(self) -> None:
        """
        Clears the start next exploration event.
        """
        self._start_next_exploration.clear()  

    def clear_inspector_done(self) -> None:
        """
        Clears the inspector done event.
        """
        self._inspector_done.clear() 

    def wait_for_stop_exploration(self) -> None:
        """
        Blocks the calling thread until the stop exploration event is set.
        """
        self._stop_exploration.wait()    

    def wait_for_start_next_exploration(self) -> None:
        """
        Blocks the calling thread until the start next exploration event is set.
        """
        self._start_next_exploration.wait()

    def wait_for_inspector_done(self) -> None:
        """
        Blocks the calling thread until the inspector done event is set.
        """
        self._inspector_done.wait()
    