from enum import Enum, auto

class RobotStatus(Enum):
    
    """
    @brief Status of a robot 
    """
    STOPPED = auto()  
    RUNNING = auto()

class MissionStatus(Enum):
    """
    @brief Status of a mission
    """
    NOT_STARTED = auto()
    STARTED = auto()
    FINISHED = auto()
