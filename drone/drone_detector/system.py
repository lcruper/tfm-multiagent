from drone_position_udp import DronePositionUDP
from camera_red_detector import CameraRedDetector
from camera_preview_window import CameraPreviewWindow
from structures import Position

class System:
    def __init__(self, drone_ip, drone_port, local_port, camera_url):
        self.drone = DronePositionUDP(drone_ip, drone_port, local_port)
        self.detector = CameraRedDetector(self.drone, camera_url, self._red_detected_callback)
        self.preview = CameraPreviewWindow(self.detector._queue)
        self.red_positions = []

    def start(self):
        print("[SYSTEM] Starting system...")
        self.drone.start()
        self.detector.start()
        self.preview.start()
        print("[SYSTEM] System started.")

    def stop(self):
        print("[SYSTEM] Stopping system...")
        self.detector.stop()
        self.drone.stop()
        self.preview.stop()
        print("[SYSTEM] System stopped.")

    def _red_detected_callback(self, pos: Position):
        print(f"[SYSTEM] Red detected at position x={pos.x:.2f}, y={pos.y:.2f}, z={pos.z:.2f}")
        self.red_positions.append(Position(pos.x, pos.y, pos.z, pos.roll, pos.pitch, pos.yaw))
