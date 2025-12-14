from drone.matcher import Matcher
from drone.drone import Drone
from drone.drone_telemetry import DroneTelemetry
from drone.camera_capture import CameraCapture 
from drone.viewer import Viewer
from core.mission import Mission
from drone.color_detection import ColorDetection
from drone.spiral_movement_simulator import SpiralMovementSimulator
from robotDog.robot_dog import RobotDog
from drone.constant_movement_simulator import ConstantMovementSimulator
from utils.logs import ColoredFormatter, LoggerNameFilter
from planners.nearest_neighbor_planner import NearestNeighborPlanner
import logging

import config

handler = logging.StreamHandler()
handler.addFilter(LoggerNameFilter("Mission"))
handler.setFormatter(ColoredFormatter("[%(levelname)s] %(name)s: %(message)s"))

logging.basicConfig(
    level=logging.INFO,  
    handlers=[handler]
)

# -------------------------
# Inicializar robots
# -------------------------
camera = CameraCapture("http://192.168.43.44:81/stream")
telemetry = DroneTelemetry(config.DRONE_IP, config.DRONE_PORT, config.LOCAL_PORT, SpiralMovementSimulator(config.SPIRAL_SIMULATOR_RADIAL_GROWTH, config.SPIRAL_SIMULATOR_ANGULAR_SPEED))
matcher = Matcher(telemetry, camera)
color_detector = ColorDetection(config.COLOR_DETECTION_COLOR, config.YOLO_MODEL_PATH, None)
viewer = Viewer()
inspector = Drone(telemetry=telemetry,
                  camera=camera,
                  matcher=matcher,
                  color_detector=color_detector,
                  viewer=viewer)
executor = RobotDog(config.ROBOT_DOG_SPEED)

planner = NearestNeighborPlanner()

mission = Mission(inspector=inspector,
                  executor=executor,
                  base_positions=[(5.0, 5.0), (10.0, 10.0)],
                  planner=planner) 

#mission.start()
mission.visualizer()
mission.wait_until_finished()
