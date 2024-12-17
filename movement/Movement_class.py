import time
import rospy
from std_msgs.msg import Float32 , Float32MultiArray, Int16MultiArray, String
from  scripts.Control_class import Control

class Movement(Control):
    def __init__(self):
        super().__init__()
        rospy.init_node("Moves")
        rospy.Rate(5)


    def move_byTime(self, move :list , motion_time:int , verbose = False):
        self.set_hamada(move)
        time.sleep(motion_time)
        self.stop_AUV(move)