from configuration import drone_telemetry as config
import socket 
import struct
import threading
import logging
from copy import deepcopy
from time import sleep
from typing import Optional

from interfaces.interfaces import ITelemetry, IMovementSimulator
from structures.structures import Battery, Position, Orientation, Pose, TelemetryData

class DroneTelemetry(ITelemetry):
    """
    UDP telemetry listener for a drone.

    This class receives real-time telemetry from a drone via UDP. It maintains
    the latest telemetry snapshot including position, orientation, and battery
    voltage. Optionally, a movement simulator can override x/y coordinates.

    The listener runs in a background thread and updates internal telemetry safely. 
    Two types of packets are processed:
        - Battery packets: update voltage
        - Pose packets: update position (x, y, z) and orientation (roll, pitch, yaw)
    """

    def __init__(self,
                 drone_ip: str,
                 drone_port: int,
                 local_port: int,
                 simulator: Optional[IMovementSimulator] = None) -> None:
        """
        Creates a DroneTelemetry instance.

        The instance starts with default telemetry (position 0,0,0 and voltage 0V)
        and the telemetry listener is idle. It starts listening in a background thread by calling start().

        Args:
            drone_ip (str): IP address of the drone sending UDP telemetry packets.
            drone_port (int): UDP port on the drone for handshake messages.
            local_port (int): Local UDP port to listen for incoming telemetry packages.
            simulator (Optional[IMovementSimulator]): Optional simulator to provide x/y drone coordinates.
        """
        self._drone_ip: str = drone_ip
        self._drone_port: int = drone_port
        self._local_port: int = local_port
        self._simulator: Optional[IMovementSimulator] = simulator

        self._telemetry: TelemetryData = TelemetryData(
            pose=Pose(
                position=Position(0, 0, 0),
                orientation=Orientation(0, 0, 0)
            ),
            battery=Battery(voltage=0)
        )

        self._sock: Optional[socket.socket] = None
    
        self._lock: threading.Lock = threading.Lock()
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None

        self._logger: logging.Logger  = logging.getLogger("DroneTelemetry")
        
    # ----------------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """
        Starts the telemetry listener.

        Launches a background thread that continuously receives UDP packets
        and updates internal telemetry. 
        """
        if self._running:
            self._logger.warning("Already running.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        self._logger.info("Started.")

    def stop(self) -> None:
        """
        Stops the telemetry listener.

        Signals the background thread to terminate and closes the UDP socket. 
        No telemetry internal state is updated
        """
        if not self._running:
            self._logger.warning("Already stopped.")
            return

        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

        if self._thread:
            self._thread.join(timeout=1.0)
            if self._thread.is_alive():
                self._logger.warning("Did not stop in time.")
            self._thread = None

        self._logger.info("Stopped.")

    def get_telemetry(self) -> TelemetryData:
        """
        Returns a copy of the latest telemetry data.

        The returned telemetry includes position, orientation, and battery voltage.
        If a simulator is active, the x/y coordinates are replaced with simulated
        values while z and orientation remain from the last received packet.

        Returns:
            TelemetryData: Thread-safe copy of the current telemetry.
        """
        with self._lock:
            telemetry_copy = deepcopy(self._telemetry)

        if self._simulator and getattr(self._simulator, "_active", False):
            xy = self._simulator.get_xy()
            if xy is not None:
                telemetry_copy = TelemetryData(
                    pose=Pose(
                        position=Position(xy.x, xy.y, telemetry_copy.pose.position.z),
                        orientation=deepcopy(telemetry_copy.pose.orientation)
                    ),
                    battery=deepcopy(telemetry_copy.battery)
                )
        return telemetry_copy
    
    def get_simulator(self) -> Optional[IMovementSimulator]:
        """
        Returns the movement simulator.

        Returns:
            IMovementSimulator: The movement simulator if set, else None.
        """
        return self._simulator 

    # ----------------------------------------------------------------------
    # Private methods
    # ----------------------------------------------------------------------
    
    def _send_handshake(self) -> None:
        """
        Sends handshake packet to the drone to start telemetry.
        
        It assumes the UDP socket is already created and bound.
        """
        if not self._sock:
            return
        
        try:
            self._logger.info("Sending handshake to %s:%d", self._drone_ip, self._drone_port)
            self._sock.sendto(config.HANDSHAKE_PACKET, (self._drone_ip, self._drone_port))
        except Exception as e:
            self._logger.error("Error sending handshake: %s", e)

    def _start_communication(self) -> None:
        """
        Initializes the UDP socket and perform handshake.

        Binds the socket to the local listening port and sends handshake
        packets multiple times to start telemetry from the drone.
        """
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(("0.0.0.0", self._local_port))
        self._sock.settimeout(config.DRONE_UDP_TIMEOUT)
        self._logger.info("Listening UDP on port %d...", self._local_port)

        for _ in range(config.DRONE_UDP_HANDSHAKE_RETRIES):
            try:
                self._send_handshake()
                sleep(config.DRONE_UDP_HANDSHAKE_RETRY_DELAY)
            except Exception:
                pass

    def _process_battery_packet(self, payload: bytes) -> None:
        """
        Processes a battery packet.

        Extracts voltage from the payload and updates internal telemetry
        in a thread-safe manner.

        Args:
            payload (bytes): Raw UDP payload of the battery packet.
        """
        if len(payload) < config.STRUCT_BATTERY.size:
            self._logger.warning(
                "Battery payload too short (%d bytes, expected %d)",
                len(payload),
                config.STRUCT_BATTERY.size
            )
            return

        (voltage,) = config.STRUCT_BATTERY.unpack_from(payload)
        with self._lock:
            self._telemetry = TelemetryData(
                pose=deepcopy(self._telemetry.pose),
                battery=Battery(voltage=voltage)
            )
        self._logger.debug("Updated battery: %.2f V", voltage)

    def _process_pose_packet(self, payload: bytes) -> None:
        """
        Processes a pose packet.

        Extracts position (x, y, z) and orientation (roll, pitch, yaw) from
        the payload and updates internal telemetry in a thread-safe way.

        Args:
            payload (bytes): Raw UDP payload of the pose packet.
        """
        if len(payload) < config.STRUCT_POSE.size:
            self._logger.warning(
                "Pose payload too short (%d bytes, expected %d)",
                len(payload),
                config.STRUCT_POSE.size
            )
            return
        
        x, y, z, roll, pitch, yaw = config.STRUCT_POSE.unpack_from(payload)
        with self._lock:
            self._telemetry = TelemetryData(
                pose=Pose(
                    position=Position(x, y, z),
                    orientation=Orientation(roll, pitch, yaw)
                ),
                battery=deepcopy(self._telemetry.battery)
            )
        self._logger.debug("Updated pose: %s", self._telemetry.pose)

    def _listen(self) -> None:
        """
        Background thread that receives and processes UDP telemetry packets.
        
        This method runs in a loop, receiving packets and dispatching them
        to the appropriate processing methods until stopped.
        """
        try:
            self._start_communication()
            while self._running:
                try:
                    packet, addr = self._sock.recvfrom(config.DRONE_UDP_BUFFER_SIZE)
                    if not packet:
                        continue

                    packet_id = packet[0]
                    payload = packet[1:]

                    if packet_id == config.PACKET_ID_BATTERY:
                        self._process_battery_packet(payload)
                    elif packet_id == config.PACKET_ID_POSE:
                        self._process_pose_packet(payload)

                except socket.timeout:
                    continue
                except struct.error as e:
                    self._logger.error("Unpack error: %s", e)
                except OSError as e:
                    if self._running:
                        self._logger.error("Socket error: %s", e)
                    break

        except Exception as e:
            self._logger.critical("Fatal socket error: %s", e)
        finally:
            if self._sock:
                try:
                    self._sock.close()
                except Exception:
                    pass
                self._sock = None
