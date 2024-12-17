import cv2
import numpy as np
import matplotlib.pyplot as plt

def get_avg_rgb(frame, channel_select=0):
  separate_channel = frame[:, frame.shape[1]//2-20:frame.shape[1]//2+20, 2-channel_select]

  return np.mean(separate_channel)

# function to plot the average RGB values of the frame as time progresses
def detect_base(frame):
  # get the average RGB values of the frame
  avg_red = get_avg_rgb(frame, channel_select=0)
  avg_green = get_avg_rgb(frame, channel_select=1)
  avg_blue = get_avg_rgb(frame, channel_select=2)

  plt.plot(avg_red, label='Red')
  plt.plot(avg_green, label='Green')
  plt.plot(avg_blue, label='Blue')
  plt.legend()
  plt.show()
  plt.pause(0.001)
  plt.clf()

cap = cv2.VideoCapture('videos/vlc-record-2024-09-22-14h51m06s-image_raw_color-.avi')
while cap.isOpened():
  ret, frame = cap.read()
  if ret:
    cv2.imshow('frame', frame)
    detect_base(frame)
  else:
    break



