import cv2
import mediapipe as mp
import time


class handDetector():
    def __init__(self, mode=False, maxHands=1, detectionCon=0.5, trackCon=0.5):
        # It is used to specify whether the input images must be treated as static images or as a video stream. False for video stream
        self.mode = mode
        self.maxHands = maxHands
        #It is used to specify the minimum confidence value with which the detection from the person-detection model needs to be considered as successful. [0,1]
        self.detectionCon = detectionCon
        #It is used to specify the minimum confidence value with which the detection from the landmark-tracking model must be considered as successful[0,1]
        self.trackCon = trackCon

        self.mpHands = mp.solutions.hands #this module performs the hand recognition algorithm.
        #maxHands= number of hands detected in frame

        self.hands = self.mpHands.Hands(self.mode, self.maxHands,self.detectionCon, self.trackCon)

        # draw the detected key points
        self.mpDraw = mp.solutions.drawing_utils

    def findHands(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)# converts from bgr to rgb
        self.results = self.hands.process(imgRGB)
        #self.results = self.hands.process(img)
        # print(results.multi_hand_landmarks)

        #for checking if any hand detected or not using results.multi_hand_landmarks
        if self.results.multi_hand_landmarks:
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, handLms,
                                               self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo=0, draw=True):

        lmList = []
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
                # print(id, lm)
                h, w, c = img.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                # print(id, cx, cy)
                lmList.append([id, cx, cy])
                if draw:
                    cv2.circle(img, (cx, cy), 15, (255, 0, 255), cv2.FILLED)

        return lmList
