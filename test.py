import cv2
import os

print(cv2.__file__)


# Ensure GStreamer is in the PATH
os.environ["PATH"] += os.pathsep + "D:\\gstreamer\\1.0\\msvc_x86_64\\bin"

# Define a simplified GStreamer pipeline for RTSP streaming
gstreamer_pipeline = (
    "rtspsrc location=rtsp://192.168.165.92:8080/h264_ulaw.sdp latency=100 ! "
    "rtph264depay ! h264parse ! avdec_h264 ! "
    "videoconvert ! video/x-raw, format=BGR ! appsink"
)


# Open the video capture with the GStreamer pipeline
cap = cv2.VideoCapture(gstreamer_pipeline, cv2.CAP_GSTREAMER)

if not cap.isOpened():
    print("Error: Unable to open the camera")
    print(f"GStreamer pipeline: {gstreamer_pipeline}")
else:
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            # Process the frame (e.g., display or save)
            cv2.imshow('RTSP Stream', frame)

            # Press 'q' to exit the loop
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        else:
            print("Error: Unable to read frame")

cap.release()
cv2.destroyAllWindows()
