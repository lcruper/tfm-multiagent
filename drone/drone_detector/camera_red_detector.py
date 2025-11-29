import cv2
import numpy as np
import requests
from ultralytics import YOLO
import threading
import time
from queue import Empty, Queue, Full
from structures import FrameWithPosition

class CameraRedDetector:
    IMG_SIZE = 256
    CONF_THRESH = 0.35
    IOU_THRESH = 0.45
    RED_RATIO_THRESH = 0.3 
    MIN_BOX_AREA = 100
    QUEUE_SIZE = 100

    def __init__(self, drone, camera_url, callback):
        self.drone = drone
        self.camera_url = camera_url
        self.stream_url = f"{camera_url}:81/stream"
        self.flash_url = f"{camera_url}/control"
        self.callback = callback
    
        self._capture_thread = None
        self._process_thread = None
        self._running = False

        self._queue = Queue(maxsize=self.QUEUE_SIZE)

        self.model = YOLO("yolov8n.pt")

    def start(self):
        if self._running:
            print("[CameraRedDetector] Already running.")
            return
        
        self._running = True
        self._capture_thread = threading.Thread(target=self._capture, daemon=True)
        self._process_thread = threading.Thread(target=self._process, daemon=True)
        self._capture_thread.start()
        self._process_thread.start()
        print("[CameraRedDetector] Started capture + processing threads.")

    def stop(self):
        self._running = False

        if self._capture_thread:
            self._capture_thread.join()
            self._capture_thread = None

        if self._process_thread:
            self._process_thread.join()
            self._process_thread = None

        print("[CameraRedDetector] Stopped.")

    def _turn_on_flash(self):
        try:
            requests.get(self.flash_url, params={"var": "led_intensity", "val": 255}, timeout=0.1)
        except:
            pass

    def _turn_off_flash(self):
        try:
            requests.get(self.flash_url, params={"var": "led_intensity", "val": 0}, timeout=0.1)
        except:
            pass

    def _capture(self):
        cap = cv2.VideoCapture(self.stream_url)
        if not cap.isOpened():
            print(f"[CameraRedDetector] Cannot open stream: {self.stream_url}")
            self._running = False
            return

        print("[CameraRedDetector] Stream opened. Capturing frames...")
        while self._running:
            ret, frame = cap.read()
            if not ret:
                print("[CameraRedDetector] Empty frame — retrying...")
                time.sleep(0.05)
                continue

            pos = self.drone.get_position()
            try:
                self._queue.put(FrameWithPosition(frame, pos), timeout=0.01)
            except Full:
                try:
                    self._queue.get_nowait()
                except Empty:
                    pass
                self._queue.put_nowait(FrameWithPosition(frame, pos))

        cap.release()

    def _process(self):
        while self._running:
            try:
                fwp = self._queue.get(timeout=0.1)
            except Empty:
                continue

            frame = fwp.frame
            pos = fwp.position   

            try:
                results = self.model.predict(frame, device="cpu", imgsz=self.IMG_SIZE,
                                            conf=self.CONF_THRESH, iou=self.IOU_THRESH,
                                            half=False, verbose=False)
            except Exception as e:
                print(f"[CameraRedDetector] YOLO error: {e}")
                continue

            dets = results[0].boxes if len(results) else []

            red_detected = False
            for box in dets:
                xyxy = box.xyxy.cpu().numpy().astype(int)[0] if hasattr(box.xyxy, "cpu") else np.array(box.xyxy).astype(int)[0]
                x1, y1, x2, y2 = xyxy
                aw, ah = x2 - x1, y2 - y1
                if aw*ah < self.MIN_BOX_AREA:
                    continue

                roi = frame[y1:y2, x1:x2]
                if roi.size == 0:
                    continue

                hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                mask1 = cv2.inRange(hsv, np.array([0, 80, 50]), np.array([10, 255, 255]))
                mask2 = cv2.inRange(hsv, np.array([160, 80, 50]), np.array([180, 255, 255]))
                mask = cv2.bitwise_or(mask1, mask2)
                red_ratio = cv2.countNonZero(mask) / (roi.shape[0]*roi.shape[1]+1e-6)

                if red_ratio >= self.RED_RATIO_THRESH:
                    self.callback(pos) 
                    red_detected = True
                    break

            if red_detected:
                self._turn_on_flash()
            else:
                self._turn_off_flash()
