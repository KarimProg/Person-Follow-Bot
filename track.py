import cv2
from ultralytics import YOLO

model = YOLO('./runs/detect/train3/weights/best.pt')
# cap = cv2.VideoCapture("http://192.168.121.197:8080/video")

# while cap.isOpened():
#     ret, frame = cap.read()
#     if ret:
#         model.track(frame, show=True)
#         # cv2.imshow('stream', frame)

#     if cv2.waitKey(1) & 0xFF == ord("q"):
#         break

frame = cv2.imread("./train/images/1202_jpg.rf.9d539533f093c85cb423d616acc591d2.jpg")
results = model.track(frame, show=True)  # Load the image into the model and display the results

# Process the results (e.g., save the output image)
# Example: Save the processed frame
cv2.imwrite("./output/processed_image.jpg", frame)

# Keep the image displayed until a key is pressed
cv2.waitKey(0)

# cap.release()
cv2.destroyAllWindows()

