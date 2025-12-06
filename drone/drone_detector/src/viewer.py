# viewer.py
import cv2
import threading
import logging
from queue import Empty, Queue

from numpy import ndarray
from structures import FrameWithTelemetry

class Viewer:
    """
    @brief Displays camera frames with drone telemetry overlay from FrameWithTelemetry in a queue.

    Reads FrameWithTelemetry objects from the input queue,
    draws drone telemetry overlay on the frames,
    and displays them in a live video window.
    """
    def __init__(self, input_queue: Queue) -> None:
        """
        @brief Constructor.

        @param input_queue Queue with FrameWithTelemetry objects
        """
        self.input_queue: Queue = input_queue

        # Threading
        self._running: bool = False             # Flag to control the background viewer thread
        self._thread: threading.Thread = None   # Viewer thread

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

        self._logger.info("Starting viewer...")
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
        
        self._logger.info("Stopping viewer...")
        self._running = False
        if self._thread:
            self._thread.join()
            if self._thread.is_alive():
                self._logger.warning("Viewer thread didn't stop in time")
            self._thread = None
        cv2.destroyAllWindows()
        self._logger.info("Viewer stopped.")

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
        bar_height = 75
        cv2.rectangle(overlay, (0, 0), (data.shape[1], bar_height), (0, 0, 0), -1)
        alpha = 0.45
        frame = cv2.addWeighted(overlay, alpha, data, 1 - alpha, 0)

        # Text lines
        line1 = f"x:{telemetry.pose.position.x:.2f}  y:{telemetry.pose.position.y:.2f}  z:{telemetry.pose.position.z:.2f}"
        line2 = f"pitch:{telemetry.pose.orientation.pitch:.2f}  roll:{telemetry.pose.orientation.roll:.2f}  yaw:{telemetry.pose.orientation.yaw:.2f}"
        line3 = f"voltage: {telemetry.battery.voltage:.2f}"
        
        def draw_text(text, y):
            font = cv2.FONT_HERSHEY_SIMPLEX
            scale = 0.45
            # Light shadow
            cv2.putText(frame, text, (11, y+2), font, scale, (0,0,0), 1, cv2.LINE_AA)
            # Main white text
            cv2.putText(frame, text, (10, y),   font, scale, (255,255,255), 1, cv2.LINE_AA)

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
                fwt = self.input_queue.get(timeout=0.05)
            except Empty:
                # Queue is empty
                self._logger.warning("Queue empty, waiting for frames...")
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
