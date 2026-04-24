import pygame
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

base_options = python.BaseOptions(model_asset_path="hand_landmarker.task")

options = vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)

detector = vision.HandLandmarker.create_from_options(options)

def set_fullscreen():
    return pygame.display.set_mode((1000, 750))

def init_camera():
    cap = cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    return cap

def draw_camera(frame, screen):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = cv2.transpose(frame)

    surface = pygame.surfarray.make_surface(frame)
    surface = pygame.transform.scale(surface, (250, 150))

    screen_width, screen_height = screen.get_size()
    x = screen_width - surface.get_width()
    y = screen_height - surface.get_height()

    screen.blit(surface, (x, y))

pygame.init()
screen = set_fullscreen()
pygame.display.set_caption("SSS Slasher")

cap = init_camera()

player_left = pygame.Rect(100, 100, 50, 50)
player_right = pygame.Rect(300, 100, 50, 50)

clock = pygame.time.Clock()
FPS = 180

smooth_x, smooth_y = player_left.center
smooth_x2, smooth_y2 = player_right.center

running = True
while running:
    clock.tick(FPS)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))

    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    results = detector.detect(mp_image)

    if results.hand_landmarks:
        for i, hand_landmarks in enumerate(results.hand_landmarks):

            handedness = results.handedness[i][0].category_name 

            index_tip = hand_landmarks[8]

            x = int(index_tip.x * screen.get_width())
            y = int(index_tip.y * screen.get_height())

            cx = int(index_tip.x * w)
            cy = int(index_tip.y * h)

            cv2.circle(frame, (cx, cy), 10, (255, 0, 255), -1)

            if handedness == "Left":
                smooth_x += (x - smooth_x) * 0.2
                smooth_y += (y - smooth_y) * 0.2
                player_left.center = (int(smooth_x), int(smooth_y))
                pygame.draw.rect(screen, (255, 0, 0), player_left)

            elif handedness == "Right":
                smooth_x2 += (x - smooth_x2) * 0.2
                smooth_y2 += (y - smooth_y2) * 0.2
                player_right.center = (int(smooth_x2), int(smooth_y2))
                pygame.draw.rect(screen, (0, 0, 255), player_right)

    draw_camera(frame, screen)
    pygame.display.update()

cap.release()
pygame.quit()