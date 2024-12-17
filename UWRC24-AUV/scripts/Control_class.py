import time
import rospy
from std_msgs.msg import Float32 , Int16, Float32MultiArray, Int16MultiArray, String, Byte
import time
import os


class Control():
    def __init__(self):
        self.inertia_delay = 0.3

        self.prev_press = 0
        self.prev_yaw   = 0
        self.curr_yaw   = 0
        self.curr_press  = 0
        self.reference_press = 0
        self.reference_yaw = 0
        # self.auv_pres_setpoint = 97000
        

        self.height_pid_param = {"kp": 1, "ki": 0.15, "kd": 2}
        self.yaw_pid_param    = {"kp": 7.5   , "ki": 0.2 , "kd": 4 }

        self.hamada_topic = rospy.Publisher('hamada', Int16MultiArray, queue_size=100)
        self.speeds_constraints_topic = rospy.Publisher('speeds', Int16MultiArray, queue_size=100)
        self.solenoids_topic = rospy.Publisher('solenoids', Byte, queue_size=100)
        self.servo_topic = rospy.Publisher('servo_camera', Int16, queue_size=100)


        self.height_pid       = rospy.Publisher('height_pid', Float32MultiArray, queue_size=100)
        self.height_sp        = rospy.Publisher('height_sp', Float32, queue_size=100)
        self.yaw_pid          = rospy.Publisher('yaw_pid', Float32MultiArray, queue_size=100)
        self.yaw_sp           = rospy.Publisher('yaw_sp', Float32, queue_size=100)
        # self.pressure_setpoint  =rospy.Publisher('pressure_setpoint',Float32,queue_size=100)
        self.pressure_sub = rospy.Subscriber('pressure', Float32, self.press_calc)
        self.yaw_sub      = rospy.Subscriber('yaw', Float32, self.yaw_calc)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        os.makedirs('logs', exist_ok=True)
        self.filename = f"logs/logs_{timestamp}.txt"


    def set_hamada(self, move , verbose = False):
        for i in move:
            i = int(i)
        print(f"Moving with: {move}")
        self.hamada_topic.publish(Int16MultiArray(data=move))

        with open(self.filename, 'a') as file:
            file.write(str(move)+'\n')
        if verbose:
            rospy.loginfo("Published to hamada" + str(move))

    def get_curr_pressure(self):
        return self.curr_press

    
    def set_setHeight_sp(self , val, verbose = False):
        self.height_sp.publish(Float32(data=val))
        if verbose:
            rospy.loginfo("Published to height_sp " + str(val))
            
    def set_setYaw_sp(self , val, verbose = False):
        self.yaw_sp.publish(Float32(data=val))
        if verbose:
            rospy.loginfo("Published to yaw_sp " + str(val))

    def set_speed_constarints(self, constraints:list, verbose = False):
        self.speeds_constraints_topic.publish(Int16MultiArray(data=constraints))
        if verbose:
            rospy.loginfo(f"Set Speed Constrains to  {constraints} ")

    def trigger_solenoid(self, solenoid:int, verbose = False):
        self.solenoids_topic.publish(data=solenoid)
        if verbose:
            rospy.loginfo(f"Triggered Solenoid {solenoid}")

    def set_servo_camera(self, servo_angle:int, verbose = False):
        self.servo_topic.publish(data=servo_angle)
        if verbose:
            rospy.loginfo(f"Servo angle set to {servo_angle}")

    def stop_AUV(self, last_hamada:list , verbose = False):
        """
        Reverse the AUV motion to stop it immediately 
        """
        
        print(f"Stopping with: {last_hamada}")
        for i in range(0,len(last_hamada)):
            last_hamada[i] = int(last_hamada[i] * -1.2)

        self.set_hamada(last_hamada,verbose)
        time.sleep(self.inertia_delay)

        self.set_hamada([0,0,0,0,0,0],verbose)
        if verbose:
            rospy.loginfo("Stop AUV")

    def kill_AUV(self,verbose = False):
        self.set_speed_constarints([0,0],verbose)    
        if verbose:
            rospy.loginfo("Kill AUV")

    def press_calc(self, val):        
        self.curr_press = val.data  
        self.err_press = self.curr_press - self.prev_press
        self.prev_press = self.curr_press

    def rotate_with_angle(self, val):
        new_angle = self.curr_yaw + val
        self.yaw_sp.publish(new_angle)
        rospy.loginfo(f"Rotated with {val} degrees to {new_angle}")

    def yaw_calc(self, val):
        self.curr_yaw = val.data
        self.err_yaw = self.curr_yaw - self.prev_yaw
        self.prev_yaw = self.curr_yaw

    def disable_height_pid(self):
        rospy.loginfo("Disabled Height PID")
        time.sleep(0.25)
        self.height_pid.publish(Float32MultiArray(data=[0, 0, 0]))

    def disable_yaw_pid(self):
        rospy.loginfo("Disabled Yaw PID")
        time.sleep(0.25)
        self.yaw_pid.publish(Float32MultiArray(data=[0, 0, 0]))

    def enable_height_pid(self):
        rospy.loginfo(f"Enable Height PID kp:{self.height_pid_param['kp']}, ki:{self.height_pid_param['ki']}, kd:{self.height_pid_param['kd']}")
        time.sleep(0.25)
        self.height_pid.publish(Float32MultiArray(data=[self.height_pid_param['kp'],self.height_pid_param['ki'],self.height_pid_param['kd']]))

    def enable_yaw_pid(self):
        rospy.loginfo(f"Enable Yaw PID kp:{self.yaw_pid_param['kp']}, ki:{self.yaw_pid_param['ki']}, kd:{self.yaw_pid_param['kd']}")
        time.sleep(0.25)
        self.yaw_pid.publish(Float32MultiArray(data=[self.yaw_pid_param['kp'],self.yaw_pid_param['ki'],self.yaw_pid_param['kd']]))

    def set_reference_yaw(self):
        self.reference_yaw = self.curr_yaw
        rospy.loginfo(f"Set Reference Yaw to {self.reference_yaw}")
    
    def set_reference_press(self):
        self.reference_press = self.curr_press
        rospy.loginfo(f"Set Reference Pressure to {self.reference_press}")

    def release(self,last_reading,grippper_no):
        self.stop_AUV(last_reading,True)
        self.trigger_solenoid(grippper_no, True)
       


