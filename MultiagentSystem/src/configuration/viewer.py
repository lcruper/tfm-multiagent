from typing import Final

VIEWER_MAX_QUEUE_SIZE: Final[int] = 100
"""Maximum number of frames stored in the viewer queue."""

VIEWER_OVERLAY_ALPHA: Final[float] = 0.45
"""Alpha transparency used for overlay rendering."""

VIEWER_BAR_HEIGHT: Final[int] = 75
"""Height (in pixels) of the telemetry overlay bar."""

VIEWER_FONT_SIZE: Final[float] = 0.45
"""Font scale used for overlay text rendering."""

VIEWER_SLEEP_TIME: Final[float] = 0.005
"""Sleep duration (in seconds) in the viewer loop."""
