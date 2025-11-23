from dataclasses import dataclass
import numpy as np

@dataclass
class Position:
    x: float
    y: float

@dataclass
class FrameWithPosition:
    frame: np.ndarray
    position: Position
