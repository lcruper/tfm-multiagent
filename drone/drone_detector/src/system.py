# system.py
import logging
from queue import Queue
import threading
import requests

import os
import json
from datetime import datetime

from drone_telemetry_listener import DroneTelemetryListener
from camera_capture import CameraCapture
from matcher import Matcher
from red_detection import RedDetection
from viewer import Viewer

class System:
    """
    @brief Main system class that integrates all components.
    """
    DEFAULT_PORT = 81       # Default stream port
    MAX_IP_TRIES = 5        # Max IPs to try for stream URL
    REQUEST_TIMEOUT = 5     # Timeout for HTTP requests in seconds

    def __init__(self, drone_ip: str, drone_port: int, local_port: int, yolo_model_path: str) -> None:
        """
        @brief Constructor.

        @param drone_ip     IP address of the drone sending UDP packets.
        @param drone_port   UDP port on the drone to which handshake messages will be sent.
        @param local_port   Local UDP port where this object will listen for incoming packets.
        @param yolo_model_path Path to the YOLO model for red detection.
        """     
        # Logger
        self._logger = logging.getLogger("System")

        # --- Results storage ---
        self._detections_folder = self._create_detections_folder()
        self._json_filename = None

        # --- Drone ---
        self.drone = DroneTelemetryListener(drone_ip, drone_port, local_port)
        
        # --- Camera ---
        stream_url = self._find_stream_url(drone_ip)
        if stream_url is None:
            raise RuntimeError("No working camera stream found. System cannot start without a camera.")
        self.camera = CameraCapture(stream_url)
        
        # --- Matcher ---
        self.matcher_queue = Queue(maxsize=100)
        self.matcher = Matcher(self.drone, self.camera)
        self.matcher.register_consumer(self.matcher_queue)
        
        # --- Red Detection ---
        self.red_detector = RedDetection(self.matcher_queue, yolo_model_path, callback=self._on_red_detected)
        
        # --- Viewer ---
        self.viewer = Viewer(self.matcher_queue)

        # Threading
        self._lock = threading.Lock()  # Lock for start/stop thread-safe

    # ----------------------------------------------------------------------
    # Control
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        @brief Start all subsystems thread-safe.
        """
        self._logger.info("Starting system...")

        # Initialize red positions storage
        self.red_positions = []

        # Create JSON filename with timestamp
        session_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._json_filename = os.path.join(
            self._detections_folder, f"red_detections_{session_timestamp}.json"
        )
        self._logger.info("Red detections will be saved in %s", self._json_filename)

        with self._lock:
            self.drone.start()
            self.camera.start()
            self.matcher.start()
            self.red_detector.start()
            self.viewer.start()
            self._logger.info("System started.")

    def stop(self) -> None:
        """ 
        @brief Stop all subsystems thread-safe.
        """
        with self._lock:
            self._logger.info("Stopping system...")
            self.viewer.stop()
            self.red_detector.stop()
            self.matcher.stop()
            self.camera.stop()
            self.drone.stop()
            self._logger.info("System stopped.")

        # Save red detections to JSON
        self._save_red_positions()

    # ----------------------------------------------------------------------
    # Internal methods
    # ----------------------------------------------------------------------
    def _find_stream_url(self, ip_base: str) -> str:
        """
        @brief Attempts to find a working camera stream URL by testing multiple IPs.

        @param ip_base: Base Ip
        @return: first working URL, or None if none found
        """
        parts = ip_base.split(".")
        base_prefix = ".".join(parts[:3])
        last_octet = int(parts[3])

        for k in range(1,self.MAX_IP_TRIES):
            test_ip = f"{base_prefix}.{last_octet + k}"
            url = f"http://{test_ip}:{self.DEFAULT_PORT}/stream"
            try:
                r = requests.head(url, timeout=self.REQUEST_TIMEOUT)
                if r.status_code == 405:
                    self._logger.info("Found working stream URL: %s", url)
                    return url
            except requests.RequestException:
                continue
        return None
    
    def _create_detections_folder(self) -> str:
        base_folder = "red_detections"
        os.makedirs(base_folder, exist_ok=True)
        timestamp_folder = datetime.now().strftime("%Y%m%d_%H%M%S")
        detections_folder = os.path.join(base_folder, timestamp_folder)
        os.makedirs(detections_folder, exist_ok=True)
        self._logger.info("Detections will be saved in folder: %s", detections_folder)
        return detections_folder


    def _save_red_positions(self) -> None:
        """
        @brief Saves all red detections to a JSON file.
        """
        if not self._json_filename:
            self._logger.warning("JSON filename not set, cannot save red positions")
            return

        with open(self._json_filename, "w") as f:
            json.dump(self.red_positions, f, indent=4)
        self._logger.debug("Saved %d red detections to %s", len(self.red_positions), self._json_filename)

    # ----------------------------------------------------------------------
    # Red Detection Callback
    # ----------------------------------------------------------------------
    def _on_red_detected(self, position):
        """
        @brief Called by RedDetection when a red object is detected.

        Saves the detection and flashes the drone.
        """
        self._logger.debug("Red detected at position x=%.2f, y=%.2f, z=%.2f", position.x, position.y, position.z)
        
        # Turn on flash
        try:
            self.camera.turn_on_flash() 
            self.camera.turn_off_flash()
        except Exception as e:
            self._logger.error("Failed to turn on flash: %s", e)

        # Store detection
        self.red_positions.append({
            "x": position.x,
            "y": position.y,
            "z": position.z,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
        })