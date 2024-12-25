import cv2
import numpy as np
from movement.Centralization_class import Centralization
from movement.Control_class import Control
from ultralytics import YOLO

# Define the RTSP URL
rtsp_url = "rtsp://192.168.1.105:8080/h264_ulaw.sdp"

# Set the desired resolution
width = 1280
height = 720

# GStreamer pipeline optimized for zero latency
gst_pipeline = (
    f"rtspsrc location={rtsp_url} latency=0 ! "
    "rtph264depay ! "
    "h264parse ! "
    "avdec_h264 ! "  # Use NVIDIA hardware decoder
    "videoconvert ! "
    f"videoscale ! video/x-raw,width={width},height={height} ! "
    "appsink drop=true max-buffers=1 sync=false"
)

# Open the video stream
cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
centralization = Centralization(xOffset=0)
control = Control()
model = YOLO("yolov8n.pt")

if not cap.isOpened():
    print("Error: Unable to open the RTSP stream.")
    exit()

print("RTSP stream is open. Press 'q' to quit.")

# Process and display frames
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Unable to read frame from stream.")
        break

    result = model.track(
        frame,
        iou=0.1,
        conf=0.4,
        persist=True,
        verbose=False,
        tracker="botsort.yaml",
        classes=[0],
    )

    yaw, y = centralization.centralize(result, frame)
    # yaw = 0
    # y = 0

    control.post_speeds(y, yaw)

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
