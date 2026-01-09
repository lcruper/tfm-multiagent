from typing import Optional, Callable
from configuration import color_detection as config
import threading
import logging
import cv2
import numpy as np
from queue import Queue, Empty
from ultralytics import YOLO
from time import sleep

from interfaces.interfaces import AFrameConsumer
from structures.structures import FrameWithTelemetry, Position


class ColorDetection(AFrameConsumer):
    """
    Detects a specific color in objects within frames that include telemetry data.

    This class consumes FrameWithTelemetry objects from an internal queue and processes each frame
    in a background thread. For every frame, it applies a YOLO model to detect 
    objects of an specified color.

    When a detection occurs, an optional callback function can be invoked with the position associated 
    with the frame.
    """

    def __init__(self,
                 color: str,
                 yolo_model_path: str) -> None:
        """
        Creates a ColorDetection instance.

        It initializes the YOLO model, sets up the color limits based on the configuration,
        and creates the internal queue. 

        Args:
            color (str): Name of the color to detect.
            yolo_model_path (str): Path to the YOLO model file.
        """
        self._color: str = color
        self._model: YOLO = YOLO(yolo_model_path)

        self._callback: Optional[Callable[[Position], None]] = None

        self._colorLimits = config.COLOR_DETECTION_COLORS.get(color)
        if self._colorLimits is None:
            raise ValueError(f"Color '{color}' not defined in configuration.")

        self._queue = Queue(maxsize=config.COLOR_DETECTION_MAX_QUEUE_SIZE)

        self._running: bool = False
        self._thread: Optional[threading.Thread] = None

        self._logger: logging.Logger = logging.getLogger("ColorDetection")

    # ----------------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        Starts the background thread that processes frames from the queue.
        
        It continously retrives FrameWithTelemetry objects for detection and color analysis. 
        When the target color is detected, it triggers the registered callback.
        """
        if self._running:
            self._logger.warning("Already running.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._process, daemon=True)
        self._thread.start()
        self._logger.info("Started.")

    def stop(self) -> None:
        """
        Stops the background color detection thread.
        """
        if not self._running:
            self._logger.warning("Already stopped.")
            return

        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            if self._thread.is_alive():
                self._logger.warning("Did not stop in time.")
            self._thread = None
        self._logger.info("Stopped.")

    def set_callback(self, callback: Callable[[Position], None]) -> None:
        """
        Registers a callback function to be called whenever the target color is detected
        in a frame, passing the Position associated with the frame.

        Args:
            callback (Callable[[Position], None]): Callback function with position as parameter.
        """
        self._callback = callback

    # ----------------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------------
    def _process_frame(self, fwt: FrameWithTelemetry) -> None:
        """
        Processes a single frame.
        
        It runs YOLO to detect objects and extracts the corresponding
        image regions, filtering by minimum area. 
        For each region, it converts the region to HSV, applies color masks,
        and computes the proportion of matching pixels.
        If the color is detected, it triggers the callback.

        Args:
            fwt (FrameWithTelemetry): Frame with telemetry to analyze.
        """
        data = fwt.frame.data
        position = fwt.telemetry.pose.position
        self._logger.debug("Processing frame of shape %s at position %s", data.shape, position)

        try:
            results = self._model.predict(
                data,
                device="cpu",
                imgsz=config.COLOR_DETECTION_IMG_SIZE,
                conf=config.COLOR_DETECTION_CONF_THRESH,
                iou=config.COLOR_DETECTION_IOU_THRESH,
                half=False,
                verbose=False
            )
        except Exception as e:
            self._logger.error("YOLO prediction error: %s", e)
            return
        dets = results[0].boxes if len(results) else []
        self._logger.debug("YOLO detected %d objects", len(dets))

        for box in dets:
            xyxy = box.xyxy.cpu().numpy().astype(int)[0] if hasattr(box.xyxy, "cpu") else np.array(box.xyxy).astype(int)[0]
            x1, y1, x2, y2 = xyxy
            w, h = x2 - x1, y2 - y1
            if w * h < config.COLOR_DETECTION_MIN_BOX_AREA:
                continue

            roi = data[y1:y2, x1:x2]
            if roi.size == 0:
                continue

            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            mask1 = cv2.inRange(hsv, np.array(self._colorLimits["lower1"]), np.array(self._colorLimits["upper1"]))
            mask2 = None
            if "lower2" in self._colorLimits and "upper2" in self._colorLimits:
                mask2 = cv2.inRange(hsv, np.array(self._colorLimits["lower2"]), np.array(self._colorLimits["upper2"]))
            mask = mask1 if mask2 is None else cv2.bitwise_or(mask1, mask2)
            ratio = cv2.countNonZero(mask) / (roi.shape[0] * roi.shape[1] + 1e-6)

            if ratio >= config.COLOR_DETECTION_THRESH:
                if self._callback:
                    self._callback(position)
                self._logger.debug("%s object detected at position %s", self._color.capitalize(), position)
                return

    def _process(self) -> None:
        """
        Background thread method that continuously retrieves frames from the queue and
        applies color detection processing.
        """
        while self._running:
            try:
                fwt = self._queue.get(timeout=0.1)
            except Empty:
                sleep(config.COLOR_DETECTION_SLEEP_TIME)
                continue

            try:
                self._process_frame(fwt)
            except Exception as e:
                self._logger.error("Error processing frame: %s", e)

            sleep(config.COLOR_DETECTION_SLEEP_TIME)
