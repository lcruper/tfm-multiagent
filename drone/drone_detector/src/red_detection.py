# red_detection.py
import threading
import logging
import cv2
import numpy as np

from queue import Queue, Empty
from ultralytics import YOLO

class RedDetection:
    """
    @brief Detects red objects in framesWithPosition coming from a queue.

    Reads FrameWithPosition objects from the input queue,
    runs YOLO object detection, then checks for red in detected boxes.
    It also triggers a callback with the position if red is detected.
    """
    IMG_SIZE = 256          # Size to which frames are resized for YOLO
    CONF_THRESH = 0.35      # Confidence threshold for YOLO detections
    IOU_THRESH = 0.45       # Intersection over Union threshold for YOLO
    RED_RATIO_THRESH = 0.3  # Minimum ratio of red pixels in a detected box to consider it red
    MIN_BOX_AREA = 100      # Minimum area of detected box to consider

    def __init__(self, input_queue: Queue, yolo_model_path: str, callback=None) -> None:
        """
        @brief Constructor.

        @param input_queue Queue with FrameWithPosition objects
        @param callback Function(Position) called when red object is detected
        """
        self.queue = input_queue
        self.callback = callback

        self.model = YOLO(yolo_model_path)     # YOLO model for object detection

        # Threading
        self._running = False   # Flag to control the background frame processing thread
        self._thread = None     # Frame processing thread

        # Logger
        self._logger = logging.getLogger("RedDetection")

    # ----------------------------------------------------------------------
    # Control
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        @brief Starts the background frame processing thread.
        """
        if self._running:
            self._logger.warning("Frame processing already running.")
            return

        self._logger.info(f"Starting frame processing...")
        self._running = True
        self._thread = threading.Thread(target=self._process, daemon=True)
        self._thread.start()
        self._logger.info("Frame processing started.")

    def stop(self) -> None:
        """
        @brief Stops the frame processing.
        """
        if not self._running:
            self._logger.warning("Frame processing already stopped.")
            return

        self._logger.info("Stopping frame processing...")
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        self._logger.info("Frame processing stopped.")

    # ----------------------------------------------------------------------
    # Internal methods
    # ----------------------------------------------------------------------
    def _process(self) -> None:
        """
        @brief Reads framesWithPosition from the queue and detects red objects.
        """
        while self._running:
            try:
                # Get a FrameWithPosition from the queue
                fwp = self.queue.get(timeout=0.1)
            except Empty:
                # Queue is empty
                self._logger.warning("Queue empty, waiting for frames...")
                continue

            frame = fwp.frame.data
            position = fwp.position

            self._logger.debug(f"Processing frame of shape {frame.shape} at position: {position}")
            try:
                # Run YOLO object detection on the frame
                results = self.model.predict(frame,
                                             device="cpu",
                                             imgsz=self.IMG_SIZE,
                                             conf=self.CONF_THRESH,
                                             iou=self.IOU_THRESH,
                                             half=False,
                                             verbose=False)
            except Exception as e:
                self._logger.error(f"YOLO prediction error: {e}")
                continue

            # Get detected boxes
            dets = results[0].boxes if len(results) else []
            red_detected = False

            for box in dets:
                # Convert box to integer coordinates
                xyxy = box.xyxy.cpu().numpy().astype(int)[0] if hasattr(box.xyxy, "cpu") else np.array(box.xyxy).astype(int)[0]
                x1, y1, x2, y2 = xyxy
                w, h = x2 - x1, y2 - y1
                if w*h < self.MIN_BOX_AREA:
                    continue

                roi = frame[y1:y2, x1:x2]
                if roi.size == 0:
                    continue

                # Convert ROI to HSV for red detection
                hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                mask1 = cv2.inRange(hsv, np.array([0, 80, 50]), np.array([10, 255, 255]))
                mask2 = cv2.inRange(hsv, np.array([160, 80, 50]), np.array([180, 255, 255]))
                mask = cv2.bitwise_or(mask1, mask2)
                red_ratio = cv2.countNonZero(mask) / (roi.shape[0]*roi.shape[1]+1e-6)

                self._logger.debug(f"Red ratio in box: {red_ratio:.3f}")
                
                if red_ratio >= self.RED_RATIO_THRESH:
                    red_detected = True
                    self._logger.info(f"Red object detected at position {position}")

                    # Call the callback if provided
                    if self.callback:
                        try:
                            self.callback(position)
                        except Exception as e:
                            self._logger.error(f"Callback error: {e}")

                    # Stop checking other boxes once red is detected
                    break

            if not red_detected:
                self._logger.debug("No red object detected in this frame.")