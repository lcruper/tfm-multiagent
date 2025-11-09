import socket
import struct
import sys
import threading

from collections import deque
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

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
# UDP Socket Setup
# -----------------------------
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", LOCAL_PORT))
sock.setblocking(False)
print(f"Listening UDP on port {LOCAL_PORT}...")

sock.sendto(b'\x01' + bytes([0x01]), (UDP_IP_ESP32, UDP_PORT_ESP32))
print(f"Handshake sent to {UDP_IP_ESP32}:{UDP_PORT_ESP32}")

# -----------------------------
# Store positions for plotting
# -----------------------------
x_data = deque(maxlen=200)
y_data = deque(maxlen=200)
z_data = deque(maxlen=200)
battery_info = {"vbatt": 0.0, "state": "UNKNOWN"}

# -----------------------------
# PyQt5 + Matplotlib Plot
# -----------------------------
class DroneMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drone Monitor")
        self.setGeometry(100, 100, 900, 700)

        self.main_widget = QWidget()
        self.layout = QVBoxLayout(self.main_widget)

        # Battery
        self.battery_label = QLabel("Battery: 0.00 V | State: UNKNOWN", self)
        self.battery_label.setStyleSheet("font-size: 18px; font-weight: bold; color: green;")
        self.layout.addWidget(self.battery_label)

        # Trajectory 
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.setCentralWidget(self.canvas)
        self.ax = self.figure.add_subplot(111, projection='3d')
        self.ax.set_xlim(-6.5, 6.5)
        self.ax.set_ylim(-6.5, 6.5)
        self.ax.set_zlim(0, 2)
        self.ax.set_xlabel('X (m)')
        self.ax.set_ylabel('Y (m)')
        self.ax.set_zlabel('Z (m)')
        self.ax.set_title('Drone Trajectory')
        self.layout.addWidget(self.canvas)

        self.setCentralWidget(self.main_widget)

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_display)
        self.timer.start(100)

    def update_display(self):
        # Battery
        vbatt = battery_info["vbatt"]
        state = battery_info["state"]
        color = "green"
        if state == "LOW_POWER":
            color = "red"
        elif state == "CHARGING":
            color = "orange"
        self.battery_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        self.battery_label.setText(f"Battery: {vbatt:.2f} V | State: {state}")

        # Trajectory
        self.ax.scatter(0, 0, 0, color='red', s=60, label='Origen')
        n = len(x_data)
        if n > 1:
            colors = np.linspace(0.1, 1.0, n)
            for i in range(1, n):
                self.ax.plot([x_data[i-1], x_data[i]],
                             [y_data[i-1], y_data[i]],
                             [z_data[i-1], z_data[i]],
                             color=(0, 0, 1, colors[i]))

        self.canvas.draw()

# -----------------------------
# Thread for UDP listener
# -----------------------------
def udp_listener():
    while True:
        try:
            packet, _ = sock.recvfrom(BUFFER_SIZE)
            packet_id = packet[0]
            payload = packet[1:-1]

            # Battery
            if packet_id == PACKET_ID_BATTERY:
                fmt = "<3fB4f"
                unpacked = struct.unpack(fmt, payload[:struct.calcsize(fmt)])
                vbatt, vbattMin, vbattMax, state = unpacked[:4]
                vmotor = unpacked[4:]
                state_dict = {0:"CHARGED",1:"CHARGING",2:"LOW_POWER",3:"BATTERY"}
                state_str = state_dict.get(state,"UNKNOWN")
                battery_info["vbatt"] = vbatt
                battery_info["state"] = state_str
                print(f"[BATTERY] V={vbatt:.2f} (Min={vbattMin:.2f} Max={vbattMax:2f}) | State={state_str} | " +
                      " ".join([f"M{i+1}={vmotor[i]:.2f}" for i in range(NBR_OF_MOTORS)]))

            # Trajectory
            elif packet_id == PACKET_ID_POSITION:
                fmt = "<9f"
                telemetry = struct.unpack(fmt, payload[:struct.calcsize(fmt)])
                x, y, z, vx, vy, vz, roll, pitch, yaw = telemetry
                x_data.append(x)
                y_data.append(y)
                z_data.append(z)
                print(f"[POSITION] x={x:.2f}, y={y:.2f}, z={z:.2f} | "
                      f"vx={vx:.2f}, vy={vy:.2f}, vz={vz:.2f} | "
                      f"roll={roll:.2f}, pitch={pitch:.2f}, yaw={yaw:.2f}")

        except BlockingIOError:
            continue

# -----------------------------
# Run everything
# -----------------------------
if __name__ == "__main__":
    listener_thread = threading.Thread(target=udp_listener, daemon=True)
    listener_thread.start()

    app = QApplication(sys.argv)
    window = DroneMonitor()
    window.show()
    sys.exit(app.exec_())
