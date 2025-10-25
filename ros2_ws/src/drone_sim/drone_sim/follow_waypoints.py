#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose
from gazebo_msgs.srv import SetEntityState
from gazebo_msgs.msg import EntityState
import time
import math

class DroneWaypoints(Node):
    def __init__(self):
        super().__init__('drone_waypoints_smooth')

        # Servicio de Gazebo para mover el dron
        self.cli = self.create_client(SetEntityState, '/set_entity_state')
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Esperando servicio /set_entity_state...")

        self.get_logger().info("Servicio /set_entity_state disponible ✅")

        # Lista de estaciones base
        self.waypoints = [
            (2.0, 2.0, 1.0),
            (6.0, 2.0, 1.0),
            (4.0, 6.0, 1.0)
        ]

        self.rate = 0.05  # intervalo de actualización (s)
        self.speed = 0.5  # m/s para interpolación

    def move_drone(self, start, end):
        """Interpolación lineal entre start y end"""
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        dz = end[2] - start[2]
        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        steps = max(int(distance / (self.speed * self.rate)), 1)

        for i in range(steps + 1):
            x = start[0] + dx * i / steps
            y = start[1] + dy * i / steps
            z = start[2] + dz * i / steps

            state_msg = EntityState()
            state_msg.name = "drone"
            state_msg.pose.position.x = float(x)
            state_msg.pose.position.y = float(y)
            state_msg.pose.position.z = float(z)
            state_msg.pose.orientation.x = 0.0
            state_msg.pose.orientation.y = 0.0
            state_msg.pose.orientation.z = 0.0
            state_msg.pose.orientation.w = 1.0

            req = SetEntityState.Request()
            req.state = state_msg
            self.cli.call_async(req)
            time.sleep(self.rate)

    def run(self):
        # Ciclo continuo entre waypoints
        while rclpy.ok():
            for i in range(len(self.waypoints)):
                start = self.waypoints[i]
                end = self.waypoints[(i + 1) % len(self.waypoints)]
                self.get_logger().info(f"Moviendo dron de {start} a {end}")
                self.move_drone(start, end)


def main(args=None):
    rclpy.init(args=args)
    node = DroneWaypoints()
    try:
        node.run()
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
