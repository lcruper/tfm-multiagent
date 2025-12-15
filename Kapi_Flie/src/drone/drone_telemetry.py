"""
Drone Telemetry Module
----------------------

This module implements a UDP listener that receives telemetry packets from a drone.
It handles battery and pose packets, maintains the latest telemetry state, and
optionally integrates with a movement simulator.
"""

import config
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
    UDP telemetry listener for a drone. Maintains the latest telemetry state.

    This class receives two types of UDP packets:
        - Battery packets
        - Pose packets

    """

    def __init__(self,
                 drone_ip: str,
                 drone_port: int,
                 local_port: int,
                 simulator: Optional[IMovementSimulator] = None) -> None:
        """
        Creates a DroneTelemetry instance.
        
        Args:
            drone_ip (str): IP address of the drone sending UDP packets.
            drone_port (int): UDP port on the drone for handshake messages.
            local_port (int): Local UDP port to listen for incoming telemetry.
            simulator (Optional[IMovementSimulator]): Optional simulator for generating x/y coordinates of the drone.
        """
        self.drone_ip: str = drone_ip
        self.drone_port: int = drone_port
        self.local_port: int = local_port
        self.simulator: Optional[IMovementSimulator] = simulator

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
    # Public metodhs
    # ----------------------------------------------------------------------
    def start(self) -> None:
        """Start the telemetry listener in a background thread."""
        if self._running:
            self._logger.warning("Already running.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()
        self._logger.info("Started.")

    def stop(self) -> None:
        """Stop the listener and close the UDP socket."""
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

        with self._lock:
            self._telemetry = TelemetryData(
                pose=Pose(
                    position=Position(0, 0, 0),
                    orientation=Orientation(0, 0, 0)
                ),
                battery=Battery(voltage=0)
            )

        self._logger.info("Stopped.")

    def get_telemetry(self) -> TelemetryData:
        """
        Get a thread-safe copy of the latest telemetry data.

        Returns:
            TelemetryData: Latest telemetry snapshot. If a simulator is active,
                the (x, y) position is overridden with simulated values.
        """
        with self._lock:
            telemetry_copy = deepcopy(self._telemetry)

        if self.simulator and getattr(self.simulator, "_active", False):
            xy = self.simulator.get_xy()
            if xy is not None:
                telemetry_copy = TelemetryData(
                    pose=Pose(
                        position=Position(xy.x, xy.y, telemetry_copy.pose.position.z),
                        orientation=deepcopy(telemetry_copy.pose.orientation)
                    ),
                    battery=deepcopy(telemetry_copy.battery)
                )
        return telemetry_copy

    # ----------------------------------------------------------------------
    # Internal methods
    # ----------------------------------------------------------------------
    def _send_handshake(self) -> None:
        """Send handshake packet to the drone to start telemetry."""
        if not self._sock:
            return
        try:
            self._logger.info("Sending handshake to %s:%d", self.drone_ip, self.drone_port)
            self._sock.sendto(config.HANDSHAKE_PACKET, (self.drone_ip, self.drone_port))
        except Exception as e:
            self._logger.error("Error sending handshake: %s", e)

    def _start_communication(self) -> None:
        """Initialize UDP socket, bind, and perform handshake with drone."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.bind(("0.0.0.0", self.local_port))
        self._sock.settimeout(config.DRONE_UDP_TIMEOUT)
        self._logger.info("Listening UDP on port %d...", self.local_port)

        for _ in range(config.DRONE_UDP_HANDSHAKE_RETRIES):
            try:
                self._send_handshake()
                sleep(config.DRONE_UDP_HANDSHAKE_RETRY_DELAY)
            except Exception:
                pass

    def _process_battery_packet(self, payload: bytes) -> None:
        """
        Update internal battery state from a packet.

        Args:
            payload (bytes): Raw payload of the battery packet.
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
        Update internal pose state from a packet.

        Args:
            payload (bytes): Raw payload of the pose packet.
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
        """Background thread to receive and process UDP telemetry packets."""
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
