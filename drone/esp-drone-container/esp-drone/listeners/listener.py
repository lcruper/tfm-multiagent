import socket
import struct

# -----------------------------
# UDP Configuration
# -----------------------------
UDP_IP_ESP32 = "192.168.43.42"
UDP_PORT_ESP32 = 2390
LOCAL_PORT = 2391
BUFFER_SIZE = 128

PACKET_ID_POSITION = 0x02

# -----------------------------
# UDP Socket Setup
# -----------------------------
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", LOCAL_PORT))
print(f"Listening UDP on port {LOCAL_PORT}...")

sock.sendto(b'\x01' + bytes([0x01]), (UDP_IP_ESP32, UDP_PORT_ESP32))
print(f"Handshake sent to {UDP_IP_ESP32}:{UDP_PORT_ESP32}")

# -----------------------------
# Listening on port
# -----------------------------
while True:
    packet, _ = sock.recvfrom(BUFFER_SIZE)
    packet_id = packet[0]
    payload = packet[1:]

    if packet_id == PACKET_ID_POSITION: 
        fmt = "<6f"
        telemetry = struct.unpack(fmt, payload[:struct.calcsize(fmt)])
        x, y, z, roll, pitch, yaw = telemetry
        print(f"[POSITION] x={x:.2f}, y={y:.2f}, z={z:.2f} (m) | "
                f"roll={roll:.2f}, pitch={pitch:.2f}, yaw={yaw:.2f} (°)")