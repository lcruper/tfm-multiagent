import socket
import struct

# -----------------------------
# UDP Configuration
# -----------------------------
UDP_IP_ESP32 = "192.168.43.42"
UDP_PORT_ESP32 = 2390
LOCAL_PORT = 2391
BUFFER_SIZE = 128

PACKET_ID_BATTERY = 0x01
PACKET_ID_POSITION = 0x02
NBR_OF_MOTORS = 4

# -----------------------------
# Checksum calculation
# -----------------------------
def calculate_cksum(data: bytes) -> int:
    return sum(data) & 0xFF

# -----------------------------
# UDP Socket Setup
# -----------------------------
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", LOCAL_PORT))
print(f"Listening UDP on port {LOCAL_PORT}...")

# Send handshake
sock.sendto(b'\x01' + bytes([0x01]), (UDP_IP_ESP32, UDP_PORT_ESP32))
print(f"Handshake sent to {UDP_IP_ESP32}:{UDP_PORT_ESP32}")

# -----------------------------
# Main Loop
# -----------------------------
while True:
    packet, addr = sock.recvfrom(BUFFER_SIZE)

    packet_id = packet[0]
    payload = packet[1:-1] 

    # -----------------------------
    # Battery Packet
    # -----------------------------
    if packet_id == PACKET_ID_BATTERY:
        fmt = "<3fB4H4f"
        unpacked = struct.unpack(fmt, payload[:struct.calcsize(fmt)])
        vbatt, vbattMin, vbattMax, state = unpacked[:4]
        pwm = unpacked[4:4 + NBR_OF_MOTORS]
        vmotor = unpacked[4 + NBR_OF_MOTORS:]

        state_dict = {0: "CHARGED", 1: "CHARGING", 2: "LOW_POWER", 3: "BATTERY"}
        state_str = state_dict.get(state, "UNKNOWN")

        print(f"[BATTERY MONITOR] ========================================================")
        print(f"Battery: {vbatt:.2f}V (Min: {vbattMin:.2f}V, Max: {vbattMax:.2f}V) | State: {state_str}")
        print("[Motors] ", end="")
        for i in range(NBR_OF_MOTORS):
            print(f"M{i+1}: V={vmotor[i]:.2f}V", end=" ")
        print("\n==============================================================================\n")


    # -----------------------------
    # Position Packet
    # -----------------------------
    elif packet_id == PACKET_ID_POSITION:
        fmt = "<9f"
        telemetry = struct.unpack(fmt, payload[:struct.calcsize(fmt)])
        x, y, z, vx, vy, vz, roll, pitch, yaw = telemetry

        print("[POSITION MONITOR] ========================================================")
        print(f"Position -> x: {x:.2f}  y: {y:.2f}  z: {z:.2f} (m)")
        print(f"Velocity -> x: {vx:.2f}  y: {vy:.2f}  z: {vz:.2f} (m/s)")
        print(f"Attitude -> Roll: {roll:.2f}°  Pitch: {pitch:.2f}°  Yaw: {yaw:.2f}°")
        print("==============================================================================\n")

