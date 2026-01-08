from drone.matcher import Matcher
from drone.drone import Drone
from drone.drone_telemetry import DroneTelemetry
from drone.camera_capture import CameraCapture
from drone.camera_simulator import CameraSimulator
from drone.viewer import Viewer
from drone.color_detection import ColorDetection
from drone.movementSimulator.spiral_movement_simulator import SpiralMovementSimulator
from robotDog.robot_dog_simulator import RobotDogSimulator
from operation.operation_controller import OperationController
from operation.operation_visualizer import OperationVisualizer
from drone.movementSimulator.zigzag_movement_simulator import ZigzagMovementSimulator
from utils.logs import ColoredFormatter, LoggerNameFilter
from planners.nearest_neighbor_planner import NearestNeighborPlanner
import logging

import configuration

handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter("[%(levelname)s] %(name)s: %(message)s"))

logging.basicConfig(
    level=logging.INFO,  
    handlers=[handler]
)

spiralMovement = SpiralMovementSimulator(
    configuration.movement_simulator.SPIRAL_SIMULATOR_RADIAL_GROWTH,
    configuration.movement_simulator.SPIRAL_SIMULATOR_LINEAR_SPEED
)

zigzagMovement = ZigzagMovementSimulator(
    configuration.movement_simulator.ZIGZAG_SIMULATOR_MAX_HORIZONTAL_DISTANCE,
    configuration.movement_simulator.ZIGZAG_SIMULATOR_LINEAR_SPEED
)

telemetry = DroneTelemetry(
    configuration.drone_telemetry.DRONE_IP, 
    configuration.drone_telemetry.DRONE_PORT, 
    configuration.drone_telemetry.LOCAL_PORT, 
    spiralMovement
)

camera = CameraCapture(
    configuration.camera_capture.CAMERA_STREAM_URL, 
    configuration.camera_capture.CAMERA_FLASH_URL
)

cameraSimulator = CameraSimulator(None,None)

matcher = Matcher(telemetry, cameraSimulator)

color_detector = ColorDetection(configuration.color_detection.COLOR_DETECTION_COLOR, configuration.color_detection.YOLO_MODEL_PATH)

viewer = Viewer()

explorer = Drone(
    telemetry=telemetry,
    camera=cameraSimulator,
    matcher=matcher,
    color_detector=color_detector,
    viewer=viewer
) 

inspector = RobotDogSimulator(configuration.robot_dog.ROBOT_DOG_SPEED)

planner = NearestNeighborPlanner()

controller = OperationController(
    explorer_robot=explorer, 
    inspector_robot=inspector, 
    planner=planner, 
    base_positions_path=configuration.operation.BASE_POSITIONS_PATH
)

visualizer = OperationVisualizer(controller)
visualizer.start()
