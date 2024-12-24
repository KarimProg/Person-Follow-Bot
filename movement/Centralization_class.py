import cv2
import time
import numpy as np

"""
Ta2riban aham file, fih kol el path el 7anemshih wel main functions
"""

class Centralization:
    # Setting default values
    def __init__(
        self,
        VIDEO_PATH_ZED,
        pid_x,
        mov,
        model,
        threshold=0.1,
        ros_rate=3,
    ):
        self.center_x_frames = 0
        self.center_y_frames = 0
        self.hamada = [0, 0, 0, 0, 0, 0]
        self.last_hamada = [0, 0, 0, 0, 0, 0]
        self.threshold = threshold
        self.pid_x = pid_x
        self.mov = mov
        self.model = model
        self.video_src_zed = VIDEO_PATH_ZED
        self.cap_camera = cv2.VideoCapture(self.video_src_zed)
        self.awelMara = True
        
        # Set buffer size to reduce latency
        self.cap_camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # If available, set FPS and resolution to match the stream
        self.cap_camera.set(cv2.CAP_PROP_FPS, 30)  # Adjust to your stream's FPS
        self.cap_camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Match stream resolution
        self.cap_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self.finishedX = False
        self.finishedY = False
        self.no_detection = 0
        self.offsetX = 0
        self.offsetY = 0.05
        self.prev_time = time.time()
        self.ros_rate = ros_rate
        self.dontCentralize = False

    # Function to move ROV by publishing on hamada (core)
    def sendHamada(self, move):
        if time.time() - self.prev_time > 1 / self.ros_rate:
            self.prev_time = time.time()

            self.hamada = move
            if self.hamada != self.last_hamada:
                self.mov.set_hamada(self.hamada, verbose=False)
                self.last_hamada = self.hamada.copy()

    # Function that returns bounding boxes from YOLO (core)
    def extract_results(self, result,):
        boxes = result[0].boxes.xywh.cpu().numpy()
        largest_area = 0
        largestBox = None

        for box in boxes:
            x_centre, y_centre, w1, h1 = box
            area = w1 * h1
            if area > largest_area:
                largest_area = area
                largestBox = box

        return largestBox, largest_area

    # Needed to interact with x and y PIDs
    def adjustMove(self, axis: str, error):
        if axis.upper() == "X":
            # if abs(error) > self.threshold:
            pidVal = self.pid_x.calculate(error)
            self.hamada[0] = pidVal

        elif axis.upper() == "Y":
            # if abs(error) > self.threshold:
            pidVal = self.pid_y.calculate(error)
            self.hamada[2] = pidVal

    def minimize_error(self, axis: str, error):
        # if axis.upper() == "X":
        #     if abs(error) < self.threshold:
        #         # print(self.center_x_frames)
        #         self.center_x_frames += 1
        #     else:
        #         self.finishedX = False
        #         self.center_x_frames = 0

            # print(f"error X = {error}")

            # if self.center_x_frames < 75:
        self.adjustMove(axis, error)
            # else:
            #     self.finishedX = True

        # elif axis.upper() == "Y":
        #     if abs(error) < self.threshold:
        #         self.center_y_frames += 1
        #     else:
        #         self.finishedY = False
        #         self.center_y_frames = 0

        #     # print(f"error Y = {error}")

        #     if self.center_y_frames < 100:
        #         self.finishedY = False
        #         self.adjustMove(axis, error)
        #     else:
        #         self.finishedY = True

        if axis.upper() == "X":
            return False
        # elif axis.upper() == "Y":
        #     return self.finishedY
        else:
            return None

    # Returns error between center of frame and center of bounding box
    def getError(self, box, frame_width, frame_height):
        if box is not None:
            x_center, y_center, BB_width, BB_height = box
            BB_center = (int(x_center), int(y_center))
            origin = (frame_width // 2 + self.offsetX, frame_height // 2 + self.offsetY)

            Xerror = (BB_center[0] - origin[0]) * -1
            Yerror = BB_center[1] - origin[1]

            Xerror_norm = Xerror / BB_width
            Yerror_norm = Yerror / BB_height

            return Xerror_norm, Yerror_norm
        else:
            return 0, 0

    def centralizeXY(
        self,
        pid_x_constants,
        forwardSpeed=0,
        isCentralizeX=False,
        offsetY=0,
        offsetX=0,
    ):
        self.pid_x.set_constants(
            pid_x_constants[0], pid_x_constants[1], pid_x_constants[2]
        )

        id = None
        lost_detection_id = None
        result = None
        while self.cap_camera.isOpened():
            e3mel = True
            ret, frame_cam = self.cap_camera.read()
            if not ret:
                break

            (frame_height, frame_width) = frame_cam.shape[:2]

            result = self.model.track(
                source=frame_cam,
                tracker="botsort.yaml",
                persist=True,
                show=False,
                iou=0.5,
                conf=0.3,
                save=False,
                verbose=False,
                device=0,
            )

            frame_cam = result[0].plot()
            box, area = self.extract_results(result)

            if id == None and box is not None and result[0].boxes.id is not None:
                id_index = np.where(result[0].boxes.xywh.cpu().numpy() == box)[0][0]
                id = int(result[0].boxes.id.cpu().numpy()[id_index])

            try:
                changed_id = id != int(
                    result[0]
                    .boxes.id.cpu()
                    .numpy()[np.where(result[0].boxes.xywh.cpu().numpy() == box)[0][0]]
                )
            except:
                changed_id = True

            if box is None:
                cv2.imshow(f"AUV", frame_cam)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                e3mel = False
            elif id is not None and changed_id:
                self.dontCentralize = True
                if lost_detection_id is None:
                    lost_detection_id = True
            else:
                self.dontCentralize = False

            if e3mel:
                x_center, y_center, BB_width, BB_height = box
                area = BB_width * BB_height

                BB_center = (
                    int(x_center + offsetX * x_center),
                    int(y_center + offsetY * y_center),
                )
                origin = (
                    int(frame_width // 2 + self.offsetX * BB_width),
                    int(frame_height // 2 - self.offsetY * BB_height),
                )
                Xcoord1 = int(x_center - BB_width // 2)
                Xcoord2 = int(x_center + BB_width // 2)
                Ycoord1 = int(y_center + BB_height // 2)
                Ycoord2 = int(y_center - BB_height // 2)

                # detection
                cv2.rectangle(
                    frame_cam,
                    pt1=(Xcoord1, Ycoord1),
                    pt2=(Xcoord2, Ycoord2),
                    color=(255, 0, 0),
                    thickness=3,
                )
                # center points
                cv2.circle(
                    frame_cam, BB_center, radius=3, color=(255, 255, 255), thickness=-1
                )
                cv2.circle(frame_cam, origin, radius=3, color=(0, 0, 0), thickness=-1)
                # X&Y error lines
                cv2.arrowedLine(
                    frame_cam,
                    (BB_center[0], frame_height // 2 - int(self.offsetY * BB_height)),
                    BB_center,
                    (0, 255, 0),
                    2,
                )
                cv2.arrowedLine(
                    frame_cam,
                    (frame_width // 2 + int(self.offsetX * BB_width), BB_center[1]),
                    BB_center,
                    (0, 0, 255),
                    2,
                )
                # X&Y axis
                cv2.line(
                    frame_cam,
                    (frame_width // 2 + int(self.offsetX * BB_width), 0),
                    (frame_width // 2 + int(self.offsetX * BB_width), frame_height),
                    (0, 0, 0),
                    1,
                )
                cv2.line(
                    frame_cam,
                    (0, frame_height // 2 - int(self.offsetY * BB_height)),
                    (frame_width, frame_height // 2 - int(self.offsetY * BB_height)),
                    (0, 0, 0),
                    1,
                )

                # find error between center of bounding box and frame
                Xerror = (BB_center[0] - origin[0]) * -1

                # normalize error in regards to bounding box
                Xerror_norm = Xerror / BB_width

                self.hamada[1] = forwardSpeed  # sets rov normal forward speed

                if not self.dontCentralize:
                    if isCentralizeX:
                        self.minimize_error("X", Xerror_norm)
                    else:
                        self.hamada[0] = 0

                self.hamada[1] = forwardSpeed

                # self.sendHamada(self.hamada)
                print(self.hamada)

                self.last_hamada = self.hamada.copy()

            cv2.imshow(f"Centralization", frame_cam)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        self.cap_camera.release()
        cv2.destroyAllWindows()
        return False
