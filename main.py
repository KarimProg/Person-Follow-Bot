import cv2
import numpy as np
from scripts.Movement_class import Movement
from scripts.Centralization_class import Centralization
from scripts.PID import PID_class
from ultralytics import YOLO
import time
import subprocess


# YOLOv8 model path
MODEL_PATH = 'models/bestl.pt'

# Video or stream Path
VIDEO_PATH = 'http://192.168.1.9:8080/stream?topic=/zed_nodelet/right_raw/image_raw_color'

# Initialize control, movement, and PID objects
mov = Movement()
pid_x = PID_class(190, 25, 35)

pid_x_constants=[190, 25, 35]

if __name__ == "__main__":
    model = YOLO(MODEL_PATH)
    # print(model_zed.names)

    centralize = Centralization(VIDEO_PATH_ZED=VIDEO_PATH, pid_x=pid_x, mov=mov, model=model, threshold=0.1, ros_rate=3)

    mov.set_hamada([0,0,0,0,0,0])
    input("Start? ")

    # centralize.centralizeXY(pid_x_constants_gates, pid_y_constants_gates, forwardSpeed=0, exitOn='centralize', isCentralizeY=True)
    centralize.centralizeXY(pid_x_constants, forwardSpeed=0, isCentralizeX=True, offsetX=0.08)