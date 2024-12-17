import cv2
import numpy as np
from scripts.Movement_class import Movement
from scripts.Centralization_class import Centralization
from scripts.PID import PID_class
from ultralytics import YOLO
import time
import subprocess


# YOLOv8 model path
MODEL_PATH_ZED = 'models/bestl.pt'
MODEL_PATH_LF = 'models/bestn_lf_v2.pt'
MOV_RECORDER_PATH = 'scripts/movement_recorder.py'
MOV_PLAYBACK_PATH = 'scripts/movement_playback.py'

# Video or stream Path
VIDEO_PATH_ZED = 'http://192.168.1.9:8080/stream?topic=/zed_nodelet/right_raw/image_raw_color'
VIDEO_PATH_LF = 'http://192.168.1.9:10002/?action=stream'

SOLENOID_PIN = 4

# Initialize control, movement, and PID objects
mov = Movement()
# FOR STAND
pid_x = PID_class(190, 25, 35)
pid_y = PID_class(150, 20, 28)
pid_depth = PID_class(3, 0, 0)
# FOR OBJECT
# pid_x = PID_class(110, 50, 60)
# pid_y = PID_class(70, 20, 50)
# pid_depth = PID_class(3, 0, 0)

pid_x_constants_gates=[190, 25, 35]
pid_y_constants_gates=[20, 0, 10]
pid_x_constants_object=[110, 50, 60]
pid_y_constants_object=[70, 20, 50]

right=1
left=-1

if __name__ == "__main__":
    model_zed = YOLO(MODEL_PATH_ZED)
    model_lf = YOLO(MODEL_PATH_LF)
    # print(model_zed.names)

    centralize = Centralization(VIDEO_PATH_ZED=VIDEO_PATH_ZED, VIDEO_PATH_LF=VIDEO_PATH_LF, pid_x=pid_x, pid_y=pid_y, pid_depth=pid_depth, mov=mov, model=model_zed, model_lf=model_lf, threshold=0.1, ros_rate=3)


    input("Start? ")

    # centralize.mapGates(20)
    mov.set_servo_camera(1600)
    mov.enable_yaw_pid()
    mov.set_hamada([0,0,-140,0,0,0])
    time.sleep(10)
    mov.set_hamada([0,0,0,0,0,0])
    mov.set_reference_press()
    mov.set_reference_yaw()


    time.sleep(1)
    # Centralize on first gate while not going forward
    mov.enable_height_pid()
    mov.set_setHeight_sp(mov.reference_press-600,verbose=True)
    time.sleep(5)

    # centralize.centralizeXY(pid_x_constants_gates, pid_y_constants_gates, forwardSpeed=0, exitOn='centralize', isCentralizeY=True)
    centralize.centralizeXY(pid_x_constants_gates, pid_y_constants_gates, forwardSpeed=0, exitOn='centralize', isCentralizeX=True, offsetX=0.08)
    print('first static centralization done')
    # mov.set_setYaw_sp(mov.reference_yaw,verbose=True)

    time.sleep(0.3)
    process1 = subprocess.Popen(["python3", MOV_RECORDER_PATH])  # Run external script
    centralize.centralizeXY(pid_x_constants_gates, pid_y_constants_gates, forwardSpeed=180, exitOn='passGate2', isCentralizeX=False)
    print('passed first gate')
    time.sleep(0.3)
    # centralize.centralizeXY(pid_x_constants_gates, pid_y_constants_gates,centralizeOn=4, forwardSpeed=0, exitOn='centralize', isCentralizeX=True)
    # print('second centralization done')
    # time.sleep(0.3)
    # centralize.centralizeXY(pid_x_constants_object, pid_y_constants_object, forwardSpeed=150, exitOn='passGate2', isCentralizeX=False)


    # # Trying to find the gate change this value if you see where is the second gate it is either [right , left]
    direction = right
    # mov.set_setYaw_sp(mov.reference_yaw,verbose=True)
    centralize.Find(direction,id=4)
    # centralize.StandCentralizing()
    mov.set_servo_camera(1700)
    centralize.pid_x.set_constants(150, 25, 35)
    centralize.centralizeXY(pid_x_constants_gates, pid_y_constants_gates, forwardSpeed=0, exitOn='centralize', isCentralizeX=True, centralizeOn=4, offsetX=-0.08)
    centralize.centralizeXY(pid_x_constants_gates, pid_y_constants_gates, forwardSpeed=150, exitOn='passGate2', isCentralizeX=True, centralizeOn=4, offsetX=-0.04)

    mov.set_setHeight_sp(mov.reference_press-300,verbose=True)
    mov.trigger_solenoid(SOLENOID_PIN)
    mov.move_byTime([0,200,0,0,0,0], 10, False)
    mov.trigger_solenoid(SOLENOID_PIN)

    time.sleep(0.3)
    
    process1.terminate()
    process2 = subprocess.Popen(["python3", MOV_PLAYBACK_PATH])  # Run external script
    process2.wait()

    mov.set_hamada([0,0,0,0,0,0])
    mov.rotate_with_angle(180)
    mov.move_byTime([0,200,0,0,0,0], 10, False)
    mov.trigger_solenoid(SOLENOID_PIN)
    print("Khalasnaaaaa")

    # mov.move_byTime([0,0,200,0,0,0], 3, False)

    # # centralize on second gate
    # centralize.centralizeXY(pid_x_constants_gates, pid_y_constants_gates, forwardSpeed=0, exitOn='centralize', isCentralizeY=True)
    # centralize.centralizeXY(pid_x_constants_gates, pid_y_constants_gates, forwardSpeed=0, exitOn='centralize', isCentralizeX=True)
    # print('second static centralization done')
    # time.sleep(0.3)

    # centralize.centralizeXY(pid_x_constants_gates, pid_y_constants_gates, forwardSpeed=150, exitOn='passGate2')
    # print('passed second gate')
    # time.sleep(0.3)

    # '''
    # dol ba3den le7ad ma nezbot el fo2
    # '''

    # centralize.centralizeXY(forwardSpeed=0, exitOn='centralize', isCentralizeY=True)
    # centralize.centralizeXY(forwardSpeed=0, exitOn='centralize', isCentralizeX=True)
    # print('second static centralization done')
    # time.sleep(0.3)

    # centralize.centralizeXY(forwardSpeed=150, exitOn='passGate')
    # print('passed second gate')
    # time.sleep(0.3)

    # # Start centralizing on object
    # centralize.centralizeXY(forwardSpeed=0, exitOn='centralize', centralizeOn=5)
    # print('second static centralization done')
    # # time.sleep(0.3)

    # # Move forward till bounding box area is larger than a certain threshold
    # centralize.centralizeXY(forwardSpeed=50, exitOn='area_size', centralizeOn=5)
    # print('second static centralization done')
    # time.sleep(0.3)

    # # this is where we have to detect and move to grab

    # if centralize.StandCe ntralizing(id=4) :
    # if centralize.ObjectGrabbingWithDownwardGripper(pid_x_constants_object, pid_y_constants_object, SOLENOID_PIN, id=5, zedAngle=1500, centeredX=False, centeredY=False, grabbingZedAngle=1400) :
    #     print("Object Grabbed and returning back")
    # else :
    #     # plan failed let's get back
    #     print("Grabbing failed")
    #     # Rotate 360 180 degrees
    #     mov.rotate_with_angle(180)

    # print("Nenafez ba2y elhaga ba2a")
    # # Centralize on first gate in the return trip
    # centralize.centralizeXY(pid_x_constants_gates, pid_y_constants_gates, forwardSpeed=-50, exitOn='centralize')
    # print('static centralization done')
    # time.sleep(0.3)

    # # # Move forward till you see less than 2 gates, then move forward {passTimeDelay} seconds
    # centralize.centralizeXY(pid_x_constants_gates, pid_y_constants_gates, forwardSpeed=150, exitOn='passGate')
    # print('passed first gate')
    # time.sleep(0.3)

    # #  we can move forward for 5 seconds until we hit the wall then release the object
    # mov.move_byTime([0, 200, 0, 0, 0, 0], 5, True)
    # print('opening gripper')
    # mov.trigger_solenoid(SOLENOID_PIN)
    # print('gripper opened')
    
    ## another approach
    ## after making sure that the second gate is passed, start centralizing on the middle bucket
    ## first choose a bucket based on the class id
    # if(centralize.centralizeBucket(id)):
    #     if(centralize.insertBucket):
    #         print('opening gripper')
    #         mov.trigger_solenoid(SOLENOID_PIN)
    #         print('gripper opened')
    #         # go up again from th middle bucket
    #         mov.move_byTime([0, 0, 200, 0, 0, 0], 2, True)

    # centralize yourself on the middle bucket and move forward till you stop seeing the bucket for 10 frames 
    # then go down for a couple of seconds and open the gripper