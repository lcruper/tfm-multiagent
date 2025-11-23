import socket
import struct
import threading
from structures import Position

class DronePositionUDP:
    PACKET_ID_POSITION = 0x02

    def __init__(self, drone_ip, drone_port, local_port):
        self.drone_ip = drone_ip
        self.drone_port = drone_port
        self.local_port = local_port
        
        self._position = Position(0.0, 0.0)
        self._lock = threading.Lock()
        self._running = False
        self._listen_thread = None

    def start(self):
        if not self._running:
            self._running = True
            self._listen_thread = threading.Thread(target=self._listen_udp, daemon=True)
            self._listen_thread.start()
            print(f"[DronePositionUDP] Listening UDP on port {self.local_port}...")

    def stop(self):
        self._running = False
        if self._listen_thread:
            self._listen_thread.join()

    def get_position(self):
        with self._lock:
            return Position(self._position.x, self._position.y)


    def _send_handshake(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(b'\x01\x01', (self.drone_ip, self.drone_port))
        sock.close()
        print(f"[DronePositionUDP] Handshake sent to {self.drone_ip}:{self.drone_port}")

    def _listen_udp(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", self.local_port))
        sock.setblocking(False)
        self._send_handshake()

        while self._running:
            try:
                packet, _ = sock.recvfrom(128)
                if not packet or packet[0] != self.PACKET_ID_POSITION:
                    continue

                x, y = struct.unpack("<2f", packet[1:1+8])
                with self._lock:
                    self._position.x = x
                    self._position.y = y

            except BlockingIOError:
                continue
