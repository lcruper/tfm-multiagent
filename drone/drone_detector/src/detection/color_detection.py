# color_detection.py
from typing import Optional
import config
import threading
import logging
import cv2
import numpy as np
from queue import Queue, Empty
from ultralytics import YOLO

from structures.structures import FrameWithTelemetry

class ColorDetection:
    """
    @brief Detects configurable colors in framesWithPosition coming from a queue.

    Reads FrameWithPosition objects from the input queue,
    runs YOLO object detection, then checks for colors in detected boxes.
    It also triggers a callback with the position if colors are detected.
    """

    def __init__(self, queue: Queue, 
                 callback: callable,
                 yolo_model_path: str,
                 color: str) -> None:
        """
        @brief Constructor.

        @param queue Queue with FrameWithPosition objects
        @param callback Function(Position) called when color object is detected
        @param yolo_model_path Path to the YOLO model file
        @param color Color name to detect
        """
        self.queue: Queue = queue
        self.callback: callable = callback
        self.color: str = color
        self.model: YOLO = YOLO(yolo_model_path)     # YOLO model for object detection

        self._colorLowerUpper = config.COLOR_DETECTION_COLORS.get(color, None)      # Color HSV ranges
        if self._colorLowerUpper is None:
            raise ValueError(f"Color '{color}' not defined in configuration.")
        
        # Threading
        self._running: bool = False                         # Flag to control the background frame processing thread
        self._thread: Optional[threading.Thread] = None     # Frame processing thread

        # Logger
        self._logger: logging.Logger = logging.getLogger("ColorDetection")

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
            if self._thread.is_alive():
                self._logger.warning("Frame processing thread didn't stop in time")
            self._thread = None
        self._logger.info("Frame processing stopped.")

    # ----------------------------------------------------------------------
    # Internal methods
    # ----------------------------------------------------------------------
    def _detect_color(self, fwt: FrameWithTelemetry) -> None:
        """
        @brief Detects colors in objects in the given FrameWithTelemetry.
        
        @param fwt FrameWithTelemetry object
        """
        data = fwt.frame.data
        position = fwt.telemetry.pose.position

        self._logger.debug("Processing frame of shape %s at position %s", data.shape, position)
        try:
            # Run YOLO object detection on the frame
            results = self.model.predict(data,
                                            device="cpu",
                                            imgsz=config.COLOR_DETECTION_IMG_SIZE,
                                            conf=config.COLOR_DETECTION_CONF_THRESH,
                                            iou=config.COLOR_DETECTION_IOU_THRESH,
                                            half=False,
                                            verbose=False)
        except Exception as e:
            self._logger.error("YOLO prediction error: %s", e)
            return

        # Get detected boxes
        dets = results[0].boxes if len(results) else []

        for box in dets:
            # Convert box to integer coordinates
            xyxy = box.xyxy.cpu().numpy().astype(int)[0] if hasattr(box.xyxy, "cpu") else np.array(box.xyxy).astype(int)[0]
            x1, y1, x2, y2 = xyxy
            w, h = x2 - x1, y2 - y1
            if w*h < config.COLOR_DETECTION_MIN_BOX_AREA:
                continue

            roi = data[y1:y2, x1:x2]
            if roi.size == 0:
                continue

            # Convert ROI to HSV for color detection
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            mask1 = cv2.inRange(hsv, np.array(self._colorLowerUpper["lower1"]), np.array(self._colorLowerUpper["upper1"]))
            mask2 = cv2.inRange(hsv, np.array(self._colorLowerUpper["lower2"]), np.array(self._colorLowerUpper["upper2"]))
            mask = cv2.bitwise_or(mask1, mask2)
            red_ratio = cv2.countNonZero(mask) / (roi.shape[0]*roi.shape[1]+1e-6)

            self._logger.debug("Red ratio in box: %.3f", red_ratio)
            
            if red_ratio >= config.COLOR_DETECTION_THRESH:
                # Call the callback with the position
                self.callback(position)
                
                self._logger.info("%s object detected at position %s", self.color.capitalize(), position)

                # Stop checking other boxes once the color is detected
                return

        self._logger.debug("No %s object detected in this frame.", self.color)

    def _process(self) -> None:
        """
        @brief Reads framesWithTelemetry from the queue and detects colors.
        """
        while self._running:
            try:
                # Get a FrameWithTelemetry from the queue
                fwt = self.queue.get(timeout=0.1)
            except Empty:
                # Queue is empty
                self._logger.debug("Queue empty, waiting for frames...")
                continue

            try:
                # Process the frame for red detection
                self._detect_color(fwt)
            except Exception as e:
                self._logger.error("Error processing frame: %s", e)
