from ultralytics import YOLO
import cv2
import time
model = YOLO('models/bestn.pt')

path = 'http://192.168.1.9:8080/stream?topic=/zed_nodelet/right_raw/image_raw_color'

cap = cv2.VideoCapture(path)

while cap.isOpened():
  ret, frame = cap.read()
  if not ret:
    continue
  start=time.time()
  model.track(source=frame, show=False, iou=0.5,conf=0.5, save = False ,verbose = False, device=0, classes=[3])    
  end=time.time()
  print(1/(end-start))
  if cv2.waitKey(1) & 0xFF == ord("q"):
            break

cap.release()
cv2.destroyAllWindows()
  # print(results[0].boxes.xyxy.cpu().numpy())

  # for result in results:
  #   print(result.boxes)
