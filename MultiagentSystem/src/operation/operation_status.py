from enum import Enum, auto

class OperationStatus(Enum):
    """
    Enumeration representing the execution status of the operation or the mission's phases.
    """

    NOT_STARTED = auto()
    """The operation/phase has not started yet."""

    RUNNING = auto()
    """The operation/phase is currently executing."""

    FINISHED = auto()
    """The operation/phase has finished."""