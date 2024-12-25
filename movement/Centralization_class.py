import cv2
import movement.PID as PID

class Centralization:
    # Setting default values
    def __init__(self, pid, xOffset=0):
        self.idOfCentralizingObject = None
        self.framesCentralizingObjectDisappeared = 0

        # Get the frame dimensions
        self.frame_width = 1280
        self.frame_height = 720

        self.PID = pid
        # Set the setpoint
        self.PID.set_setpoint(self.frame_width // 2 + xOffset)

    def __get_largest_bounding_box(self, result):
        if not result or not result[0].boxes:
            return None, 0, None

        boxes = result[0].boxes.xywh.cpu().numpy()
        ids = result[0].boxes.id

        if ids is None:
            return None, 0, None

        ids = ids.int().cpu().tolist()

        largest_area = 0
        largestBox = None
        id = None

        index = 0
        for box in boxes:
            x_centre, y_centre, w1, h1 = box
            area = w1 * h1
            if area > largest_area:
                largest_area = area
                largestBox = box
                id = ids[index]
            index += 1

        return largestBox, largest_area, id

    def __get_centralizing_object(self, result, id):
        if not result or not result[0].boxes:
            return None

        boxes = result[0].boxes.xywh.cpu().numpy()
        ids = result[0].boxes.id

        if ids is None:
            return None

        ids = ids.int().cpu().tolist()

        index = 0
        for box in boxes:
            x_centre, y_centre, w1, h1 = box
            if ids[index] == id:
                return box
            index += 1

        return None

    def centralize(self, result, frame):
        # Get the bounding box
        if self.idOfCentralizingObject is None:
            box, area, self.idOfCentralizingObject = self.__get_largest_bounding_box(result)
        else:
            box = self.__get_centralizing_object(result, self.idOfCentralizingObject)
            if box is None:
                self.framesCentralizingObjectDisappeared += 1
                if self.framesCentralizingObjectDisappeared > 30:
                    self.idOfCentralizingObject = None
                    self.framesCentralizingObjectDisappeared = 0

        if box is None:
            cv2.imshow("RTSP Stream", frame)
            # Return default speeds when the object is not found
            return 0, 0
        x_centre, y_centre, w1, h1 = box
        bounding_box_center_x = x_centre
        bounding_box_center_y = y_centre

        # Draw the bounding box
        cv2.rectangle(
            frame,
            (int(x_centre - w1 / 2), int(y_centre - h1 / 2)),
            (int(x_centre + w1 / 2), int(y_centre + h1 / 2)),
            (0, 255, 0),
            2,
        )

        # Draw the bounding box center
        cv2.circle(
            frame,
            (int(bounding_box_center_x), int(bounding_box_center_y)),
            5,
            (0, 0, 255),
            -1,
        )

        # Draw vertical line in the middle of the frame
        cv2.line(frame, (self.frame_width // 2, 0), (self.frame_width // 2, self.frame_height), (0, 0, 0), 2)

        # Draw the arrow from the center of the bounding box to the setpoint
        cv2.arrowedLine(
            frame,
            (int(bounding_box_center_x), int(bounding_box_center_y)),
            (self.frame_width // 2, int(bounding_box_center_y)),
            (255, 0, 0),
            2,
        )

        # Draw the setpoint
        cv2.circle(
            frame,
            (self.frame_width // 2, self.frame_height // 2),
            5,
            (0, 0, 0),
            -1,
        )

        # show the frame
        cv2.imshow("RTSP Stream", frame)

        # Calculate the PID value
        pid_value = self.PID.calculate(bounding_box_center_x)

        # Normalize the PID value
        normalized_pid_value = pid_value / (self.frame_width // 2)

        return normalized_pid_value, 200  # 100 is the forward speed of the robot