import cv2
import threading
from queue import Empty

class CameraPreviewWindow:
    def __init__(self, frame_queue, drone):
        self.frame_queue = frame_queue   
        self.drone = drone
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        print("[Preview] Started preview window.")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join()
        cv2.destroyAllWindows()
        print("[Preview] Stopped preview window.")

    def _loop(self):
        while self._running:
            try:
                frame_with_pos = self.frame_queue.get(timeout=0.05)
            except Empty:
                continue

            frame = frame_with_pos.frame
            pos = frame_with_pos.position

            txt = f"x:{pos.x:.2f} y:{pos.y:.2f} z:{pos.z:.2f} | roll:{pos.roll:.1f} pitch:{pos.pitch:.1f} yaw:{pos.yaw:.1f}"

            cv2.putText(frame, txt, (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

            cv2.imshow("Drone Camera Live", frame)

            if cv2.waitKey(1) & 0xFF == 27:
                self.stop()
                break
