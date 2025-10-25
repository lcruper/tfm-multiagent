#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point

class StationsRViz(Node):
    def __init__(self):
        super().__init__('stations_rviz')

        # Publicador de marcadores
        self.publisher = self.create_publisher(MarkerArray, '/stations', 10)

        # Lista de estaciones (x, y, z)
        self.stations = [
            (2.0, 2.0, 0.5),
            (6.0, 2.0, 0.5),
            (4.0, 6.0, 0.5)
        ]

        self.timer = self.create_timer(1.0, self.timer_callback)
        self.get_logger().info("Stations RViz node started ✅")

    def timer_callback(self):
        marker_array = MarkerArray()
        for i, (x, y, z) in enumerate(self.stations):
            marker = Marker()
            marker.header.frame_id = "map"
            marker.header.stamp = self.get_clock().now().to_msg()
            marker.ns = "stations"
            marker.id = i
            marker.type = Marker.CYLINDER
            marker.action = Marker.ADD

            # Posición de la estación
            marker.pose.position.x = x
            marker.pose.position.y = y
            marker.pose.position.z = z
            marker.pose.orientation.x = 0.0
            marker.pose.orientation.y = 0.0
            marker.pose.orientation.z = 0.0
            marker.pose.orientation.w = 1.0

            # Dimensiones del cilindro
            marker.scale.x = 0.6   # diámetro
            marker.scale.y = 0.6
            marker.scale.z = 1.0   # altura

            # Color verde
            marker.color.a = 1.0
            marker.color.r = 0.0
            marker.color.g = 1.0
            marker.color.b = 0.0

            marker_array.markers.append(marker)

        self.publisher.publish(marker_array)


def main(args=None):
    rclpy.init(args=args)
    node = StationsRViz()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
