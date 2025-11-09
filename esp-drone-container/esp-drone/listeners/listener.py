import socket
import struct

UDP_IP_ESP32 = "192.168.43.42"
UDP_PORT = 2390
LOCAL_PORT = 2391  # puerto local para recibir
BUFFER_SIZE = 64
PACKET_ID_POSITION = 0x02

def calculate_cksum(data: bytes) -> int:
    return sum(data) & 0xFF

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", LOCAL_PORT))
print(f"Escuchando paquetes UDP en {LOCAL_PORT}...")

# Handshake para que ESP32 conozca nuestra IP
sock.sendto(b'\x01' + bytes([0x01]), (UDP_IP_ESP32, UDP_PORT))
print(f"Handshake enviado a {UDP_IP_ESP32}:{UDP_PORT}")

while True:
    data, addr = sock.recvfrom(BUFFER_SIZE)
    if len(data) < 2:
        continue

    received_cksum = data[-1]
    payload = data[:-1]

    if calculate_cksum(payload) != received_cksum:
        print("Checksum inválido")
        continue

    packet_id = payload[0]
    if packet_id == PACKET_ID_POSITION:
        telemetry = struct.unpack('<9f', payload[1:37])
        x, y, z, vx, vy, vz, roll, pitch, yaw = telemetry
        print(f"Pos: ({x:.2f},{y:.2f},{z:.2f}) | Vel: ({vx:.2f},{vy:.2f},{vz:.2f}) | Att: ({roll:.2f},{pitch:.2f},{yaw:.2f})")
