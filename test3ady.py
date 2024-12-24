import cv2

# Replace with your RTSP stream URL
rtsp_url = "rtsp://192.168.115.237:8080/h264_ulaw.sdp"

# Open the RTSP stream
video_capture = cv2.VideoCapture(rtsp_url)

# Set buffer size to reduce latency
video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

# If available, set FPS and resolution to match the stream
video_capture.set(cv2.CAP_PROP_FPS, 30)  # Adjust to your stream's FPS
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Match stream resolution
video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

if not video_capture.isOpened():
    print("Error: Unable to open RTSP stream.")
    exit()

while True:
    
    success, frame = video_capture.read()
    if not success:
        print("Failed to retrieve frame. Exiting.")
        break
    
    # Display the frame
    cv2.imshow("RTSP Stream", frame)

    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close display window
video_capture.release()
cv2.destroyAllWindows()