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

#Swipe trail config
trail_length = 12
trail_points = []

#Images
amongus_img = pygame.image.load("alive.png")
amongus_img = pygame.transform.scale(amongus_img, (80, 80))

#food dispawning area
rect_x = 0
rect_y = height - 1
rect_width = width
rect_height = 1
ground_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)

#Game Initialization
pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Siopao, Siomai, Suman Slasher")
clock = pygame.time.Clock()
spawn_timer = 0
spawn_interval = 2000
font = pygame.font.SysFont("Arial", 25)

def now_ms():
    return pygame.time.get_ticks()

base_options = python.BaseOptions(model_asset_path="hand_landmarker.task")

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.8,
    min_tracking_confidence=0.6
)

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

        self.image = amongus_img
        self.rect = self.image.get_rect(center=(self.x, self.y))

        self.spawned_at = now_ms()
        self.sliced = False

        #for visual rotation
        self.angle = random.uniform(0, 360)
        self.angle_speed = random.uniform(-8, 8)

    def update(self):
        self.vy += gravity
        self.x += self.vx
        self.y += self.vy
        self.rect.center = (self.x, self.y)
        self.angle = (self.angle + self.angle_speed) % 360

# CORRECTED COLLISION
def segment_circle_intersection(p1, p2, center, radius):

    x1, y1 = p1
    x2, y2 = p2
    cx, cy = center

    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return False

    # projection factor
    t = ((cx - x1) * dx + (cy - y1) * dy) / (dx * dx + dy * dy)

    # clamp to line segment
    t = max(0, min(1, t))

    # closest point on segment
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy

    dist_x = closest_x - cx
    dist_y = closest_y - cy

    distance_squared = dist_x * dist_x + dist_y * dist_y

    return distance_squared <= radius * radius

# configs before main loop
current_index_tips = []
prev_index_tips = []
running = True

foods = [Food((255, 200, 100)) for _ in range(5)]

# Main Game Loop
while running:

    dt = clock.tick(fps)
    distance = 0

    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb
    )

    result = detector.detect(mp_image)

    # Get current frame index tips
    current_index_tips.clear()

    if result.hand_landmarks:

        for hand_landmarks in result.hand_landmarks:

            index_tip = hand_landmarks[8]

            x = int(index_tip.x * w)
            y = int(index_tip.y * h)

            cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)

            current_index_tips.append((x, y))

    # slicing logic inside loop
    if len(current_index_tips) >= 1:

        if len(current_index_tips) == 1 and len(prev_index_tips) >= 1:

            p1 = prev_index_tips[0]
            p2 = current_index_tips[0]

            # Only slice if there's accurate movement
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]

            distance = math.hypot(dx, dy)

            MAX_SWIPE = 100

            if distance > MAX_SWIPE:

                scale = MAX_SWIPE / distance

                p2 = (
                    int(p1[0] + dx * scale),
                    int(p1[1] + dy * scale)
                )

            # Slice only when hand moved enough
            if distance > 25:

                for f in foods:

                    if not f.sliced and segment_circle_intersection(
                        p1,
                        p2,
                        (f.x, f.y),
                        f.radius
                    ):
                        f.sliced = True

                # Add point to swipe trail WITH TIMESTAMP
                trail_points.append((p2, now_ms()))

    # Update previous positions for next frame
    prev_index_tips = current_index_tips.copy()

    # Remove old trail points
    trail_points = [
        (point, t)
        for point, t in trail_points
        if now_ms() - t < particle_longevity_ms
    ]

    # Keep trail length limited
    if len(trail_points) > trail_length:
        trail_points.pop(0)

    spawn_timer += dt

    if spawn_timer >= spawn_interval and len([f for f in foods if not f.sliced]) < 1:

        for _ in range(5):
            foods.append(Food((255, 200, 100)))

        spawn_timer = 0

    for food in foods[:]:
        food.update()

    # Remove foods that fell off screen
    foods = [f for f in foods if f.y < height + 100 and not f.sliced]

    # Ground collision detection
    for food in foods[:]:

        food_rect = pygame.Rect(
            food.x - food.radius,
            food.y - food.radius,
            food.radius * 2,
            food.radius * 2
        )

        if food_rect.colliderect(ground_rect):
            foods.remove(food)
            break

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))

    frame = pygame.transform.scale(frame, (width, height))

    screen.blit(frame, (0, 0))

    # Draw fading slash trail
    if len(trail_points) > 1:

        trail_surface = pygame.Surface(
            (width, height),
            pygame.SRCALPHA
        )

        for i in range(1, len(trail_points)):

            p1, t1 = trail_points[i - 1]
            p2, t2 = trail_points[i]

            age = now_ms() - t2

            life_ratio = max(
                0,
                1 - (age / particle_longevity_ms)
            )

            alpha = int(255 * life_ratio)

            thickness = max(
                1,
                int(8 * life_ratio)
            )

            pygame.draw.line(
                trail_surface,
                (0, 180, 255, alpha),
                p1,
                p2,
                thickness
            )

        screen.blit(trail_surface, (0, 0))

    #draw ground
    pygame.draw.rect(screen, (0, 200, 0), ground_rect)

    for f in foods:

        if not f.sliced:
            screen.blit(f.image, f.rect)

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

    pygame.display.update()

cap.release()
cv2.destroyAllWindows()
pygame.quit()