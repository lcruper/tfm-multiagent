import cv2
import threading
from queue import Empty

class CameraPreviewWindow:
    def __init__(self, frame_queue):
        self.frame_queue = frame_queue   
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            print("[Preview] Already running.")
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

    def _draw_overlay(self, frame, pos):
        overlay = frame.copy()

        bar_height = 60
        cv2.rectangle(overlay, (0, 0), (frame.shape[1], bar_height), (0, 0, 0), -1)
        alpha = 0.45
        frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)

        line1 = f"x:{pos.x:.2f}  y:{pos.y:.2f}  z:{pos.z:.2f}"
        line2 = f"roll:{pos.roll:.1f}  pitch:{pos.pitch:.1f}  yaw:{pos.yaw:.1f}"

        def draw_text(text, y):
            cv2.putText(frame, text, (12, y+2), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (0,0,0), 3, cv2.LINE_AA)
            cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX,
                        0.7, (255,255,255), 2, cv2.LINE_AA)

        draw_text(line1, 25)
        draw_text(line2, 50)

        return frame

    def _loop(self):
        while self._running:
            try:
                fwp = self.frame_queue.get(timeout=0.05)
            except Empty:
                continue

            frame = fwp.frame
            pos = fwp.position

            frame_display = self._draw_overlay(frame.copy(), pos)

            cv2.imshow("Drone Camera Live", frame_display)

            if cv2.waitKey(1) & 0xFF == 27:
                self.stop()
                break
