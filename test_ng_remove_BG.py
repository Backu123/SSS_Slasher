import cv2
import cvzone
from cvzone.SelfiSegmentationModule import SelfiSegmentation
import os
import mediapipe as mp
import numpy as np

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 60)
segmentation = SelfiSegmentation()

while True:
    success, bg = cap.read()

    frame = cv2.flip(frame, 1)
    
    bgOut = segmentation.removeBG(bg, (0, 0, 0))

    cv2.imshow("Background test", bgOut)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()