import cv2
from ultralytics import YOLO
import requests
import numpy as np
import time


def format_elapsed(elapsed):
    mins = int((elapsed % 3600) // 60)
    secs = int(elapsed % 60)
    return f"{mins:02d}:{secs:02d}"

def turn_on_flash(intensity=255):
    try:
        requests.get(ESP32_URL, params={"var": "led_intensity", "val": intensity}, timeout=0.1)
    except:
        pass

def turn_off_flash():
    try:
        requests.get(ESP32_URL, params={"var": "led_intensity", "val": 0}, timeout=0.1)
    except:
        pass


STREAM_URL = "http://192.168.1.40:81/stream"
ESP32_URL = "http://192.168.1.40/control"

IMG_SIZE = 256
CONF_THRESH = 0.35
IOU_THRESH = 0.45

RED_RATIO_THRESH = 0.30
MIN_BOX_AREA = 100

model = YOLO("yolov8n.pt")      

device = "cpu"  

cap = cv2.VideoCapture(STREAM_URL)
if not cap.isOpened():
    print("Stream cannot be opened:", STREAM_URL)
    exit(1)

print("Stream opened. Running detector... (press 'q' to quit)")
start_time = time.time() 
fps_avg = 0.0
cnt = 0
t0 = start_time

while True:
    ret, frame = cap.read()
    if not ret:
        print("Empty frame — retrying...")
        time.sleep(0.2)
        continue

    elapsed = time.time() - start_time
    frame_timestamp = format_elapsed(elapsed)

    results = model.predict(frame, device=device, imgsz=IMG_SIZE, conf=CONF_THRESH, iou=IOU_THRESH, half=False, verbose=False)
    dets = results[0].boxes if len(results) else []
    h, w = frame.shape[:2]

    red_detected = False
    detections = []
    for box in dets:
        xyxy = box.xyxy.cpu().numpy().astype(int)[0] if hasattr(box.xyxy, "cpu") else np.array(box.xyxy).astype(int)[0]
        x1, y1, x2, y2 = xyxy
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w-1, x2), min(h-1, y2)
        aw = x2 - x1
        ah = y2 - y1
        if aw * ah < MIN_BOX_AREA:
            continue

        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            continue

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        lower1 = np.array([0, 80, 50])
        upper1 = np.array([10, 255, 255])
        lower2 = np.array([160, 80, 50])
        upper2 = np.array([180, 255, 255])
        mask1 = cv2.inRange(hsv, lower1, upper1)
        mask2 = cv2.inRange(hsv, lower2, upper2)
        mask = cv2.bitwise_or(mask1, mask2)
        red_pixels = cv2.countNonZero(mask)
        total_pixels = roi.shape[0] * roi.shape[1]
        red_ratio = red_pixels / (total_pixels + 1e-6)

        if red_ratio >= RED_RATIO_THRESH:
            red_detected = True
            detections.append((x1, y1, x2, y2, red_ratio))
            print(f"[{cnt}][{frame_timestamp}] Red detected at box ({x1},{y1},{x2},{y2}) with intensity {red_ratio:.2f}")

    if red_detected:
        turn_on_flash()
    else:
        turn_off_flash()

    for (x1, y1, x2, y2, r) in detections:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,0,255), 2)
        cv2.putText(frame, f"Red:{r:.2f}", (x1, max(10, y1-5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1)

    cv2.putText(frame, f"[{cnt}] {frame_timestamp}", (218, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)

    cnt += 1
    if cnt % 10 == 0:
        t1 = time.time()
        fps_avg = 10 / (t1 - t0)
        t0 = t1
    cv2.putText(frame, f"FPS:{fps_avg:.1f}", (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

    cv2.imshow("Red detector", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()