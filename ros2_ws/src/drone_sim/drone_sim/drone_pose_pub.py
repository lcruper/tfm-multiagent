#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from gazebo_msgs.msg import ModelStates
from geometry_msgs.msg import PoseStamped

class DronePosePublisher(Node):
    def __init__(self):
        super().__init__('drone_pose_publisher')

        # Suscripción a /model_states de Gazebo
        self.sub = self.create_subscription(
            ModelStates,
            '/model_states',
            self.callback,
            10
        )

        # Publicador de PoseStamped para RViz
        self.pub = self.create_publisher(PoseStamped, '/drone_pose', 10)
        self.get_logger().info("DronePosePublisher started ✅")

    def callback(self, msg):
        try:
            # Buscar índice del modelo llamado "drone"
            if "drone" in msg.name:
                idx = msg.name.index("drone")
                pose = msg.pose[idx]

                pose_stamped = PoseStamped()
                pose_stamped.header.frame_id = "map"
                pose_stamped.header.stamp = self.get_clock().now().to_msg()
                pose_stamped.pose = pose

                self.pub.publish(pose_stamped)
        except Exception as e:
            self.get_logger().error(f"Error procesando /model_states: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = DronePosePublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
