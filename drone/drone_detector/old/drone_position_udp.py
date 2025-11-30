# Import necessary modules
import socket
import struct
import threading
import logging
from structures import Position

class DronePositionUDP:
    """
    @brief Receives drone position data via UDP and keeps the latest position safely accessible.

    This class listens for UDP packets from an ESP32-drone. The expected packet format is:

    - Byte 0: Packet ID (0x02 for position)
    - Bytes 1..: Payload containing 6 floats in little-endian format:
        [x, y, z, roll, pitch, yaw]

    The listener runs in a background thread and keeps the last known position internally.
    """
    BUFFER_SIZE = 128                            # Maximum UDP packet size
    PACKET_ID_POSITION = 0x02                    # Packet ID for position packets
    HANDSHAKE_PACKET = b'\x01' + bytes([0x01])   # Handshake packet to initiate communication

    def __init__(self, drone_ip, drone_port, local_port):
        """
        @brief Constructor.

        @param drone_ip     IP address of the drone sending UDP packets.
        @param drone_port   UDP port on the drone to which handshake messages will be sent.
        @param local_port   Local port where this object will listen for incoming packets.
        """
        self.drone_ip = drone_ip
        self.drone_port = drone_port
        self.local_port = local_port
        
        self._position = Position(0, 0, 0, 0, 0, 0)     # Last known drone position
        self._lock = threading.Lock()                   # Lock for thread-safe access to position
        
        self._running = False                           # Flag to control the background listener thread
        self._listen_thread = None                      # Listener thread
        self._sock = None                               # UDP socket

        # Struct for unpacking 6 float values: x, y, z, roll, pitch, yaw
        self._struct_pose = struct.Struct("<6f")
        self._expected_size = self._struct_pose.size

        # Logger
        self._logger = logging.getLogger("DronePositionUDP")

    # ----------------------------------------------------------------------
    # Control
    # ----------------------------------------------------------------------
    def start(self):
        """
        @brief Starts the background listener thread.

        Creates a UDP socket, binds it, and begins listening for incoming
        position packets. Also sends an initial handshake packet to the drone.
        """
    def start(self):
        if self._running:
            self._logger.warning("Listener already running.")
            return
        
        self._logger.info("Starting listener...")
        self._running = True
        self._listen_thread = threading.Thread(target=self._listen_udp, daemon=True)
        self._listen_thread.start()
        self._logger.info("Listener started.")

    def stop(self):
        """
        @brief Stops the listener and closes the socket.

        The listener thread will terminate gracefully, and resources will be
        released. Calling stop() multiple times is safe.
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
        if self._listen_thread:
            self._listen_thread.join(timeout=1.0)
            self._listen_thread = None
        self._logger.info("Listener stopped.")

    # ----------------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------------
    def get_position(self):
        """
        @brief Retrieves the latest known drone position.

        @return Position A new Position object with the last received coordinates and orientation.
        """
        with self._lock:
            return Position(
                self._position.x, 
                self._position.y, 
                self._position.z,
                self._position.roll, 
                self._position.pitch, 
                self._position.yaw
            )

    # ----------------------------------------------------------------------
    # Internal methods
    # ----------------------------------------------------------------------
    def _send_handshake(self):
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
    
    def _listen_udp(self):
        """
        @brief Internal listener loop.

        Runs in a background thread and waits for position packets.
        Each valid packet updates the internal Position object.
        """
        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._sock.bind(("0.0.0.0", self.local_port))
            self._sock.settimeout(0.5)
            self._logger.info(f"Listening UDP on port {self.local_port}...")
            
            self._send_handshake()

            while self._running:
                try:
                    packet, addr = self._sock.recvfrom(self.BUFFER_SIZE)
                    self._logger.debug(f"Received packet from {addr} of size {len(packet)}")
                    
                    # Validate packet
                    if not packet or packet[0] != self.PACKET_ID_POSITION:
                        self._logger.debug("Ignoring non-position packet")
                        continue

                    payload = packet[1:]
                    
                    # Validate expected payload size
                    if len(payload) < self._expected_size:
                        self._logger.warning(
                            f"Payload too short ({len(payload)} bytes, expected {self._expected_size})"
                        )
                        continue

                    # Unpack position data: 6 floats
                    x, y, z, roll, pitch, yaw = self._struct_pose.unpack_from(payload)

                    # Update internal position safely
                    with self._lock:
                        self._position.x = x
                        self._position.y = y
                        self._position.z = z
                        self._position.roll = roll
                        self._position.pitch = pitch
                        self._position.yaw = yaw

                    self._logger.debug(f"Updated position: {self._position}")

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