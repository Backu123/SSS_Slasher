import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pygame
import random

#Configs
width, height = 900, 600
fps = 60
food_spawn_interval_ms = 900

gravity = 0.4
intial_vy_min, intial_vy_max = 12, 18

#Implement swipe longevity here
#Particle system for swipe longevity or effects

#max food items on screen at once, to prevent lag
max_food = 9

#Game Initialization
pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Siopao, Siomai, Suman Slasher")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 25)


def now_ms():
    return pygame.time.get_ticks()

base_options = python.BaseOptions(model_asset_path="hand_landmarker.task")
options = vision.HandLandmarkerOptions(base_options=base_options, 
                                      num_hands=2, 
                                      min_hand_detection_confidence=0.8,
                                      min_hand_presence_confidence=0.8,
                                      min_tracking_confidence=0.8)

detector = vision.HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

hand_points = []
foods = []
running = True

while running:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    h,w,_ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb)
    result = detector.detect(mp_image)

    hand_points.clear()

    if result.hand_landmarks:
        for hand in result.hand_landmarks:
            index_tip = hand[8]
            x,y = int(index_tip.x * w), int(index_tip.y * h)
            cv2.circle(frame, (x,y), 10, (255,0,255), -2)
            hand_points.append((x, y))

            if len(hand_points) > 2:
                hand_points.pop(0)

    # slicing logic inside loop
    if len(hand_points) >= 2:
        p1 = hand_points[0]
        p2 = hand_points[1]

        for f in foods:
            if segment_circle_intersection(p1, p2, (f.x, f.y), f.radius):
                f.sliced = True
    
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
    frame = pygame.transform.scale(frame, (width, height))

    screen.blit(frame, (0, 0))

    for f in foods:
        if not f.sliced:
            pygame.draw.circle(screen, (255, 100, 0), (f.x, f.y), f.radius)

    pygame.display.update()
    clock.tick(fps)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
cap.release()
cv2.destroyAllWindows()
pygame.quit()