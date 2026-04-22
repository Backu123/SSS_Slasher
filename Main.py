import pygame  
import cv2
import mediapipe as mp

# Set up the display
def set_fullscreen():
    screen_width = 1000
    screen_height = 750

    return pygame.display.set_mode((screen_width, screen_height)) 

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

# Initialize the webcam
def init_camera():
    return cv2.VideoCapture(0)

# Process the video frame and detect hand landmarks
def process_frame(frame, hands):
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)
    return frame, result

# Determine which fingers are up based on landmark positions
def get_finger_states(lm):
    thumb_up = lm[4].x < lm[3].x
    index_up = lm[8].y < lm[6].y
    middle_up = lm[12].y < lm[10].y
    ring_up = lm[16].y < lm[14].y
    pinky_up = lm[20].y < lm[18].y

    return thumb_up, index_up, middle_up, ring_up, pinky_up

# Detect gestures based on finger states
def detect_gesture(frame, states):
    thumb, index, middle, ring, pinky = states
    fingers_up = sum([index, middle, ring, pinky])

    if index and middle and not ring and not pinky:
        text = "PEACE"
    elif index and not middle and not ring and not pinky:
        text = "Actualey"
    elif thumb and not index and not middle and not ring and not pinky:
        text = "klus"
    elif fingers_up == 4:
        text = "upin"
    elif not any(states):
        text = "lik"
    else:
        text = ""

    if text:
        cv2.putText(frame, text, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

# Convert OpenCV frame to Pygame surface and draw bottom-right
def draw_camera(frame, screen):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    frame = cv2.transpose(frame)

    surface = pygame.surfarray.make_surface(frame)

    surface = pygame.transform.scale(surface, (200, 150))

    screen_width, screen_height = screen.get_size()
    x = screen_width - surface.get_width()
    y = screen_height - surface.get_height()

    screen.blit(surface, (x, y))


pygame.init() # initialization of pygame

screen = set_fullscreen()
pygame.display.set_caption("SSS Slasher") # title

cap = init_camera() # initialize camera
hands = mp_hands.Hands() # initialize hand detection

player = pygame.Rect(100, 100, 50, 50) # create a rectangle object
speed = 8

#FPS variables
clock = pygame.time.Clock()
FPS = 120

# smoother movement variables
smooth_x, smooth_y = player.center

# exiting the program
running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # clear screen
    screen.fill((0, 0, 0))

    # get frame
    ret, frame = cap.read()
    if not ret:
        break

    # process frame
    frame, result = process_frame(frame, hands)

    if result.multi_hand_landmarks:
        for hand_landmarks in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            lm = hand_landmarks.landmark
            states = get_finger_states(lm)

            detect_gesture(frame, states)

            print(lm[8].x, lm[8].y)

            # move using motion of index finger
            target_x = int(lm[8].x * screen.get_width())
            target_y = int(lm[8].y * screen.get_height())

            # smoothing (important for jitter)
            smooth_x += (target_x - smooth_x) * 0.2
            smooth_y += (target_y - smooth_y) * 0.2

            player.center = (int(smooth_x), int(smooth_y))

            pygame.draw.rect(screen, (255, 0, 0), player) # draw the rectangle

            break  # only use first detected hand

    # draw camera in pygame
    draw_camera(frame, screen)

    pygame.display.update() # displays changes

cap.release()
pygame.quit()