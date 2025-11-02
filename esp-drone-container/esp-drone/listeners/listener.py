import socket
import struct

UDP_PORT = 2390
ESP32_IP = "192.168.43.42"

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", UDP_PORT))
sock.sendto(b'HELLO', (ESP32_IP, UDP_PORT))
print(f"Listening on UDP port {UDP_PORT}")

N_MOTORS = 4
SIZE_BATTERY_PACKET = 4*3 + 1 + N_MOTORS*2 + N_MOTORS*4  
SIZE_POSITION_PACKET = 9*4  

while True:
    data, addr = sock.recvfrom(1024)
    packet_type = data[0]
    payload = data[1:]

    if packet_type == 0x01 and len(payload) == SIZE_BATTERY_PACKET:
        fmt = f'fffB{N_MOTORS}H{N_MOTORS}f'
        unpacked = struct.unpack(fmt, payload)
        vbatt, vbattMin, vbattMax, state = unpacked[:4]
        pwm = unpacked[4:4+N_MOTORS]
        vmotor = unpacked[4+N_MOTORS:]
        print(f"[BATTERY] V:{vbatt:.2f} Estado:{state}")
        for i in range(N_MOTORS):
            print(f" M{i+1}: PWM={pwm[i]} V={vmotor[i]:.2f}")
        print("--------------------------")

    elif packet_type == 0x02 and len(payload) == SIZE_POSITION_PACKET:
        fmt = 'fffffffff'
        unpacked = struct.unpack(fmt, payload)
        x, y, z, vx, vy, vz, roll, pitch, yaw = unpacked
        print(f"[POSITION] Pos: x={x:.2f}, y={y:.2f}, z={z:.2f}")
        print(f" Vel: vx={vx:.2f}, vy={vy:.2f}, vz={vz:.2f}")
        print(f" Att: roll={roll:.2f}, pitch={pitch:.2f}, yaw={yaw:.2f}")
        print("--------------------------")
