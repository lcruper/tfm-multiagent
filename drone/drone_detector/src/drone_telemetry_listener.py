# drone_telemetry_listener.py
import socket
import struct
import threading
import logging

from copy import deepcopy
from structures import Battery, Position, Orientation, Pose, TelemetryData

class DroneTelemetryListener:
    """
    @brief UDP listener for drone telemetry.

    Listens for pose battery and pose packets from the drone and keeps
    internally the latest telemetry data thread-safe. 
    
    @note All get_* methods are thread-safe.
    """
    BUFFER_SIZE = 128                            # Maximum UDP packet size
    PACKET_ID_BATTERY = 0x01                     # Packet ID for battery packets
    PACKET_ID_POSE = 0x02                        # Packet ID for pose packets
    HANDSHAKE_PACKET = b'\x01' + bytes([0x01])   # Handshake packet to initiate communication

    def __init__(self, drone_ip: str, drone_port: int, local_port: int) -> None:
        """
        @brief Constructor.

        @param drone_ip     IP address of the drone sending UDP packets.
        @param drone_port   UDP port on the drone to which handshake messages will be sent.
        @param local_port   Local UDP port where this object will listen for incoming packets.
        """
        self.drone_ip = drone_ip
        self.drone_port = drone_port
        self.local_port = local_port
        
        # Last known drone telemetry data
        self._telemetry = TelemetryData(
            pose=Pose(
                position=Position(0,0,0), 
                orientation=Orientation(0,0,0)
            ),
            battery=Battery(
                voltage=0
            )
        )
        
        # UDP socket
        self._sock = None                              

        # Structs for unpacking data
        self._struct_pose = struct.Struct("<6f")        # x,y,z,roll,pitch,yaw
        self._struct_battery = struct.Struct("<f")      # battery voltage

        # Threading
        self._lock = threading.Lock()                   # Lock for thread-safe access to telemetry data
        self._running = False                           # Flag to control the background listener thread
        self._thread = None                             # Listener thread
        
        # Logger
        self._logger = logging.getLogger("DroneTelemetryListener")

    # ----------------------------------------------------------------------
    # Control
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        @brief Starts the background listener thread.

        Creates a UDP socket, binds it, and begins listening for incoming
        packets. Also sends an initial handshake packet to the drone.
        """
        if self._running:
            self._logger.warning("Listener already running.")
            return
        
        self._logger.info("Starting listener...")
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        self._logger.info("Listener started.")

    def stop(self) -> None:
        """
        @brief Stops the listener and closes the socket.

        The listener thread will terminate gracefully, and resources will be
        released.
        """
        if not self._running:
            self._logger.warning("Listener already stopped.")
            return
        
        self._logger.info("Stopping listener...")
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        self._logger.info("Listener stopped.")

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    def get_telemetry(self) -> TelemetryData:
        """
        @brief Retrieves a deep copy of the latest telemetry data.

        @return TelemetryData A new TelemetryData object with the last received telemetry data.
        """
        with self._lock:
            return deepcopy(self._telemetry)
        
    def get_battery(self) -> Battery:
        """
        @brief Retrieves a deep copy of the latest battery data.

        @return Battery A new Battery object with the last received battery data.
        """
        with self._lock:
            return deepcopy(self._telemetry.battery)

    def get_pose(self) -> Pose:
        """
        @brief Retrieves a deep copy of the latest pose data.

        @return Pose A new Pose object with the last received pose data.
        """
        with self._lock:
            return deepcopy(self._telemetry.pose)
        
    def get_position(self) -> Position:
        """
        @brief Retrieves a deep copy of the latest position data.

        @return Position A new Position object with the last received position data.
        """
        with self._lock:
            return deepcopy(self._telemetry.pose.position)
        
    def get_orientation(self) -> Orientation:
        """
        @brief Retrieves a deep copy of the latest orientation data.

        @return Orientation A new Orientation object with the last received orientation data.
        """
        with self._lock:
            return deepcopy(self._telemetry.pose.orientation)
        
    # ----------------------------------------------------------------------
    # Internal methods
    # ----------------------------------------------------------------------
    def _send_handshake(self) -> None:
        """
        @brief Sends a handshake packet to the drone.

        This lets the drone know that we are ready to receive packets.
        """
        if not self._sock:
            return
        
        try:
            self._logger.info(f"Sending handshake to {self.drone_ip}:{self.drone_port}")
            self._sock.sendto(self.HANDSHAKE_PACKET, (self.drone_ip, self.drone_port))
            self._logger.info(f"Handshake sent.")
        except Exception as e:
            self._logger.error(f"Error sending handshake: {e}")
    
    def _start_communication(self) -> None:
            """
            @brief Initializes the UDP socket and sends handshake.
            """
            self._logger.info("Initializing UDP socket...")
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.bind(("0.0.0.0", self.local_port))
            self._sock.settimeout(0.5)
            self._logger.info("UDP socket initialized.")
            self._logger.info(f"Listening UDP on port {self.local_port}...")
            
            self._send_handshake()

    def _process_battery_packet(self, payload: bytes) -> None:
        """
        @brief Processes a battery packet and updates internal state.

        @param payload The payload of the battery packet.
        """
        # Validate expected battery payload size
        if len(payload) < self._struct_battery.size:
            self._logger.warning(f"Battery payload too short ({len(payload)} bytes)")
            return 
        
        # Unpack battery data: 1 float
        (vbatt,) = self._struct_battery.unpack_from(payload)

        # Update internal battery safely
        with self._lock:
            self._telemetry.battery.voltage = vbatt
        
        self._logger.debug(f"Updated battery: {self._telemetry.battery.voltage:.2f} V")

    def _process_pose_packet(self, payload: bytes) -> None:
        """
        @brief Processes a pose packet and updates internal state.

        @param payload The payload of the pose packet.
        """
        # Validate expected pose payload size
        if len(payload) < self._struct_pose.size:
            self._logger.warning(f"Pose payload too short ({len(payload)} bytes, expected {self._struct_pose.size})")
            return 
        
        # Unpack pose data: 6 floats
        x, y, z, roll, pitch, yaw = self._struct_pose.unpack_from(payload)
        
        # Update internal pose safely
        with self._lock:
            self._telemetry.pose.position.x = x
            self._telemetry.pose.position.y = y
            self._telemetry.pose.position.z = z     
            self._telemetry.pose.orientation.roll = roll
            self._telemetry.pose.orientation.pitch = pitch
            self._telemetry.pose.orientation.yaw = yaw
        
        self._logger.debug(f"Updated pose: {self._telemetry.pose}")

    def _listen(self) -> None:
        """
        @brief Background listener thread.

        Runs in a background thread and waits for packets.
        Each valid packet updates the internal TelemetryData object.
        """
        try:
            self._start_communication()
            while self._running:
                try:
                    packet, addr = self._sock.recvfrom(self.BUFFER_SIZE)

                    # Validate packet
                    if not packet:
                        continue

                    self._logger.debug(f"Received packet from {addr} of size {len(packet)}")
                
                    packet_id = packet[0]
                    payload = packet[1:]
                    
                    # Battery packet
                    if packet_id == self.PACKET_ID_BATTERY:
                       self._process_battery_packet(payload)
                    # Pose packet
                    elif packet_id == self.PACKET_ID_POSE:
                        self._process_pose_packet(payload)
                    else:
                        self._logger.debug("Ignoring unknown packet")

                except socket.timeout:
                    continue  
                except struct.error as e:
                    self._logger.error(f"Unpack error: {e}")
                except OSError as e:
                    if self._running:
                        self._logger.error(f"Socket error: {e}")
                    break

        except Exception as e:
            self._logger.critical(f"Fatal socket error: {e}")
        
        finally:
            if self._sock:
                try:
                    self._sock.close()
                except:
                    pass
                self._sock = None

            self._logger.info("Socket closed")