import pygame # type: ignore
import cv2
import mediapipe as mp
def set_fullscreen():
    screen_width = 1000
    screen_height = 750

    return pygame.display.set_mode((screen_width, screen_height)) 

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils


def init_camera():
    return cv2.VideoCapture(0)


def process_frame(frame, hands):
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)
    return frame, result


def get_finger_states(lm):
    thumb_up = lm[4].x < lm[3].x
    index_up = lm[8].y < lm[6].y
    middle_up = lm[12].y < lm[10].y
    ring_up = lm[16].y < lm[14].y
    pinky_up = lm[20].y < lm[18].y

    return thumb_up, index_up, middle_up, ring_up, pinky_up


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
        cv2.putText(frame, text, (50, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)


def run_hand_tracker():
    cap = init_camera()

    with mp_hands.Hands() as hands:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame, result = process_frame(frame, hands)

            if result.multi_hand_landmarks:
                for hand_landmarks in result.multi_hand_landmarks:
                    mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    lm = hand_landmarks.landmark
                    states = get_finger_states(lm)

                    detect_gesture(frame, states)

                    print(lm[8].x, lm[8].y)

            cv2.imshow("Hand Tracking", frame)

            if cv2.waitKey(1) & 0xFF == 27:
                break

    cap.release()
    cv2.destroyAllWindows()

pygame.init() # initialization

screen = set_fullscreen()
pygame.display.set_caption("Dont Touch My Lovelove") # title

# exiting the program
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    
    run_hand_tracker()

    pygame.display.update() # displays changes

pygame.quit()

