# viewer.py
import cv2
import threading
import logging
from queue import Empty

from numpy import ndarray

class Viewer:
    """
    @brief Displays camera frames with drone telemetry overlay from FrameWithPosition in a queue.

    Reads FrameWithPosition objects from the input queue,
    draws drone telemetry (position + orientation) overlay on the frames,
    and displays them in a live video window.
    """
    def __init__(self, input_queue) -> None:
        """
        @brief Constructor.

        @param input_queue Queue with FrameWithPosition objects
        """
        self.input_queue = input_queue

        # Threading
        self._running = False  # Flag to control the background viewer thread
        self._thread = None    # Viewer thread

        # Logger
        self._logger = logging.getLogger("Viewer")

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
        cv2.destroyAllWindows()
        self._logger.info("Viewer stopped.")

    # ----------------------------------------------------------------------
    # Internal methods
    # ----------------------------------------------------------------------
    def _draw_overlay(self, frame, position) -> ndarray:
        """
        @brief Draws telemetry overlay on the frame.

        @param frame Frame image
        @param position Position object
        @return Frame with overlay
        """
        overlay = frame.copy()

        # Semi-transparent black bar at top
        bar_height = 60
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], bar_height), (0, 0, 0), -1)
        alpha = 0.45
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        # Text lines
        line1 = f"x:{position.x:.2f}  y:{position.y:.2f}  z:{position.z:.2f}"

        def draw_text(text, y):
            # Black shadow
            cv2.putText(frame, text, (12, y+2), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 3, cv2.LINE_AA)
            # White text
            cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2, cv2.LINE_AA)

        draw_text(line1, 25)
        return frame

    def _loop(self):
        """
        @brief Reads frames and displays them.
        """
        while self._running:
            try:
                # Get FrameWithPosition from the queue
                fwp = self.input_queue.get(timeout=0.05)
            except Empty:
                continue

            try:
                frame_display = self._draw_overlay(fwp.frame.data.copy(), fwp.position)
                cv2.imshow("Drone Camera Live", frame_display)
                # ESC key to exit
                if cv2.waitKey(1) & 0xFF == 27: 
                    self._logger.info("ESC pressed. Closing viewer...")
                    self.stop()
                    break
            except Exception as e:
                self._logger.error(f"Error displaying frame: {e}")
