# drone.py
"""
@file drone.py
@brief Aggregates drone components: telemetry, camera, matcher, color detector, and viewer.
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime

from interfaces.interfaces import ICamera, ITelemetry, IRobot
from drone.matcher import Matcher
from drone.color_detection import ColorDetection
from drone.viewer import Viewer
from structures.structures import Position

class Drone(IRobot):
    """
    @brief Aggregates all drone-related components: telemetry, camera, matcher, color detector and viewer.
           Provides a unified API to start/stop inspections.
    """
    def __init__(self,
                 telemetry: ITelemetry,
                 camera: ICamera,
                 matcher: Matcher,
                 color_detector: ColorDetection,
                 viewer: Viewer) -> None:
        """
        @brief Constructor.

        @param telemetry Telemetry interface for the drone
        @param camera Camera interface for the drone
        @param matcher Matcher instance for object matching 
        @param color_detector ColorDetection instance for color-specific detection 
        @param viewer Viewer instance for displaying camera frames with telemetry overlay
        """
        self.telemetry: ITelemetry = telemetry
        self.camera: ICamera = camera
        self.matcher: Matcher = matcher
        self.color_detector: ColorDetection = color_detector
        self.viewer: Viewer = viewer

        self.color_detector.callback = self._on_red_detected

        # Register consumers
        self.matcher.register_consumer(self.color_detector)  
        self.matcher.register_consumer(self.viewer)        

        # Storage for detected points
        self._detected_points: List[Dict[str, float]] = []

        # Flag to indicate if inspection is running
        self._running: bool = False                      

        # Logger
        self._logger = logging.getLogger("Drone")

    # ---------------------------------------------------
    # Control
    # ---------------------------------------------------
    def start_inspection(self) -> None:
        """
        @brief Start the drone's telemetry, camera, matcher and color detector.
        """
        if self._running:
            self._logger.warning("Drone inspection already running.")
            return
        
        self._running = True
        self._detected_points.clear()

        self.telemetry.start()
        if hasattr(self.telemetry, "simulator") and self.telemetry.simulator:
            self.telemetry.simulator.start()    
        self.camera.start()
        self.matcher.start()
        self.color_detector.start()
        self.viewer.start()

        self._logger.info("Drone inspection started.")

    def stop_inspection(self) -> List[Dict[str, float]]:
        """
        @brief Stop color detector, matcher, camera and telemetry.

        @return List of detected points.
        """
        if not self._running:
            self._logger.warning("Drone inspection already stopped.")
            return
        
        self._running = False

        self.viewer.stop()
        self.color_detector.stop()
        self.matcher.stop()
        self.camera.stop()
        if hasattr(self.telemetry, "simulator") and self.telemetry.simulator:
            self.telemetry.simulator.stop()
        self.telemetry.stop()

        self._logger.info("Drone inspection stopped.")

        return self._detected_points

    def set_callback_onFinish(self, callback: callable) -> None:
        """
        @brief Sets a callback function to be called when the drone inspection finishes.

        @param callback Function to call when inspection finishes.
        """
        self._callbackOnFinish = callback

    def set_callback_onPoint(self, callback: callable) -> None:
        """
        @brief Sets a callback function to be called when the drone reaches each point.

        @param callback Function to call when reaching each point: fn(x: float, y: float)
        """
        self._callbackOnPoint = callback

    # ---------------------------------------------------------
    # Internal Callbacks
    # ---------------------------------------------------------

    def _on_red_detected(self, position: Position) -> None:
        """
        @brief Called by ColorDetection when a colored object is detected.

        Saves the detection with its 3D position and timestamp.
        """
        self._logger.debug("Colored detected at position x=%.2f, y=%.2f, z=%.2f", position.x, position.y, position.z)

        # Turn on flash
        try:
            self.camera.turn_on_flash() 
            self.camera.turn_off_flash()
        except Exception as e:
            self._logger.error("Failed to turn on flash: %s", e)

        # Store detection
        self._detected_points.append({
            "x": position.x,
            "y": position.y,
            "z": position.z,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
        })