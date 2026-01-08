from typing import Optional
from configuration import viewer as config
import cv2
import threading
import logging
from queue import Empty, Queue
from numpy import ndarray
from time import sleep

from interfaces.interfaces import AFrameConsumer
from structures.structures import FrameWithTelemetry

class Viewer(AFrameConsumer):
    """
    Real-time drone video viewer with telemetry overlay.

    This class implements a frame consumer designed to visualize
    live camera frames augmented with telemetry information, 
    including 3D position, orientation, and battery status.

    The Viewer maintains an internal queue for incoming frames and processes them
    in a dedicated background thread. The thread draws telemetry data on the frame
    and displays it in a live OpenCV window. 
    """

    def __init__(self) -> None:
        """
        Creates a Viewer instance.
        """
        self._queue = Queue(maxsize=config.VIEWER_MAX_QUEUE_SIZE)

        self._running: bool = False
        self._thread: Optional[threading.Thread] = None

        self._logger: logging.Logger = logging.getLogger("Viewer")

    # ----------------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        Starts the viewer's background thread.

        The thread continuously retrieves frames from the queue, applies telemetry
        overlay, and renders them in a live OpenCV window.
        """
        if self._running:
            self._logger.warning("Already running.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._logger.info("Started.")

    def stop(self) -> None:
        """
        Stops the viewer thread and closes the OpenCV window.

        Waits for the thread to finish processing the actual frame and safely destroys all OpenCV windows.
        """
        if not self._running:
            self._logger.warning("Already stopped.")
            return

        self._running = False
        if self._thread:
            self._thread.join()
            if self._thread.is_alive():
                self._logger.warning("Did not stop in time")
            self._thread = None
        cv2.destroyAllWindows()
        self._logger.info("Stopped.")

    # ----------------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------------
    def _process_frame(self, fwt: FrameWithTelemetry) -> ndarray:
        """
        Draws telemetry overlay on the frame.

        Args:
            fwt (FrameWithTelemetry): Frame with telemetry associated.

        Returns:
            ndarray: Frame with its telemetry information rendered on top.
        """
        data = fwt.frame.data
        telemetry = fwt.telemetry
        self._logger.debug("Processing frame of shape %s.", data.shape)

        overlay = data.copy()

        cv2.rectangle(overlay, (0, 0), (data.shape[1], config.VIEWER_BAR_HEIGHT), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, config.VIEWER_OVERLAY_ALPHA, data, 1 - config.VIEWER_OVERLAY_ALPHA, 0)

        line1 = f"x:{telemetry.pose.position.x:.1f} y:{telemetry.pose.position.y:.1f}, z:{telemetry.pose.position.z:.1f}"
        line2 = f"pitch:{telemetry.pose.orientation.pitch:.2f}  roll:{telemetry.pose.orientation.roll:.2f}  yaw:{telemetry.pose.orientation.yaw:.2f}"
        line3 = f"voltage: {telemetry.battery.voltage:.2f}"

        def draw_text(text, y):
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, text, (11, y + 2), font, config.VIEWER_FONT_SIZE, (0, 0, 0), 1, cv2.LINE_AA)
            cv2.putText(frame, text, (10, y), font, config.VIEWER_FONT_SIZE, (255, 255, 255), 1, cv2.LINE_AA)

        draw_text(line1, 22)
        draw_text(line2, 44)
        draw_text(line3, 66)

        return frame

    def _loop(self):
        """
        Background thread loop.

        Continuously retrieves frames from the queue, applies telemetry overlay, 
        and renders them. Pressing ESC stops the viewer.
        """
        while self._running:
            try:
                fwt = self._queue.get(timeout=0.05)
            except Empty:
                sleep(config.VIEWER_SLEEP_TIME)
                continue
            try:
                frame_display = self._process_frame(fwt)
                cv2.imshow("Drone Camera Live", frame_display)
                if cv2.waitKey(1) & 0xFF == 27:
                    self._logger.info("ESC pressed. Closing viewer...")
                    self.stop()
                    break
            except Exception as e:
                self._logger.error("Error displaying frame: %s", e)
