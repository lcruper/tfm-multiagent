from drone.matcher import Matcher
from drone.drone import Drone
from drone.drone_telemetry import DroneTelemetry
from drone.camera_capture import CameraCapture
from drone.camera_simulator import CameraSimulator
from drone.viewer import Viewer
from drone.color_detection import ColorDetection
from drone.spiral_movement_simulator import SpiralMovementSimulator
from robotDog.robot_dog import RobotDog
from operation.operation_controller import OperationController
from operation.operation_visualizer import OperationVisualizer
from utils.logs import ColoredFormatter, LoggerNameFilter
from planners.nearest_neighbor_planner import NearestNeighborPlanner
import logging

import configuration.config as config

handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter("[%(levelname)s] %(name)s: %(message)s"))

logging.basicConfig(
    level=logging.INFO,  
    handlers=[handler]
)

telemetry = DroneTelemetry(
    config.DRONE_IP, 
    config.DRONE_PORT, 
    config.LOCAL_PORT, 
    SpiralMovementSimulator(
        config.SPIRAL_SIMULATOR_RADIAL_GROWTH, 
        config.SPIRAL_SIMULATOR_LINEAR_SPEED
    )
)

camera = CameraCapture(
    config.CAMERA_STREAM_URL, 
    config.CAMERA_FLASH_URL
)

cameraSimulator = CameraSimulator(None,None)

matcher = Matcher(telemetry, cameraSimulator)

color_detector = ColorDetection(config.COLOR_DETECTION_COLOR, config.YOLO_MODEL_PATH)

viewer = Viewer()

explorer = Drone(
    telemetry=telemetry,
    camera=cameraSimulator,
    matcher=matcher,
    color_detector=color_detector,
    viewer=viewer
) 

inspector = RobotDog(config.ROBOT_DOG_SPEED)

planner = NearestNeighborPlanner()

controller = OperationController(
    explorer_robot=explorer, 
    inspector_robot=inspector, 
    planner=planner, 
    base_positions_path=config.BASE_POSITIONS_PATH
)

visualizer = OperationVisualizer(controller)
visualizer.start()
