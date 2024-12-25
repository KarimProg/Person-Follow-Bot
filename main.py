import cv2
from movement.Centralization_class import Centralization
from movement.Control_class import Control
from ultralytics import YOLO
from movement.PID import PID_class
import time

# Define the RTSP URL
rtsp_url = "rtsp://10.42.0.205:8080/h264_ulaw.sdp"

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
pid = PID_class(70, 1, 20)
centralization = Centralization(pid=pid, xOffset=0)
control = Control()
model = YOLO("models/yolov8m.pt")
state = "stop"
if not cap.isOpened():
    print("Error: Unable to open the RTSP stream.")
    # exit()

print("RTSP stream is open. Press 'q' to quit.")


last_post_time = time.time()
last_read_file_time = time.time()
# Process and display frames
while True:
    ret, frame = cap.read()
    ret  = True
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

    current_time = time.time()
    if (current_time - last_read_file_time) >= 0.5:
        with open("command.txt", "r") as f:
            command = f.read()
            if command == "follow":
                state = "follow"
            elif command == "stop":
                state = "stop"
        last_read_file_time = current_time

    if state == "stop":
        y = 0
        yaw = 0

    # Get the current time
    # current_time = time.time()
    # Check if 50 milliseconds have passed
    # if (current_time - last_post_time) >= 0.5:
        # Post the speeds
    # print(f"y: {y}, yaw: {yaw}")
    # y=0
    control.post_speeds(-y, -yaw)
        
        # Update the last post time
        # last_post_time = current_time

    # Exit on pressing 'q'
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
