from system import System
import time

def main():
    system = System(
        drone_ip="192.168.43.42",
        drone_port=2390,
        local_port=2391,
        camera_url="http://192.168.43.43"
    )
    system.start()

    try:
        while True:
            time.sleep(1) 
    except KeyboardInterrupt:
        system.stop()

    print("Red positions detected:")
    for pos in system.red_positions:
        print(f"x={pos.x:.2f}, y={pos.y:.2f}, z={pos.z:.2f}")

if __name__ == "__main__":
    main()
