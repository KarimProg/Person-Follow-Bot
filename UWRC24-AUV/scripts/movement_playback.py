#!/usr/bin/env python3

import rospy
from std_msgs.msg import Int16MultiArray
import time

class MovementPlayback:
    def __init__(self):
        # Initialize ROS node
        rospy.init_node('movement_playback', anonymous=True)

        # Publisher for the 'hamada' topic
        self.pub = rospy.Publisher('hamada', Int16MultiArray, queue_size=100)

        # File to read movements
        self.input_file = 'movements.txt'

    def playback_movements(self):
        # Read movements from the file
        with open(self.input_file, 'r') as f:
            movements = f.readlines()

        # Reverse the list to simulate stack behavior (LIFO)
        movements.reverse()
        while movements[0] == '\n':
            movements.remove('\n')
        # print(movements)


        # last_movement_time_difference = float((movements[0].strip().replace('\n','').split(' , '))[0])
        
        # Start playback

        for line in movements:

            last_time = time.time()

            if line == '\n':
                continue

            # time_diff = abs((float((line.strip().replace('\n','').split(' , '))[0]) - last_movement_time_difference)*-1)
            time_diff = (float((line.strip().replace('\n','').split(' , '))[0]))
            movement_data = (line.strip().replace('\n','').split(' , '))[1]


            # Create Int16MultiArray message
            movement_msg = Int16MultiArray()
            
            # Process the movement data
            movement_values = list(map(int, movement_data.strip('()').split(', ')))
            # print(movement_values)
            # Multiply each value by -1
            movement_values = [-1 * value for value in movement_values]
            movement_values[1]=int(movement_values[1]*1.2)
            movement_msg.data = movement_values
            self.pub.publish(movement_msg)
            print(f"Published movement: {movement_msg.data} at {time_diff} seconds.")
            # Wait until the appropriate time to publish
            while time.time() - last_time <= time_diff:
                time.sleep(0.01)  # Sleep to avoid busy-waiting

    def run(self):
        print("Starting playback...")
        self.playback_movements()
        print("Playback finished.")

if __name__ == '__main__':
    try:
        player = MovementPlayback()
        player.run()
    except rospy.ROSInterruptException:
        pass