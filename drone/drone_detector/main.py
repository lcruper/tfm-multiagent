from system import System
import time

def main():
    system = System(
        drone_ip="192.168.43.42",
        drone_port=2390,
        local_port=2391,
        camera_url="http://192.168.1.137"
    )
    system.start()

    try:
        while True:
            time.sleep(1) 
    except KeyboardInterrupt:
        system.stop()

if __name__ == "__main__":
    main()
