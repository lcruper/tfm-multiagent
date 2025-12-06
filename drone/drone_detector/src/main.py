from colored_logs import ColoredFormatter
from movement_simulator import MovementSimulator
from system import System
import time
import logging

handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter("[%(levelname)s] %(name)s: %(message)s"))

logging.basicConfig(
    level=logging.INFO,  
    handlers=[handler]
)

def main():
    system = System(
        drone_ip="192.168.43.42",
        drone_port=2390,
        local_port=2391,
        yolo_model_path="yoloModels/yolov8n.pt",
        simulator=MovementSimulator(b=0.08, w=0.6)
    )
    system.start()
    system.start_drone_simulation()

    try:
        while True:
            time.sleep(1) 
    except KeyboardInterrupt:
        system.stop()

if __name__ == "__main__":
    main()
