import socket
import struct
import threading
from structures import Position

class DronePositionUDP:
    BUFFER_SIZE = 128
    PACKET_ID_POSITION = 0x02

    def __init__(self, drone_ip, drone_port, local_port):
        self.drone_ip = drone_ip
        self.drone_port = drone_port
        self.local_port = local_port
        
        self._position = Position(0.00, 0.00, 0.00, 
                                  0.00, 0.00, 0.00)
        self._lock = threading.Lock()
        self._running = False
        self._listen_thread = None
        self._sock = None 

    def start(self):
        if not self._running:
            self._running = True
            self._listen_thread = threading.Thread(target=self._listen_udp, daemon=True)
            self._listen_thread.start()

    def stop(self):
        self._running = False
        if self._sock:
            self._sock.close()
            self._sock = None
        if self._listen_thread:
            self._listen_thread.join()
            self._listen_thread = None

    def get_position(self):
        with self._lock:
            return Position(self._position.x, self._position.y, self._position.z,
                            self._position.roll, self._position.pitch, self._position.yaw)

    def _send_handshake(self):
        if self._sock:
            try:
                self._sock.sendto(b'\x01' + bytes([0x01]), (self.drone_ip, self.drone_port))
                print(f"[DronePositionUDP] Handshake sent to {self.drone_ip}:{self.drone_port}")
            except Exception as e:
                print(f"[DronePositionUDP] Error sending handshake: {e}")

    def _listen_udp(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self._sock.bind(("0.0.0.0", self.local_port))
            self._sock.settimeout(0.5)
            print(f"[DronePositionUDP] Listening UDP on port {self.local_port}...")
            self._send_handshake()

            fmt = "<6f"
            packet_size = struct.calcsize(fmt)

            while self._running:
                try:
                    packet, _ = self._sock.recvfrom(self.BUFFER_SIZE)
                    if not packet or packet[0] != self.PACKET_ID_POSITION:
                        continue

                    payload = packet[1:]
                    if len(payload) < packet_size:
                        print(f"[DronePositionUDP] Warning: payload too short ({len(payload)} bytes)")
                        continue

                    x, y, z, roll, pitch, yaw = struct.unpack(fmt, payload[:packet_size])
                    with self._lock:
                        self._position.x = x
                        self._position.y = y
                        self._position.z = z
                        self._position.roll = roll
                        self._position.pitch = pitch
                        self._position.yaw = yaw

                except socket.timeout:
                    continue  

                except struct.error as e:
                    print(f"[DronePositionUDP] Unpack error: {e}")

        except Exception as e:
            print(f"[DronePositionUDP] Socket error: {e}")

        finally:
            if self._sock:
                self._sock.close()
                self._sock = None
            print("[DronePositionUDP] Socket closed")
