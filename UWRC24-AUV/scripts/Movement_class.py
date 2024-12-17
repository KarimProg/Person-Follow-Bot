import time
import rospy
from std_msgs.msg import Float32 , Float32MultiArray, Int16MultiArray, String
from  scripts.Control_class import Control

class Movement(Control):
    def __init__(self):
        super().__init__()
        rospy.init_node("AUV_Moves")
        rospy.Rate(5)

    def auv_init(self, const_vertical=350, const_horizontal=350):
        constraint_arr = [const_horizontal, const_vertical]
        self.set_speed_constrains(constraint_arr)

    def move_byTime(self, move :list , motion_time:int , verbose = False):
        '''
        Move ROV with a specific speed for a specific time

        Parameters:
        - move : list
            - list of 6 integers representing the desired motion 
        - motion_time : int
            - time in seconds to keep the motion
        - verbose : bool
            - print loginfo if True
        '''        
        
        self.set_hamada(move)
        time.sleep(motion_time)
        self.stop_AUV(move)