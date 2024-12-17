import cv2
import os

path = 'videos/vlc-record-2024-10-01-12h38m27s-_action=stream-.avi'
final_num = 985

cap = cv2.VideoCapture(path)

os.makedirs('./split_frames', exist_ok=True)

i=(final_num+1)*10
while cap.isOpened():
    ret, frame = cap.read()
    if i % 10 == 0:
      cv2.imwrite(f'./split_frames/frame_{int(i/10)}.jpg', frame)
    i += 1