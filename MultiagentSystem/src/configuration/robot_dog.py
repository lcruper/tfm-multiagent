from typing import Final

ROBOT_DOG_SPEED: Final[float] = 0.5
"""Default walking speed (in meters per second) of the robot dog."""

ROBOT_DOG_REACHED_TOLERANCE: Final[float] = 0.05
"""Distance threshold (in meters) to consider a target point reached."""

ROBOT_SLEEP_TIME: Final[float] = 0.1
"""Sleep duration (in seconds) between robot dog movement steps."""

ROBOT_DOG_MEAN_TEMPERATURE: Final[float] = 25.0
"""Mean ambient temperature measured by the robot dog (in Celsius)."""

ROBOT_DOG_TEMPERATURE_STDDEV: Final[float] = 5.0
"""Standard deviation of ambient temperature measured by the robot dog (in Celsius)."""
