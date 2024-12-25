

class Control():
    def __init__(self):
        self.inertia_delay = 0.3
        
        self.yaw_pid_param    = {"kp": 7.5   , "ki": 0.2 , "kd": 4 }

        # self.hamada_topic = rospy.Publisher('move', Int16MultiArray, queue_size=100)

    def set_hamada(self, move , verbose = False):
        for i in move:
            i = int(i)
        print(f"Moving with: {move}")
        # self.hamada_topic.publish(Int16MultiArray(data=move))

