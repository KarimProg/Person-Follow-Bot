import cv2
import time
import numpy as np

'''
Ta2riban aham file, fih kol el path el 7anemshih wel main functions
'''
class Centralization:
    # Setting default values
    def __init__(self, VIDEO_PATH_ZED, VIDEO_PATH_LF, pid_x, pid_y, pid_depth, mov, model, model_lf=None, threshold=0.1, ros_rate=3):
        self.center_x_frames = 0
        self.center_y_frames = 0
        self.hamada = [0,0,0,0,0,0]
        self.last_hamada = [0,0,0,0,0,0]
        self.threshold = threshold
        self.pid_x = pid_x
        self.pid_y = pid_y
        self.pid_depth = pid_depth
        self.mov = mov
        self.model = model
        self.model_lf = model_lf
        self.video_src_zed = VIDEO_PATH_ZED
        self.video_src_lf = VIDEO_PATH_LF
        self.cap_zed = cv2.VideoCapture(self.video_src_zed)
        self.cap_lf = cv2.VideoCapture(self.video_src_lf)
        self.finishedX = False
        self.finishedY = False
        self.no_detection = 0
        self.offsetX = -0
        self.offsetY = 0.05
        self.prev_time = time.time()
        self.ros_rate = ros_rate
        self.dontCentralize = False

    # Function to move ROV by publishing on hamada (core)
    def sendHamada(self,move):
        if time.time() - self.prev_time > 1/self.ros_rate:
            self.prev_time = time.time()

            self.hamada = move
            if self.hamada != self.last_hamada:
                self.mov.set_hamada(self.hamada,verbose=False)
                self.last_hamada = self.hamada.copy()

    # Function that returns bounding boxes from YOLO (core)
    def extract_results(self,result, class_id : int):
        boxes = result[0].boxes.xywh.cpu().numpy()
        classes = result[0].boxes.cls.cpu().numpy()
        largest_area = 0
        largestBox = None

        boxes = boxes.tolist()
        for i in reversed(range(len(classes))):
            if int(classes[i]) != class_id:
                boxes.pop(i)

        for box in boxes:
            x_centre, y_centre, w1, h1 = box
            area = w1 * h1
            if area > largest_area:
                largest_area = area
                largestBox = box
            
        
        return largestBox, largest_area
    
    def extract_two_results(self,result, class_id : int):
        boxes = result[0].boxes.xywh.cpu().numpy()
        classes = result[0].boxes.cls.cpu().numpy()
        largest_area = 0
        largestBox = None

        boxes = boxes.tolist()
        for i in reversed(range(len(classes))):
            if int(classes[i]) != class_id:
                boxes.pop(i)

        if len(boxes) < 2:
            return None, None

        print(f'#boxes= {len(boxes)}')
        print(f'boxes : {boxes}')
        areas = []
        # boxes = []

        print(boxes[0])
        for box in boxes:
            x_centre, y_centre, w1, h1 = box
            area = w1 * h1
            print(f'area = {area}')
            areas.append(area)
            # boxes.append(box)
            if area > largest_area:
                largest_area = area
                largestBox = box

        print(f'areas: {areas}')
        areas.pop(areas.index(largest_area))
        second_largestBox = boxes[areas.index(max(areas))]

        print("boxes::::", largestBox, second_largestBox)
            
        
        return largestBox, largest_area
    
    def extract_results_bucket(self, bucket, result, class_id : int):
        boxes = result[0].boxes.xywh.cpu().numpy()
        classes = result[0].boxes.cls.cpu().numpy()
        largest_area = 0
        largestBox = None

        boxes = boxes.tolist()
        for i in reversed(range(len(classes))):
            if int(classes[i]) != class_id:
                boxes.pop(i)

        for box in boxes:
            x_centre, y_centre, w1, h1 = box
            area = w1 * h1
            if area > largest_area:
                largest_area = area
                largestBox = box
            
        
        return largestBox, largest_area
    
    # Needed to interact with x and y PIDs
    def adjustMove(self,axis : str, error):
        if axis.upper() == "X":
            # if abs(error) > self.threshold:
            pidVal = self.pid_x.calculate(error)
            self.hamada[0] = pidVal

        elif axis.upper() == "Y":
            # if abs(error) > self.threshold:
            pidVal = self.pid_y.calculate(error)
            self.hamada[2] = pidVal

    # Implements logic of how many frames ROV should be centralized for
    def minimize_error(self,axis : str, error):
        if axis.upper() == "X":
            if abs(error) < self.threshold:
                # print(self.center_x_frames)
                self.center_x_frames += 1
            else:
                self.finishedX = False  
                self.center_x_frames = 0

            # print(f"error X = {error}")
            
            if self.center_x_frames < 75:
                self.adjustMove(axis,error)  
            else:
                # self.mov.stop_AUV(self.hamada.copy())
                self.finishedX = True

        elif axis.upper() == "Y":
            if abs(error) < self.threshold:
                self.center_y_frames += 1
            else:
                self.finishedY = False  
                self.center_y_frames = 0

            # print(f"error Y = {error}")

            if self.center_y_frames < 100:
                self.finishedY = False
                self.adjustMove(axis,error)        
            else:
                # self.mov.stop_AUV(self.hamada.copy())
                self.finishedY = True
        

        if axis.upper() == 'X':
            return self.finishedX
        elif axis.upper() =='Y':
            return self.finishedY
        else:
            return None
        
    
    # Returns error between center of frame and center of bounding box
    def getError(self, box, frame_width, frame_height):
        if box is not None:
            x_center, y_center, BB_width, BB_height = box
            BB_center = (int(x_center), int(y_center))
            origin = (frame_width // 2+self.offsetX, frame_height // 2+self.offsetY)

            Xerror = (BB_center[0] - origin[0])*-1
            Yerror = (BB_center[1] - origin[1])

            Xerror_norm = Xerror / BB_width
            Yerror_norm = Yerror / BB_height

            return Xerror_norm, Yerror_norm
        else: 
            return 0, 0
        
    # Function to get average RGB value of a channel in a frame
    def get_avg_rgb(self, frame, channel_select=0):
        separate_channel = frame[:, frame.shape[1]//2-20:frame.shape[1]//2+20, 2-channel_select]

        return np.mean(separate_channel)
        
    '''
    forwardSpeed: determines what speed rov will normally be moving at
    exitOn: determines exit condition for function
        'centralize': exits once error threshold is met for a set amount of frames
        'disappear': exits once no detection for set amount of frames
        'passGate': once in gate, goes forward till gate disappears and exits 
    ''' 

    def findDiffHeight(self, frame):
        print('')

    def Find(self, direction, id=3):
        print("trying to find the stand")
        number_of_movement=0
        while self.cap_zed.isOpened():
            ret, frame_zed = self.cap_zed.read()
            if not ret:
                break
            result = self.model.track(source=frame_zed, show=False, iou=0.5,conf=0.5, save = False ,verbose = False, device=0, classes=[id])    
            box, _ = self.extract_results(result, id)
            if not box:
                self.mov.move_byTime([200*direction, 0, 0, 0, 0, 0], 2, True)
                number_of_movement+=1
            else:
                print("we found the stand")
                return True

    def mapGates(self, searchTime=10):
        areas={}
        speed = 250
        self.sendHamada([speed,0,0,0,0,0])
        startTime = time.time()
        firstChange = True
        secondChange = True
        while time.time()-startTime < searchTime:
            if time.time()-startTime > searchTime//4 and firstChange:
                speed*=-1
                firstChange=False
                self.sendHamada([speed,0,0,0,0,0])
                print(f'time now (1st change): {time.time()-startTime}')

            if time.time()-startTime > searchTime*(3/4) and secondChange:
                speed*=-1
                secondChange=False
                self.sendHamada([speed,0,0,0,0,0])
                print(f'time now (2nd change): {time.time()-startTime}')

            ret, frame = self.cap_zed.read()
            if not ret:
                continue

            result = self.model.track(source=frame, tracker='botsort.yaml', persist=True, show=False, iou=0.5,conf=0.3, save = False ,verbose = False, device=0, classes=[3])
            frame = result[0].plot()
            cv2.imshow('mapping', frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            box, area = self.extract_results(result, 3)
            area = area-area%10000
            print(f"el area aheeeee: {area}")

            areas[int(time.time()-startTime)] += area


        print(max(areas))        
        cv2.destroyAllWindows()
        self.mov.stop_AUV([speed,0,0,0,0,0])


    def centralizeXY(self, pid_x_constants, pid_y_constants, forwardSpeed=0, exitOn='centralize', passTimeDelay=2, centralizeOn=3,isCentralizeX=False, isCentralizeY=False, offsetY=0, offsetX=0):
        self.pid_x.set_constants(pid_x_constants[0], pid_x_constants[1], pid_x_constants[2])
        self.pid_y.set_constants(pid_y_constants[0], pid_y_constants[1], pid_y_constants[2])
        in_gate = False
        num_frames_in_gate = 0
        num_frames_out_gate = 0
        isCenteredX = False
        isCenteredY = False
        id = None
        lost_detection_id = None
        while self.cap_zed.isOpened():
            e3mel=True
            ret, frame_zed = self.cap_zed.read()
            if not ret:
                break

            (frame_height, frame_width)  = frame_zed.shape[:2]
            start=time.time()
            result = self.model.track(source=frame_zed, tracker='botsort.yaml', persist=True, show=False, iou=0.5,conf=0.3, save = False ,verbose = False, device=0, classes=[centralizeOn,5 ,4])    
            # print(f"fps is {1/(time.time()-start)}")
            # _, _ = self.extract_two_results(result, 1)
            # if result[0].boxes.id is not None:
            #     print(result[0].boxes.id.cpu().numpy())

            frame_zed = result[0].plot()
            box, area = self.extract_results(result, centralizeOn)

            if id == None and box is not None and result[0].boxes.id is not None:
                id_index = np.where(result[0].boxes.xywh.cpu().numpy() == box)[0][0]
                id = int(result[0].boxes.id.cpu().numpy()[id_index])

             
            try:
                changed_id = id != int(result[0].boxes.id.cpu().numpy()[np.where(result[0].boxes.xywh.cpu().numpy() == box)[0][0]])
            except:
                changed_id = True

            if box is None:
                cv2.imshow(f'AUV', frame_zed)
            
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                e3mel=False 
            elif id is not None and changed_id:
                self.dontCentralize = True
                if lost_detection_id is None:
                    lost_detection_id = True
            else:
                self.dontCentralize = False
                

            self.dontCentralize=False  
            lost_detection_id=False           
            if e3mel: 
                x_center, y_center, BB_width, BB_height = box
                area = BB_width * BB_height
                
                BB_center = (int(x_center+offsetX*x_center), int(y_center+offsetY*y_center))
                origin = (int(frame_width // 2+self.offsetX*BB_width), int(frame_height // 2-self.offsetY*BB_height))
                Xcoord1 = int(x_center - BB_width//2)
                Xcoord2 = int(x_center + BB_width//2)
                Ycoord1 = int(y_center + BB_height//2)
                Ycoord2 = int(y_center - BB_height//2)

                
                # detection
                cv2.rectangle(frame_zed, pt1=(Xcoord1, Ycoord1), pt2=(Xcoord2, Ycoord2), color=(255,0,0),thickness=3)
                # center points
                cv2.circle(frame_zed, BB_center, radius=3, color=(255, 255, 255), thickness=-1)
                cv2.circle(frame_zed, origin, radius=3, color=(0, 0, 0), thickness=-1)
                # X&Y error lines
                cv2.arrowedLine(frame_zed,(BB_center[0], frame_height // 2-int(self.offsetY*BB_height)),BB_center,(0,255,0),2)
                cv2.arrowedLine(frame_zed,(frame_width // 2+int(self.offsetX*BB_width), BB_center[1]),BB_center,(0,0,255),2)
                # X&Y axis
                cv2.line(frame_zed,(frame_width // 2+int(self.offsetX*BB_width), 0),(frame_width // 2+int(self.offsetX*BB_width), frame_height),(0,0,0),1)
                cv2.line(frame_zed,(0, frame_height // 2-int(self.offsetY*BB_height)),(frame_width, frame_height // 2-int(self.offsetY*BB_height)),(0,0,0),1)

                # find error between center of bounding box and frame
                Xerror = (BB_center[0] - origin[0])*-1
                Yerror = (BB_center[1] - origin[1])

                # normalize error in regards to bounding box
                Xerror_norm = Xerror / BB_width
                Yerror_norm = Yerror / BB_height

                isCenteredX = False
                isCenteredY = False
                self.hamada[1] = forwardSpeed   # sets rov normal forward speed

                if not self.dontCentralize:
                    if isCentralizeY:
                        isCenteredY = self.minimize_error('Y',Yerror_norm)
                    else:
                        self.hamada[2] = 0
                        
                    if isCentralizeX:
                        isCenteredX = self.minimize_error('X',Xerror_norm)
                    else:
                        self.hamada[0] = 0
                
                # print(f"area: {area}")

                ##################################################################
                # if area > 74069 and forwardSpeed == 0:
                #     self.hamada[1] = -100
                ##################################################################

                # elif area < 40000 and forwardSpeed == 0:
                #     self.hamada[1] = 100
                else:
                    self.hamada[1] = forwardSpeed
                if lost_detection_id == True:
                    self.hamada[0] = int(self.hamada[0] * -1.5)
                    lost_detection_id = False
                self.sendHamada(self.hamada)

                self.last_hamada = self.hamada.copy()            


            if  exitOn == 'centralize':
                if (isCenteredX and isCentralizeX) or (isCenteredY and isCentralizeY):
                    self.mov.stop_AUV(self.hamada)
                    print("CCCCCCCEENETTTTTTTTTTEEEEERRRREEEECDCCCC!!!!!!!!!!!!!!!!!")
                    return True
            elif exitOn == 'disappear':
                if box is None:
                    self.no_detection += 1
                else:
                    self.no_detection = 0
                
                if self.no_detection > 20:
                    self.mov.stop_AUV(self.hamada)
                    return True
                
            elif exitOn == 'passGate':
                ret_lf, frame_lf = self.cap_lf.read()
                result = self.model_lf.predict(frame_lf, verbose=False)[0]
                final = result.probs.top1
                annotated_frame = result.plot()
                cv2.imshow('frame_lf', annotated_frame)

                if final == 0:
                    num_frames_in_gate += 1
                    if num_frames_in_gate > 15:
                        print("In Gate")
                        in_gate = True

                if final == 1 and in_gate == True:
                    num_frames_out_gate += 1
                    if num_frames_out_gate > 5:
                        self.mov.stop_AUV(self.hamada)
                        print("Out Gate")
                        return True
                    
            elif exitOn == 'passGate2':
                ret_lf, frame_lf = self.cap_lf.read()
                frame_lf = frame_lf[:, :,:]
                result = self.model_lf.predict(frame_lf, verbose=False)[0]
                final = result.probs.top1
                annotated_frame = result.plot()
                cv2.imshow('frame_lf', annotated_frame)

                if final == 0:
                    num_frames_in_gate += 1
                    if num_frames_in_gate > 15:
                        print("In Gate")
                        self.mov.move_byTime([0,180,0,0,0,0], 2, False)
                        return True
                
            elif exitOn == 'area_size':
                print(f'area exceeded: {area}')
                if area > 50:
                    return True
            else:
                raise NameError("Undefined Exit Condition")

            cv2.imshow(f'AUV', frame_zed)
            
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        self.cap_zed.release()
        self.cap_lf.release()
        cv2.destroyAllWindows()
        return False



    # def StandCentralizing(self, id=4,framesthresould=50,centeredX=False,centeredY=False):
    #     # first we need to centralize with the stand and grab the object
        
        
    #     ZPIDflag =True
    #     noDetectionFrames = 0
    #     while self.cap_zed.isOpened():

    #         if noDetectionFrames > framesthresould:
    #             self.mov.stop_AUV(self.hamada)
    #             print("No detection for 50 frames")
    #             return False
            
    #         ret, frame_zed = self.cap_zed.read()
    #         if not ret:
    #             break
            
    #         (frame_height, frame_width)  = frame_zed.shape[:2]
    #         result = self.model.track(source=frame_zed, show=False, iou=0.5,conf=0.5, save = False ,verbose = False, device=0, classes=[id])    
            
    #         box, area = self.extract_results(result, id)
    #         # print(f"Area: {area}")
    #         if box is None:
    #             print("ANA MSH SHAYEF HAGAAAAA")
    #             noDetectionFrames += 1
    #             # move = [0]*6
    #             # self.sendHamada(move)                
            
    #         if box is not None:
    #             # print("ba7seb")
    #             noDetectionFrames = 0
    #             x_center, y_center, BB_width, BB_height = box
    #             area = BB_width * BB_height
    #             # BB_center = (int(x_center), int(y_center-(BB_height//2))) # this is where you get the lowest Y and put it instead of the the y_center
    #             BB_center = (int(x_center), int(y_center)) # normal center
    #             origin = (frame_width // 2+self.offsetX*BB_width, frame_height // 2-self.offsetY*BB_height)
    #             Xcoord1 = int(x_center - BB_width//2)
    #             Xcoord2 = int(x_center + BB_width//2)
    #             Ycoord1 = int(y_center + BB_height//2)
    #             Ycoord2 = int(y_center - BB_height//2)

    #             # detection
    #             cv2.rectangle(frame_zed, pt1=(Xcoord1, Ycoord1), pt2=(Xcoord2, Ycoord2), color=(255,0,0),thickness=3)
    #             # center points
    #             cv2.circle(frame_zed, BB_center, radius=3, color=(255, 255, 255), thickness=-1)
    #             cv2.circle(frame_zed, origin, radius=3, color=(0, 0, 0), thickness=-1)
    #             # X&Y error lines
    #             cv2.arrowedLine(frame_zed,(BB_center[0], frame_height // 2-self.offsetY),BB_center,(0,255,0),2)
    #             cv2.arrowedLine(frame_zed,(frame_width // 2+self.offsetX, BB_center[1]),BB_center,(0,0,255),2)
    #             # X&Y axis
    #             cv2.line(frame_zed,(frame_width // 2+self.offsetX, 0),(frame_width // 2+self.offsetX, frame_height),(0,0,0),1)
    #             cv2.line(frame_zed,(0, frame_height // 2-self.offsetY),(frame_width, frame_height // 2-self.offsetY),(0,0,0),1)

    #             # find error between center of bounding box and frame
    #             Xerror = (BB_center[0] - origin[0])*-1
    #             Yerror = (BB_center[1] - origin[1])

    #             # normalize error in regards to bounding box
    #             Xerror_norm = Xerror / BB_width
    #             Yerror_norm = Yerror / BB_height

    #         cv2.imshow(f'AUV', frame_zed)
    #         if cv2.waitKey(1) & 0xFF == ord("q"):
    #             break
    #         # centralize on X axis
    #         if box is not None :
    #             # print(f"Hanzabat x we y we elerrors {Xerror_norm} and {Yerror_norm}")
    #             if not centeredY:
    #                 centeredY = self.minimize_error('Y',Yerror_norm)
    #             if centeredY and ZPIDflag:
    #                 ZPIDflag = False
    #                 print("STOPPIIIIIIIIIIIIIING")
    #                 self.mov.stop_AUV(self.last_hamada)
    #                 self.hamada[2]=0
    #             if centeredY and not centeredX:
    #                 centeredX = self.minimize_error('X',Xerror_norm)
    #             self.sendHamada(self.hamada)
    #             self.last_hamada = self.hamada.copy()            
                
    #             if centeredX and centeredY:
    #                 self.mov.stop_AUV(self.hamada)
    #                 return True
    #     return False
    

    # def ObjectGrabbingWithDownwardGripper (self, pid_x_constants, pid_y_constants, sol_pin, id=5, zedAngle=1400, framesthresould=50, centeredX=False ,centeredY=False, grabbingZedAngle=1400):
    #     # first we need to centralize with the stand and grab the object
    #     # self.mov.set_servo_camera(zedAngle)
    #     self.pid_x.set_constants(pid_x_constants[0], pid_x_constants[1], pid_x_constants[2])
    #     self.pid_y.set_constants(pid_y_constants[0], pid_y_constants[1], pid_y_constants[2])
    #     AtFirst = True
    #     ZPIDflag = True
    #     self.mov.set_servo_camera(zedAngle)
    #     noDetectionFrames = 0
    #     noDetectionFramesAtFirst = 0

    #     while self.cap_zed.isOpened():

    #         if noDetectionFrames > framesthresould and not AtFirst:
    #             self.mov.stop_AUV(self.hamada)
    #             print("No detection for 50 frames")
    #             return False
            
    #         ret, frame_zed = self.cap_zed.read()
    #         if not ret:
    #             break
            
    #         (frame_height, frame_width)  = frame_zed.shape[:2]
    #         result = self.model.track(source=frame_zed, show=False, iou=0.5,conf=0.5, save = False ,verbose = False, device=0, classes=[id])    
            
    #         box, area = self.extract_results(result, id)
    #         # print(f"Area: {area}")
    #         if box is None:
    #             noDetectionFramesAtFirst+=1
    #             if AtFirst and noDetectionFramesAtFirst>5:
    #                 self.mov.move_byTime([0, 0, 150, 0, 0, 0], 2, True)
    #                 noDetectionFrames=0
    #                 noDetectionFramesAtFirst=0
    #                 continue
    #             elif not AtFirst :
    #                 print("ANA MSH SHAYEF HAGAAAAA")
    #                 noDetectionFrames += 1
    #             # move = [0]*6
    #             # self.sendHamada(move)                
            
    #         if box is not None:
    #             # print("ba7seb")
    #             noDetectionFrames = 0
    #             x_center, y_center, BB_width, BB_height = box
    #             area = BB_width * BB_height
    #             # BB_center = (int(x_center), int((y_center-(BB_height//2))-0.25*(y_center-(BB_height//2)))) # this is where you get the lowest Y and put it instead of the the y_center
    #             BB_center = (int(x_center), int((y_center-(BB_height//2)))) # this is where you get the lowest Y and put it instead of the the y_center
    #             origin = (frame_width // 2+self.offsetX, frame_height // 2-self.offsetY)
    #             Xcoord1 = int(x_center - BB_width//2)
    #             Xcoord2 = int(x_center + BB_width//2)
    #             Ycoord1 = int(y_center + BB_height//2)
    #             Ycoord2 = int(y_center - BB_height//2)

    #             # detection
    #             cv2.rectangle(frame_zed, pt1=(Xcoord1, Ycoord1), pt2=(Xcoord2, Ycoord2), color=(255,0,0),thickness=3)
    #             # center points
    #             cv2.circle(frame_zed, BB_center, radius=3, color=(255, 255, 255), thickness=-1)
    #             cv2.circle(frame_zed, origin, radius=3, color=(0, 0, 0), thickness=-1)
    #             # X&Y error lines
    #             cv2.arrowedLine(frame_zed,(BB_center[0], frame_height // 2-self.offsetY),BB_center,(0,255,0),2)
    #             cv2.arrowedLine(frame_zed,(frame_width // 2+self.offsetX, BB_center[1]),BB_center,(0,0,255),2)
    #             # X&Y axis
    #             cv2.line(frame_zed,(frame_width // 2+self.offsetX, 0),(frame_width // 2+self.offsetX, frame_height),(0,0,0),1)
    #             cv2.line(frame_zed,(0, frame_height // 2-self.offsetY),(frame_width, frame_height // 2-self.offsetY),(0,0,0),1)

    #             # find error between center of bounding box and frame
    #             Xerror = (BB_center[0] - origin[0])*-1
    #             Yerror = (BB_center[1] - origin[1])

    #             # normalize error in regards to bounding box
    #             Xerror_norm = Xerror / BB_width
    #             Yerror_norm = Yerror / BB_height

    #         cv2.imshow(f'AUV', frame_zed)
    #         if cv2.waitKey(1) & 0xFF == ord("q"):
    #             break
    #         # centralize on X axis
    #         if box is not None and (not centeredX or not centeredY) :
    #             AtFirst=False
    #             # print(f"Hanzabat x we y we elerrors {Xerror_norm} and {Yerror_norm}")
    #             if not centeredY:
    #                 print("BENSANTAR Y")
    #                 centeredY = self.minimize_error('Y',Yerror_norm)

    #             if centeredY and ZPIDflag:
    #                 self.mov.set_servo_camera(grabbingZedAngle)
    #                 ZPIDflag = False
    #                 self.mov.stop_AUV(self.last_hamada)
    #                 self.hamada[2]=0

    #             if centeredY and not centeredX:
    #                 print("BENSANTAR X")
    #                 centeredX = self.minimize_error('X',Xerror_norm)

    #             self.sendHamada(self.hamada)
    #             self.last_hamada = self.hamada.copy()            
                
    #             # if centeredX and centeredY:
    #             if centeredX and centeredY:
    #                 print("NAFEZ YA ME3ALEEEEEEEEEEEEM")
    #                 self.mov.stop_AUV(self.last_hamada)
    #                 self.hamada=[0,0,0,0,0,0]
    #                 # self.sendHamada(self.hamada)
    #                 # Open gripper
    #                 self.mov.trigger_solenoid(sol_pin)
    #                 self.hamada[1]=100
    #                 # self.mov.move_byTime([0, 200, 0, 0, 0, 0], 3, False)
    #                 self.sendHamada(self.hamada)
    #                 self.last_hamada = self.hamada.copy()            


    #         elif box is None and centeredY and centeredX:
    #             self.mov.stop_AUV(self.hamada)
    #             print("khalasna allahom saly 3ala elnabaaaay")
    #             # self.mov.move_byTime([0, 0, 200, 0, 0, 0], 1, False)
    #             # Close gripper
    #             self.mov.trigger_solenoid(sol_pin)
    #             # Move up
    #             self.mov.move_byTime([0, 0, 200, 0, 0, 0], 2, False)
    #             # Rotate 180 degrees
    #             self.mov.rotate_with_angle(180)
    #             return True

    #     return False
        
    # def ObjectGrabbingWithUpwardGripper (self, pid_x_constants, pid_y_constants, sol_pin, id=5, zedAngle=1700, framesthresould=50, centeredX=False ,centeredY=True, grabbingZedAngle=1700):
    #     # first we need to centralize with the stand and grab the object
    #     # self.mov.set_servo_camera(zedAngle)
    #     self.pid_x.set_constants(pid_x_constants[0], pid_x_constants[1], pid_x_constants[2])
    #     self.pid_y.set_constants(pid_y_constants[0], pid_y_constants[1], pid_y_constants[2])
    #     AtFirst = True
    #     ZPIDflag = True
    #     self.mov.set_servo_camera(zedAngle)
    #     noDetectionFrames = 0
    #     noDetectionFramesAtFirst = 0

    #     while self.cap_zed.isOpened():

    #         if noDetectionFrames > framesthresould and not AtFirst:
    #             self.mov.stop_AUV(self.hamada)
    #             print("No detection for 50 frames")
    #             return False
            
    #         ret, frame_zed = self.cap_zed.read()
    #         if not ret:
    #             break
            
    #         (frame_height, frame_width)  = frame_zed.shape[:2]
    #         result = self.model.track(source=frame_zed, show=False, iou=0.5,conf=0.5, save = False ,verbose = False, device=0, classes=[id])    
            
    #         box, area = self.extract_results(result, id)
    #         # print(f"Area: {area}")
    #         if box is None:
    #             noDetectionFramesAtFirst+=1
    #             if AtFirst and noDetectionFramesAtFirst>10:
    #                 zedAngle+=50
    #                 if(zedAngle>1800):
    #                     self.mov.set_servo_camera(zedAngle)
    #                 noDetectionFrames=0
    #                 noDetectionFramesAtFirst=0
    #                 continue
    #             elif not AtFirst :
    #                 print("ANA MSH SHAYEF HAGAAAAA")
    #                 noDetectionFrames += 1
               
            
    #         if box is not None:
    #             # print("ba7seb")
    #             noDetectionFrames = 0
    #             x_center, y_center, BB_width, BB_height = box
    #             area = BB_width * BB_height
    #             # BB_center = (int(x_center), int((y_center-(BB_height//2))-0.25*(y_center-(BB_height//2)))) # this is where you get the lowest Y and put it instead of the the y_center
    #             BB_center = (int(x_center), int((y_center-(BB_height//2)))) # this is where you get the lowest Y and put it instead of the the y_center
    #             origin = (frame_width // 2+self.offsetX, frame_height // 2-self.offsetY)
    #             Xcoord1 = int(x_center - BB_width//2)
    #             Xcoord2 = int(x_center + BB_width//2)
    #             Ycoord1 = int(y_center + BB_height//2)
    #             Ycoord2 = int(y_center - BB_height//2)

    #             # detection
    #             cv2.rectangle(frame_zed, pt1=(Xcoord1, Ycoord1), pt2=(Xcoord2, Ycoord2), color=(255,0,0),thickness=3)
    #             # center points
    #             cv2.circle(frame_zed, BB_center, radius=3, color=(255, 255, 255), thickness=-1)
    #             cv2.circle(frame_zed, origin, radius=3, color=(0, 0, 0), thickness=-1)
    #             # X&Y error lines
    #             cv2.arrowedLine(frame_zed,(BB_center[0], frame_height // 2-self.offsetY),BB_center,(0,255,0),2)
    #             cv2.arrowedLine(frame_zed,(frame_width // 2+self.offsetX, BB_center[1]),BB_center,(0,0,255),2)
    #             # X&Y axis
    #             cv2.line(frame_zed,(frame_width // 2+self.offsetX, 0),(frame_width // 2+self.offsetX, frame_height),(0,0,0),1)
    #             cv2.line(frame_zed,(0, frame_height // 2-self.offsetY),(frame_width, frame_height // 2-self.offsetY),(0,0,0),1)

    #             # find error between center of bounding box and frame
    #             Xerror = (BB_center[0] - origin[0])*-1
    #             # Yerror = (BB_center[1] - origin[1])

    #             # normalize error in regards to bounding box
    #             Xerror_norm = Xerror / BB_width
    #             # Yerror_norm = Yerror / BB_height

    #         cv2.imshow(f'AUV', frame_zed)
    #         if cv2.waitKey(1) & 0xFF == ord("q"):
    #             break
    #         # centralize on X axis
    #         if box is not None and not centeredX :
    #             AtFirst=False
    #             # print(f"Hanzabat x we y we elerrors {Xerror_norm} and {Yerror_norm}")

    #             if centeredX:
    #                 print("BENSANTAR X")
    #                 centeredX = self.minimize_error('X',Xerror_norm)

    #             self.sendHamada(self.hamada)
    #             self.last_hamada = self.hamada.copy()            
                
    #             # if centeredX and centeredY:
    #         if centeredX :
    #             print("Going to Grab the object")
    #             self.mov.stop_AUV(self.last_hamada)
    #             self.hamada=[0,0,0,0,0,0]
    #             self.sendHamada(self.hamada)
    #             # Open gripper
    #             self.mov.trigger_solenoid(sol_pin)
    #             self.mov.move_byTime([0, 200, 0, 0, 0, 0], 4, False)
    #             # Close gripper
    #             self.mov.trigger_solenoid(sol_pin)
    #             # Rotate 180 degrees
    #             self.mov.rotate_with_angle(180)
    #             return True

    #     return False

    # def centralizeBucket(self, framesthresould=50, bucket='center'):
    #     first=True
    #     noDetectionFrames = 0
    #     idd=0
    #     while self.cap_zed.isOpened():

    #         if noDetectionFrames > framesthresould:
    #             self.mov.stop_AUV(self.hamada)
    #             print("No detection for 50 frames")
    #             return False
            
    #         ret, frame_zed = self.cap_zed.read()
    #         if not ret:
    #             break

    #         # Perform inference on the frame
    #         results = self.model(frame_zed)
            
    #         # Get boxes, scores, and class IDs from the results
    #         for result in results:
    #             for box in result.boxes:
    #                 # Class ID and confidence score
    #                 class_id = int(box.cls)
    #                 if first:
    #                     idd=class_id
    #                     first=False
    #                     break
    #             break


    #         (frame_height, frame_width)  = frame_zed.shape[:2]
    #         result = self.model.track(source=frame_zed, show=False, iou=0.5,conf=0.5, save = False ,verbose = False, device=0)    
            
    #         box, area = self.extract_results_bucket(bucket,result, id)
    #         # print(f"Area: {area}")
    #         if box is None:
    #             cv2.imshow(f'AUV', frame_zed)
    #             noDetectionFrames += 1
    #             if cv2.waitKey(1) & 0xFF == ord("q"):
    #                 break
    #             # move = [0]*6
    #             # self.sendHamada(move)                
    #             continue

    #         x_center, y_center, BB_width, BB_height = box
    #         area = BB_width * BB_height
    #         BB_center = (int(x_center), int(y_center))
    #         origin = (frame_width // 2+self.offsetX, frame_height // 2-self.offsetY)
    #         Xcoord1 = int(x_center - BB_width//2)
    #         Xcoord2 = int(x_center + BB_width//2)
    #         Ycoord1 = int(y_center + BB_height//2)
    #         Ycoord2 = int(y_center - BB_height//2)

    #         # detection
    #         cv2.rectangle(frame_zed, pt1=(Xcoord1, Ycoord1), pt2=(Xcoord2, Ycoord2), color=(255,0,0),thickness=3)
    #         # center points
    #         cv2.circle(frame_zed, BB_center, radius=3, color=(255, 255, 255), thickness=-1)
    #         cv2.circle(frame_zed, origin, radius=3, color=(0, 0, 0), thickness=-1)
    #         # X&Y error lines
    #         cv2.arrowedLine(frame_zed,(BB_center[0], frame_height // 2-self.offsetY),BB_center,(0,255,0),2)
    #         cv2.arrowedLine(frame_zed,(frame_width // 2+self.offsetX, BB_center[1]),BB_center,(0,0,255),2)
    #         # X&Y axis
    #         cv2.line(frame_zed,(frame_width // 2+self.offsetX, 0),(frame_width // 2+self.offsetX, frame_height),(0,0,0),1)
    #         cv2.line(frame_zed,(0, frame_height // 2-self.offsetY),(frame_width, frame_height // 2-self.offsetY),(0,0,0),1)

    #         # find error between center of bounding box and frame
    #         Xerror = (BB_center[0] - origin[0])*-1
    #         # Yerror = (BB_center[1] - origin[1])

    #         # normalize error in regards to bounding box
    #         Xerror_norm = Xerror / BB_width
    #         # Yerror_norm = Yerror / BB_height

    #         isCenteredX = False

    #         # centralize on X axis
    #         if(self.minimize_error('X',Xerror_norm)):
    #             self.mov.stop_AUV(self.hamada)
    #             return True
    #     return False
            

    # def insertBucket(self, id, zedAngle=1500, forwardSpeed=100, framesthresould=50, bucket='center'):

    #     noDetectionFrames = 0
    #     self.hamada[1] = forwardSpeed   # sets rov normal forward speed
    #     self.mov.set_servo_camera(zedAngle, verbose=False)
    #     while self.cap_zed.isOpened():

    #         if noDetectionFrames > framesthresould:
    #             self.mov.stop_AUV(self.hamada)
    #             print("we are on top of the bucket")
    #             self.mov.move_byTime([0,0,-200,0,0,0],4,verbose=False)
    #             return True
            
    #         ret, frame_zed = self.cap_zed.read()
    #         if not ret:
    #             break

    #         (frame_height, frame_width)  = frame_zed.shape[:2]
    #         result = self.model.track(source=frame_zed, show=False, iou=0.5,conf=0.5, save = False ,verbose = False, device=0, classes=[id])    
            
    #         box, area = self.extract_results(result, id)
    #         # print(f"Area: {area}")
    #         if box is None:
    #             cv2.imshow(f'AUV', frame_zed)
    #             noDetectionFrames += 1
    #             if cv2.waitKey(1) & 0xFF == ord("q"):
    #                 break
    #             # move = [0]*6
    #             # self.sendHamada(move)                
    #             continue

    #         x_center, y_center, BB_width, BB_height = box
    #         area = BB_width * BB_height
    #         BB_center = (int(x_center), int(y_center))
    #         origin = (frame_width // 2+self.offsetX, frame_height // 2-self.offsetY)
    #         Xcoord1 = int(x_center - BB_width//2)
    #         Xcoord2 = int(x_center + BB_width//2)
    #         Ycoord1 = int(y_center + BB_height//2)
    #         Ycoord2 = int(y_center - BB_height//2)

    #         # detection
    #         cv2.rectangle(frame_zed, pt1=(Xcoord1, Ycoord1), pt2=(Xcoord2, Ycoord2), color=(255,0,0),thickness=3)
    #         # center points
    #         cv2.circle(frame_zed, BB_center, radius=3, color=(255, 255, 255), thickness=-1)
    #         cv2.circle(frame_zed, origin, radius=3, color=(0, 0, 0), thickness=-1)
    #         # X&Y error lines
    #         cv2.arrowedLine(frame_zed,(BB_center[0], frame_height // 2-self.offsetY),BB_center,(0,255,0),2)
    #         cv2.arrowedLine(frame_zed,(frame_width // 2+self.offsetX, BB_center[1]),BB_center,(0,0,255),2)
    #         # X&Y axis
    #         cv2.line(frame_zed,(frame_width // 2+self.offsetX, 0),(frame_width // 2+self.offsetX, frame_height),(0,0,0),1)
    #         cv2.line(frame_zed,(0, frame_height // 2-self.offsetY),(frame_width, frame_height // 2-self.offsetY),(0,0,0),1)

    #         # find error between center of bounding box and frame
    #         Xerror = (BB_center[0] - origin[0])*-1
    #         # Yerror = (BB_center[1] - origin[1])

    #         # normalize error in regards to bounding box
    #         Xerror_norm = Xerror / BB_width

    #         # self.minimize_error('X',Xerror_norm) # if you want to centralize while moving forward
        
    #     return False
        