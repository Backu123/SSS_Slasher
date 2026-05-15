import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pygame
import random
import math

#Configs
width, height = 1280, 720
fps = 60
food_spawn_interval_ms = 900

gravity = 0.4
intial_vy_min, intial_vy_max = 12, 18

#Implement swipe longevity here
#Particle system for swipe longevity or effects
particle_longevity_ms = 700

#max food items on screen at once, to prevent lag
max_food = 9

#food dispawning area
rect_x = 0
rect_y = height - 50   # 50px from bottom
rect_width = width
rect_height = 50
ground_rect = pygame.Rect(rect_x + 200, rect_y, rect_width, rect_height)

#Game Initialization
pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Siopao, Siomai, Suman Slasher")
clock = pygame.time.Clock()
spawn_timer = 0
spawn_interval = 2000  # milliseconds
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

class Food:
    def __init__(self, color):
        self.radius = random.randint(22, 36)
        self.color = color

        #spawn near bottom
        self.x = random.randint(80, width - 80)
        self.y = ground_rect.top - self.radius - 10

        #upward launch
        self.vx = random.uniform(-3.5, 3.5)
        self.vy = -random.uniform(intial_vy_min, intial_vy_max)

        self.spawned_at = now_ms()
        self.sliced = False

        #for visual rotation
        self.angle = random.uniform(0, 360)
        self.angle_speed = random.uniform(-8, 8)
    
    def update(self):
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy
        self.angle = (self.angle + self.angle_speed) % 360

def segment_circle_intersection(p1, p2, center, radius):
    x1, y1 = p1
    x2, y2 = p2
    cx, cy = center

    dx = x2 - x1
    dy = y2 - y1

    fx = x1 - cx
    fy = y1 - cy

    a = dx*dx + dy*dy
    b = 2 * (fx*dx + fy*dy)
    c = fx*fx + fy*fy - radius*radius

    discriminant = b*b - 4*a*c

    return discriminant >= 0

#configs before main loop
hand_points = []
running = True
foods = [Food((255, 200, 100)) for _ in range(5)]

#Main Game Loop
while running:
    dt = clock.tick(fps)

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
            if not f.sliced and segment_circle_intersection(p1, p2, (f.x, f.y), f.radius):
                f.sliced = True

    spawn_timer += dt
    if spawn_timer >= spawn_interval and len(foods) < 1:
        for _ in range(5):
            foods.append(Food((255, 200, 100)))
        spawn_timer = 0
    
    for food in foods[:]:  # copy of list so we can remove safely
        food.update()

    foods = [f for f in foods if f.y < height + 100]

    # create a rect for the circle (approximation)
    foods_rect = pygame.Rect(food.x - food.radius,
                            food.y - food.radius,
                            food.radius * 2,
                            food.radius * 2)

    # collision check
    if foods_rect.colliderect(ground_rect):
        foods.remove(food)
        continue

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
    frame = pygame.transform.scale(frame, (width, height)) 

    screen.blit(frame, (0, 0))   

    #draw ground
    pygame.draw.rect(screen, (0, 200, 0), ground_rect)

    for f in foods:
        if not f.sliced:
            pygame.draw.circle(screen, f.color, (int(f.x), int(f.y)), f.radius)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False 

    pygame.display.update()

cap.release()
cv2.destroyAllWindows()
pygame.quit()