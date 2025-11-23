from drone_position_udp import DronePositionUDP
from camera_red_detector import CameraRedDetector
from structures import Position

class System:
    def __init__(self, drone_ip, drone_port, local_port, camera_url):
        self.drone = DronePositionUDP(drone_ip, drone_port, local_port)
        self.detector = CameraRedDetector(
            drone=self.drone,
            camera_url=camera_url,
            callback=self._red_detected_callback
        )
        self.red_positions = []

    def start(self):
        print("[SYSTEM] Starting system...")
        self.drone.start()
        self.detector.start()
        print("[SYSTEM] System started.")

    def stop(self):
        print("[SYSTEM] Stopping system...")
        self.detector.stop()
        self.drone.stop()
        print("[SYSTEM] System stopped.")

    def _red_detected_callback(self, pos: Position):
        print(f"[SYSTEM] Red detected at position x={pos.x:.2f}, y={pos.y:.2f}")
        self.red_positions.append(Position(pos.x, pos.y))
