#!/usr/bin/env python3

import rospy
from std_msgs.msg import Int16MultiArray
from threading import Thread, Event
import sys
import select
import time

class MovementRecorder:
    def __init__(self):
        # Initialize ROS node
        rospy.init_node('movement_recorder', anonymous=True)

        # Publisher and subscriber for the 'hamada' topic
        # self.pub = rospy.Publisher('hamada', Int16MultiArray, queue_size=10)
        self.sub = rospy.Subscriber('hamada', Int16MultiArray, self.movement_callback)

        # File to save movements
        self.output_file = 'movements.txt'
        self.last_data = (0,0,0,0,0,0)
        # Timestamps for recording
        self.initial_timestamp = None

        # To handle keyboard input
        # self.key_thread = Thread(target=self.wait_for_keypress)
        # self.key_thread.daemon = True
        # self.key_thread.start()

    # def wait_for_keypress(self):
    #     while not rospy.is_shutdown():
    #         # Wait for 's' key press to change states
    #         if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
    #             key = sys.stdin.read(1)
    #             if key == 's':
    #                 if self.initial_timestamp is None:
    #                     print("Starting movement recording...")
    #                     self.initial_timestamp = rospy.Time.now()
    #                 else:
    #                     print("Recording finished.")
    #                     self.unsubscribe_from_hamada()
    #                     break

    def movement_callback(self, data):
            current_time = rospy.Time.now()
            time_diff = (current_time - self.initial_timestamp).to_sec()
            self.initial_timestamp = current_time
            # Save the movement and time difference to the file
            with open(self.output_file, 'a') as f:
                f.write(f"{time_diff} , {self.last_data}\n")
            
            self.last_data = data.data
            print(f"Recorded {self.last_data} at {time_diff} seconds.")

    def unsubscribe_from_hamada(self):
        """Unsubscribe from the hamada topic after recording is done."""
        print("Unsubscribing from hamada topic to stop recording.")
        self.sub.unregister()

    def run(self):
        # Wait for user to press 's' to start recording
        while not rospy.is_shutdown():
            rospy.spin () 

if __name__ == '__main__':
    try:
        recorder = MovementRecorder()
        with open(recorder.output_file, 'w') as f:
                f.write("")
        recorder.initial_timestamp = rospy.Time.now()
        recorder.run()
    except rospy.ROSInterruptException:
        pass