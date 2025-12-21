"""
Operation Status
----------------

Defines enums representing the execution status of robots and operations.
"""

from enum import Enum, auto

class Status(Enum):
    """
    Status of an entity.
    """
    NOT_STARTED = auto()
    """Not started yet."""
    RUNNING = auto()
    """Currently running."""
    FINISHED = auto()
    """Finished successfully."""
    ALL_FINISHED = auto()
    """All finished."""
    ABORTED = auto()
    """Aborted before completion."""