import cv2
import requests
import numpy as np
from ultralytics import YOLO

ESP32_URL = "http://192.168.1.39/capture"  
model = YOLO("yolov8n.pt")  

while True:
    try:
        # Captura frame
        r = requests.get(ESP32_URL, timeout=3)
        frame = cv2.imdecode(np.frombuffer(r.content, np.uint8), cv2.IMREAD_COLOR)

        # Predicción YOLO
        results = model.predict(frame, imgsz=320)

        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            crop = frame[y1:y2, x1:x2]

            # Detectar rojo solo en este bbox
            hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
            lower_red1 = np.array([0, 70, 50])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 70, 50])
            upper_red2 = np.array([180, 255, 255])
            mask = cv2.inRange(hsv, lower_red1, upper_red1) | cv2.inRange(hsv, lower_red2, upper_red2)

            if cv2.countNonZero(mask) / (crop.shape[0] * crop.shape[1]) > 0.2:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,0,255), 2)
                cv2.putText(frame, "Red Object", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)

        # Mostrar frame completo
        cv2.imshow("Red Object Detection", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC para salir
            break

    except Exception as e:
        print("Error:", e)
