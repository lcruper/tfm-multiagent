# viewer.py
"""
@file viewer.py
@brief Displays camera frames with telemetry overlay from a queue of FrameWithTelemetry.
"""
from typing import Optional
import config
import cv2
import threading
import logging
from queue import Empty, Full, Queue
from numpy import ndarray
from time import sleep

from interfaces.interfaces import IFrameConsumer
from structures.structures import FrameWithTelemetry

class Viewer(IFrameConsumer):
    """
    @brief Displays camera frames with telemetry overlay from FrameWithTelemetry in a queue.

    Reads FrameWithTelemetry objects from the input queue,
    draws telemetry overlay on the frames,
    and displays them in a live video window.
    """
    def __init__(self) -> None:
        """
        @brief Constructor.

        @param queue Queue with FrameWithTelemetry objects
        """
        self._queue: Queue = Queue(maxsize=config.VIEWER_MAX_QUEUE_SIZE)    # Queue for FrameWithTelemetry objects

        # Threading
        self._running: bool = False                         # Flag to control the background viewer thread
        self._thread: Optional[threading.Thread] = None     # Viewer thread

        # Logger
        self._logger: logging.Logger = logging.getLogger("Viewer")

    # ----------------------------------------------------------------------
    # Control
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        @brief Starts the viewer thread.
        """
        if self._running:
            self._logger.warning("Viewer already running.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._logger.info("Viewer started.")

    def stop(self) -> None:
        """
        @brief Stops the viewer and closes the window.
        """
        if not self._running:
            self._logger.warning("Viewer already stopped.")
            return
        
        self._running = False
        if self._thread:
            self._thread.join()
            if self._thread.is_alive():
                self._logger.warning("Viewer thread didn't stop in time")
            self._thread = None
        cv2.destroyAllWindows()
        self._logger.info("Viewer stopped.")

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    def enqueue(self, fwt: FrameWithTelemetry) -> None:
        """
        @brief Enqueues a FrameWithTelemetry for display.

        @param fwt FrameWithTelemetry object
        """
        while True:
            try:
                self._queue.put_nowait(fwt)
                break
            except Full:
                try:
                    self._queue.get_nowait()
                except Empty:
                    break

    # ----------------------------------------------------------------------
    # Internal methods
    # ----------------------------------------------------------------------
    def _draw_overlay(self, fwt: FrameWithTelemetry) -> ndarray:
        """
        @brief Draws telemetry overlay on the frame.

        @param fwt FrameWithTelemetry object
        @return Frame with overlay
        """
        data = fwt.frame.data
        telemetry = fwt.telemetry

        overlay = data.copy()

        # Semi-transparent black bar at top
        cv2.rectangle(overlay, (0, 0), (data.shape[1], config.VIEWER_BAR_HEIGHT), (0, 0, 0), -1)
        frame = cv2.addWeighted(overlay, config.VIEWER_OVERLAY_ALPHA, data, 1 - config.VIEWER_OVERLAY_ALPHA, 0)

        # Text lines
        #line1 = f"x:{telemetry.pose.position.x:.1f}  y:{telemetry.pose.position.y:.1f}  z:{telemetry.pose.position.z:.1f}"
        line1 = f"z:{telemetry.pose.position.z:.1f}"
        line2 = f"pitch:{telemetry.pose.orientation.pitch:.2f}  roll:{telemetry.pose.orientation.roll:.2f}  yaw:{telemetry.pose.orientation.yaw:.2f}"
        line3 = f"voltage: {telemetry.battery.voltage:.2f}"
        
        def draw_text(text, y):
            font = cv2.FONT_HERSHEY_SIMPLEX
            # Light shadow
            cv2.putText(frame, text, (11, y+2), font, config.VIEWER_FONT_SIZE, (0,0,0), 1, cv2.LINE_AA)
            # Main white text
            cv2.putText(frame, text, (10, y), font, config.VIEWER_FONT_SIZE, (255,255,255), 1, cv2.LINE_AA)

        draw_text(line1, 22)
        draw_text(line2, 44)
        draw_text(line3, 66)
        return frame

    def _loop(self):
        """
        @brief Reads frames and displays them.
        """
        while self._running:
            try:
                # Get FrameWithTelemetry from the queue
                fwt = self._queue.get(timeout=0.05)
            except Empty:
                # Queue is empty
                self._logger.debug("Queue empty, waiting for frames...")
                sleep(config.VIEWER_SLEEP_TIME)
                continue

            try:
                frame_display = self._draw_overlay(fwt)
                cv2.imshow("Drone Camera Live", frame_display)
                # ESC key to exit
                if cv2.waitKey(1) & 0xFF == 27: 
                    self._logger.info("ESC pressed. Closing viewer...")
                    self.stop()
                    break
            except Exception as e:
                self._logger.error("Error displaying frame: %s", e)