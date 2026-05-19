# ================= IMPORTS =================
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pygame
import random
import math
import psycopg2
from PIL import Image

# Database connection
DB_URL = "postgresql://neondb_owner:npg_yAHXZ0iM8ORI@ep-proud-haze-ao93abr3-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()


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
max_food = 5

#food dispawning area
rect_x = 0
rect_y = height - 1
rect_width = width
rect_height = 1
ground_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)

# Game timer (increment)
game_timer = 0

#health
health = 3

#for game over timer
game_over_time = None

#score
score = 0

#score background
score_img = pygame.image.load("Points, Time.png")
score_img = pygame.transform.scale(score_img, (200, 50))

# Trail effect variables
trail_length = 12
trail_points = []

# improved swipe detection
min_distance = 25
prev_tip = None
slice_active = False

# Pygame setup
pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Siopao, Siomai, Suman Slasher")
clock = pygame.time.Clock()
spawn_timer = 0
spawn_interval = 250
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

# Database

def init_db():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leaderboards (
            id SERIAL PRIMARY KEY,
            username TEXT,
            score INT,
            game_time TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

init_db()

def save_score(username, score, game_time):
    cursor.execute("""
        INSERT INTO leaderboards (username, score, game_time)
        VALUES (%s, %s, %s)
    """, (username, score, game_time))

    conn.commit()

def get_leaderboard():
    cursor.execute("""
        SELECT username, score, game_time, created_at
        FROM leaderboards
        ORDER BY score DESC, created_at ASC
        LIMIT 10
    """)

    return cursor.fetchall()


# GIF Animation
def load_gif_frames(path, scale_size=None):

    gif = Image.open(path)

    frames = []

    try:
        while True:

            frame = gif.copy().convert("RGBA")

            if scale_size:
                frame = frame.resize(scale_size)

            pygame_image = pygame.image.fromstring(
                frame.tobytes(),
                frame.size,
                frame.mode
            )

            frames.append(pygame_image)

            gif.seek(gif.tell() + 1)

    except EOFError:
        pass

    return frames

# GIF Images
siopao_frames = load_gif_frames("Siopao.gif", (100, 100))
siomai_frames = load_gif_frames("Siomai.gif", (100, 100))
suman_frames = load_gif_frames("Suman.gif", (100, 100))
chili_frames = load_gif_frames("Chili.gif", (100, 100))

# Game exit button
gameexitbttn_img = pygame.image.load("Gameexit.png").convert_alpha()
gameexitbttn_img = pygame.transform.scale(gameexitbttn_img, (50, 50))

gameexitbttn_hover_img = pygame.image.load("Gameexit1.png").convert_alpha()
gameexitbttn_hover_img = pygame.transform.scale(gameexitbttn_hover_img, (50, 50))
gameexitbttn_rect = gameexitbttn_img.get_rect(topleft=(1, 1))

# Health icons
healthicon_img = pygame.image.load("Health.png")
healthicon_img = pygame.transform.scale(healthicon_img, (50, 50))
healthicon_rect = healthicon_img.get_rect(topright=(width, 0))

healthicon1_img = pygame.image.load("Health.png")
healthicon1_img = pygame.transform.scale(healthicon1_img, (50, 50))
healthicon1_rect = healthicon1_img.get_rect(topright=(width - 50, 0))

healthicon2_img = pygame.image.load("Health.png")
healthicon2_img = pygame.transform.scale(healthicon2_img, (50, 50))
healthicon2_rect = healthicon2_img.get_rect(topright=(width - 100, 0))

# Damage icons
damageicon_img = pygame.image.load("Damage.png")
damageicon_img = pygame.transform.scale(damageicon_img, (50, 50))
damageicon_rect = damageicon_img.get_rect(topright=(width, 0))

damageicon1_img = pygame.image.load("Damage.png")
damageicon1_img = pygame.transform.scale(damageicon1_img, (50, 50))
damageicon1_rect = damageicon1_img.get_rect(topright=(width - 50, 0))

damageicon2_img = pygame.image.load("Damage.png")
damageicon2_img = pygame.transform.scale(damageicon2_img, (50, 50))
damageicon2_rect = damageicon2_img.get_rect(topright=(width - 100, 0))

# Sliced GIF Animations
chili_sliced = load_gif_frames("Chili slashed.gif", (100, 100))
food_sliced = load_gif_frames("Food sliced.gif", (100, 100))

# Food Class
class Food:

    def __init__(self, frames, foodtype):

        self.radius = random.randint(22, 36)

        #spawn near bottom
        self.x = random.randint(80, width - 80)
        self.y = ground_rect.top - self.radius - 10

        #upward launch
        self.vx = random.uniform(-3.5, 3.5)
        self.vy = -random.uniform(intial_vy_min, intial_vy_max)

        #GIF TEST
        self.frames = frames
        self.frame_index = 0
        self.animation_speed = 0.25

        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(self.x, self.y))

        self.spawned_at = now_ms()
        self.sliced = False

        #for visual rotation
        self.angle = random.uniform(0, 360)
        self.angle_speed = random.uniform(-8, 8)

        #foodtype sliced animation
        self.foodtype = foodtype

    def update(self):

        self.vy += gravity
        self.x += self.vx
        self.y += self.vy

        self.rect = self.image.get_rect(center=(self.x, self.y))
        self.angle = (self.angle + self.angle_speed) % 360

        #GIF
        self.frame_index += self.animation_speed

        if self.frame_index >= len(self.frames):
            self.frame_index = 0

        self.image = self.frames[int(self.frame_index)]

def point_circle_collision(point, circle_center, radius):
    return math.hypot(point[0] - circle_center[0], point[1] - circle_center[1]) <= radius

# Collision detection between a line segment and a circle
def segment_circle_intersection(p1, p2, center, radius):

    x1, y1 = p1
    x2, y2 = p2
    cx, cy = center

    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return False

    t = ((cx - x1) * dx + (cy - y1) * dy) / (dx * dx + dy * dy)

    t = max(0, min(1, t))

    nearest_x = x1 + t * dx
    nearest_y = y1 + t * dy

    distance = math.hypot(cx - nearest_x, cy - nearest_y)

    return distance <= radius

# Effect class for sliced animation
class Effect:

    def __init__(self, x, y, frames):

        self.x = x
        self.y = y

        self.frames = frames
        self.frame_index = 0
        self.animation_speed = 0.35

        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=(x, y))

        self.finished = False

    def update(self):

        self.frame_index += self.animation_speed

        if self.frame_index >= len(self.frames):
            self.finished = True
            return

        self.image = self.frames[int(self.frame_index)]

    def draw(self, screen):
        screen.blit(self.image, self.rect)

# Main Game Variables
current_index_tips = []
prev_index_tips = []

running = True

foods = []
effects = []

#about screen
def about_screen():

    # Load scroll frames
    scroll_frames = [

        pygame.transform.scale(
            pygame.image.load("Scroll1.png").convert_alpha(),
            (1200, 700)
        ),

        pygame.transform.scale(
            pygame.image.load("Scroll2.png").convert_alpha(),
            (1200, 700)
        ),

        pygame.transform.scale(
            pygame.image.load("Scroll3.png").convert_alpha(),
            (1200, 700)
        )
    ]

    # About text
    pages = [
    [
        " About ",
        "SSS Slasher is a fast-paced arcade slicing game where players use their hands as blades",
        "through camera-based hand detection. Slash flying foods, score points, and avoid chilis",
        "in this computer vision-powered game."
    ],

    [
        " How to play ",
        "The goal of the game is to slice as much food and earn points by doing so.",
        "Slicing three chilis will eliminate the player."
    ],

    [
        " How it works ",
        "- The player will be showing his hand to the camera. It will act as blade in the",
        "game and the player can use it by moving it in a slicing motion to the food.",
        "- Foods such as siomai, siopao and suman will start popping up from the bottom of the screen.",
        "- The player must slice as much food and avoid chilis.",
        "- The player won't lose a health if a food is not sliced, only when a chili is sliced.",
        "- Score as much points and avoid chilis!"
    ],

    [
        " Developers ",
        "Audije, Timothy Rayjell",
        "Bermillo, Franzen Edhrian Kirby",
        "Capistrano, John Wayne",
        "Cristobal, Leilanie Alaine",
        "Teves, Jamaica"
    ]
    ]

    # Animation variables
    current_page = 0

    current_frame = 0
    frame_timer = 0
    frame_delay = 12

    animation_done = False

    # Fonts
    title_font = pygame.font.SysFont("Times New Roman", 48)
    text_font = pygame.font.SysFont("Arial", 28)

    #next scroll page button
    #scroll page navigation
    nextscrollbttn_img = pygame.image.load("Next.png").convert_alpha()
    nextscrollbttn_img = pygame.transform.scale(nextscrollbttn_img, (50, 50))

    nextscrollbttn_hover_img = pygame.image.load("Next1.png").convert_alpha()
    nextscrollbttn_hover_img = pygame.transform.scale(nextscrollbttn_hover_img, (50, 50))

    nextscrollbttn_rect = nextscrollbttn_img.get_rect(center= (680, 700))

    #back scroll page button
    backscrollbttn_img = pygame.image.load("Back.png").convert_alpha()
    backscrollbttn_img = pygame.transform.scale(backscrollbttn_img, (50, 50))

    backscrollbttn_hover_img = pygame.image.load("Back1.png").convert_alpha()
    backscrollbttn_hover_img = pygame.transform.scale(backscrollbttn_hover_img, (50, 50))

    backscrollbttn_rect = backscrollbttn_img.get_rect(center= (600, 700))

     # FIX: initialize current images (IMPORTANT)
    current_next_img = nextscrollbttn_img
    current_back_img = backscrollbttn_img
    current_exit_img = gameexitbttn_img

    while True:

        clock.tick(60)

        #game exit button
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN:

                if gameexitbttn_rect.collidepoint(pygame.mouse.get_pos()):
                    return
                
                if nextscrollbttn_rect.collidepoint(
                    pygame.mouse.get_pos()
                ):

                    if current_page < len(pages) - 1:

                        # Go next page
                        current_page += 1

                        # Restart animation
                        current_frame = 0
                        frame_timer = 0
                        animation_done = False

                if backscrollbttn_rect.collidepoint(
                    pygame.mouse.get_pos()
                ):

                    if current_page > 0:

                        # Go next page
                        current_page -= 1

                        # Restart animation
                        current_frame = 0
                        frame_timer = 0
                        animation_done = False


        #game exit button hover
        mouse_pos = pygame.mouse.get_pos()

        if gameexitbttn_rect.collidepoint(mouse_pos):
            current_exit_img = gameexitbttn_hover_img
        else:
            current_exit_img = gameexitbttn_img

        if nextscrollbttn_rect.collidepoint(mouse_pos):
            current_next_img = nextscrollbttn_hover_img
        else:
            current_next_img = nextscrollbttn_img

        if backscrollbttn_rect.collidepoint(mouse_pos):
            current_back_img = backscrollbttn_hover_img
        else:
            current_back_img = backscrollbttn_img

        # camera
        success, frame = cap.read()

        if not success:
            break

        frame = cv2.flip(frame, 1)

        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        frame = pygame.surfarray.make_surface(
            frame.swapaxes(0, 1)
        )

        frame = pygame.transform.scale(
            frame,
            (width, height)
        )

        # draw camera
        screen.blit(frame, (0, 0))

        # Dark overlay
        overlay = pygame.Surface((width, height))
        overlay.set_alpha(120)
        overlay.fill((0, 0, 0))

        screen.blit(overlay, (0, 0))

        # scroll animation
        if not animation_done:

            frame_timer += 1

            if frame_timer >= frame_delay:

                current_frame += 1

                frame_timer = 0

                if current_frame >= len(scroll_frames):

                    current_frame = len(scroll_frames) - 1

                    animation_done = True

        # Draw current frame
        scroll_img = scroll_frames[current_frame]

        scroll_rect = scroll_img.get_rect(
            center=(width // 2, height // 2)
        )

        screen.blit(scroll_img, scroll_rect)

        # ================= SHOW TEXT =================
        if animation_done:

            y = 190

            for line in pages[current_page]:

                if line in [
                    " About ",
                    " How to play ",
                    " How it works ",
                    " Developers "
                ]:
                    text_surface = title_font.render(
                        line,
                        True,
                        (70, 35, 10)
                    )

                else:

                    text_surface = text_font.render(
                        line,
                        True,
                        (70, 35, 10)
                    )

                text_rect = text_surface.get_rect(
                    center=(width // 2, y)
                )

                screen.blit(text_surface, text_rect)

                y += 50

        screen.blit(current_exit_img, gameexitbttn_rect)
        if current_page < len(pages) - 1:
            screen.blit(current_next_img, nextscrollbttn_rect)
            #pygame.draw.rect(screen, (255, 0, 0), nextscrollbttn_rect, 2)
            
        if current_page > 0:
            screen.blit(current_back_img, backscrollbttn_rect)
            #pygame.draw.rect(screen, (255, 0, 0), backscrollbttn_rect, 2)
        
        pygame.draw.rect(screen, (255, 0, 0), gameexitbttn_rect, 2)

        pygame.display.update()

def main_menu():
    screen = pygame.display.set_mode((width, height))
    font = pygame.font.SysFont("Arial", 25)

    button_size = 200, 40

    #play button
    playbttn_img = pygame.image.load("Play.png")
    playbttn_img = pygame.transform.scale(playbttn_img, button_size)
    playbttn_hover_img = pygame.image.load("Play1.png")
    playbttn_hover_img = pygame.transform.scale(playbttn_hover_img, button_size)
    playbttn_rect = playbttn_img.get_rect(center=(width // 2, height // 2))

    #about button
    aboutbttn_img = pygame.image.load("About.png")
    aboutbttn_img = pygame.transform.scale(aboutbttn_img, button_size)
    aboutbttn_hover_img = pygame.image.load("About1.png")
    aboutbttn_hover_img = pygame.transform.scale(aboutbttn_hover_img, button_size)
    aboutbttn_rect = aboutbttn_img.get_rect(center=(width // 2, height // 2 + 100))

    #exit button
    exitbttn_img = pygame.image.load("Exit.png")
    exitbttn_img = pygame.transform.scale(exitbttn_img, button_size)
    exitbttn_hover_img = pygame.image.load("Exit1.png")
    exitbttn_hover_img = pygame.transform.scale(exitbttn_hover_img, button_size)
    exitbttn_rect = exitbttn_img.get_rect(center=(width // 2, height // 2 + 200))

    while True:
        clock.tick(60)

        success, frame = cap.read()
        if not success:
            break

        #screen
        frame = cv2.flip(frame, 1)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        frame = pygame.transform.scale(frame, (width, height))
        flipped_frame = frame

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
        
            #play button
            if event.type == pygame.MOUSEBUTTONDOWN:
                if playbttn_rect.collidepoint(pygame.mouse.get_pos()):
                    return
                elif aboutbttn_rect.collidepoint(pygame.mouse.get_pos()):
                    about_screen()
                elif exitbttn_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.quit()
                    exit()

        screen.fill((0, 0, 0))      # optional background color
        screen.blit(flipped_frame, (0, 0))  # camera FIRST layer
        
        #play button hover
        mouse_pos_play = pygame.mouse.get_pos()

        if playbttn_rect.collidepoint(mouse_pos_play):
            current_img = playbttn_hover_img
        else:
            current_img = playbttn_img

        screen.blit(current_img, playbttn_rect)

        #about button hover
        mouse_pos_about = pygame.mouse.get_pos()

        if aboutbttn_rect.collidepoint(mouse_pos_about):
            current_img = aboutbttn_hover_img
        else:
            current_img = aboutbttn_img

        screen.blit(current_img, aboutbttn_rect)

        #exit button hover
        mouse_pos_about = pygame.mouse.get_pos()

        if exitbttn_rect.collidepoint(mouse_pos_about):
            current_img = exitbttn_hover_img
        else:
            current_img = exitbttn_img

        screen.blit(current_img, exitbttn_rect)

        pygame.display.update()

# Main Menu
main_menu()
# Main Game Loop
while running:

    dt = clock.tick(fps)

    # timer seconds 
    game_timer += dt
    total_seconds = game_timer // 1000 # convert milliseconds to seconds
    game_timer_minutes = total_seconds // 60
    game_timer_seconds = total_seconds % 60
    final_time = f"{game_timer_minutes:02.0f}:{game_timer_seconds%60:02.0f}"


    success, frame = cap.read()

    if not success:
        break

    #sliced animation
    for effect in effects[:]:

        effect.update()

        if effect.finished:
            effects.remove(effect)

    #game exit button
    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:

            if gameexitbttn_rect.collidepoint(pygame.mouse.get_pos()):
                game_timer = 0
                health = 3
                score = 0
                print("Returning to Main Menu...")
                print(f"Final Time: {final_time}")
                print(f"Final Score: {score}")
                main_menu()

    #game exit button hover
    mouse_pos_play = pygame.mouse.get_pos()

    if gameexitbttn_rect.collidepoint(mouse_pos_play):
        current_img = gameexitbttn_hover_img
    else:
        current_img = gameexitbttn_img

    # ================= CAMERA =================
    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

    result = detector.detect(mp_image)

    # ================= HAND TRACKING =================
    current_index_tips.clear()
    slice_active = False

    if result.hand_landmarks:
        # Get the largest hand only
        largest_hand = None
        largest_area = 0

        for hand_landmarks in result.hand_landmarks:
            xs = [lm.x for lm in hand_landmarks]
            ys = [lm.y for lm in hand_landmarks]

            hand_width = (max(xs) - min(xs)) * w
            hand_height = (max(ys) - min(ys)) * h

            area = hand_width * hand_height

            if area > largest_area:
                largest_area = area
                largest_hand = hand_landmarks

        # minimum hand size threshold
        MIN_HAND_AREA = 25000

        if largest_hand and largest_area > MIN_HAND_AREA:

            index_tip = largest_hand[8]

            x = int(index_tip.x * w)
            y = int(index_tip.y * h)

            current_index_tips.append((x, y))

            # trail effect
            trail_points.append(((x, y), now_ms()))

            # movement detection
            if prev_tip is not None:
                dist = math.hypot(x - prev_tip[0], y - prev_tip[1])

                if dist >= min_distance and len(trail_points) >= 3:
                    slice_active = True

            prev_tip = (x, y)

            cv2.circle(frame, (x, y), 11, (255, 180, 0), -1)

    # remove old trail points
    trail_points = [
        (point, t)
        for point, t in trail_points
        if now_ms() - t < particle_longevity_ms
    ]

    # keep trail short
    if len(trail_points) > trail_length:
        trail_points = trail_points[-trail_length:]

    # ================= SLICING LOGIC =================
    if len(current_index_tips) >= 1:

        if len(current_index_tips) == 1 and len(prev_index_tips) >= 1:

            p1 = prev_index_tips[0]
            p2 = current_index_tips[0]

            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]

            distance = math.hypot(dx, dy)

            MAX_SWIPE = 100
            MIN_SWIPE = 45

            if health > 0 and slice_active and MIN_SWIPE < distance < MAX_SWIPE:

                scale = MAX_SWIPE / distance
                p2 = (
                    int(p1[0] + dx * scale), int(p1[1] + dy * scale))

                for f in foods:

                    if not f.sliced and segment_circle_intersection(
                        p1,
                        p2,
                        (f.x, f.y),
                        f.radius + 25
                    ):

                        f.sliced = True

                        #slice animation
                        if f.foodtype == "chili":

                            effects.append(
                                Effect(f.x, f.y, chili_sliced)
                            )

                            health -= 1

                        if f.foodtype == "siopao":

                            effects.append(
                                Effect(f.x, f.y, food_sliced)
                            )

                            score += 1

                        if f.foodtype == "siomai":

                            effects.append(
                                Effect(f.x, f.y, food_sliced)
                            )

                            score += 2

                        if f.foodtype == "suman":

                            effects.append(
                                Effect(f.x, f.y, food_sliced)
                            )

                            score += 3

                # cv2.line(frame, p1, p2, (255, 0, 0), 4) 

    # Update previous positions
    prev_index_tips = current_index_tips.copy()

    # ================= FOOD SPAWN =================
    # TO EDIT
    spawn_timer += dt
    if health != 0 and spawn_timer >= spawn_interval and len(foods) < 5:

        if len(foods) <= max_food:

            rand = random.randint(1, 20)

            if rand <= 6:
                foods.append(Food(siopao_frames, "siopao"))

            elif rand <= 12:
                foods.append(Food(siomai_frames, "siomai"))

            elif rand <= 18:
                foods.append(Food(suman_frames, "suman"))

            else:
                foods.append(Food(chili_frames, "chili"))

        spawn_timer = 0

    # ================= FOOD UPDATE =================
    for food in foods[:]:
        food.update()

    # Remove foods that fell off screen
    foods = [
        f for f in foods
        if not f.sliced and f.y < height + 100
    ]

    foods = [
        food for food in foods
        if not pygame.Rect(
            food.x - food.radius,
            food.y - food.radius,
            food.radius * 2,
            food.radius * 2
        ).colliderect(ground_rect)
    ]

    # ================= CONVERT FRAME =================
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    frame = pygame.surfarray.make_surface(
        frame.swapaxes(0, 1)
    )

    frame = pygame.transform.scale(frame, (width, height))

    # ================= DRAW =================
    screen.blit(frame, (0, 0))

    # ================= TRAIL DRAW =================
    if len(trail_points) > 1:

        trail_surface = pygame.Surface((width, height),pygame.SRCALPHA)

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
                int(13 * life_ratio)
            )

            pygame.draw.line(
                trail_surface,
                (0, 180, 255, alpha),
                p1,
                p2,
                thickness
            )

        screen.blit(trail_surface, (0, 0))

    # ================= BUTTON =================
    screen.blit(current_img, gameexitbttn_rect)
    pygame.draw.rect(screen, (255, 0, 0), gameexitbttn_rect, 2)

    # ================= HEALTH DISPLAY =================
    if health == 3:
        screen.blit(healthicon_img, healthicon_rect)
        screen.blit(healthicon1_img, healthicon1_rect)
        screen.blit(healthicon2_img, healthicon2_rect)

    if health == 2:
        screen.blit(damageicon_img, damageicon_rect)
        screen.blit(healthicon1_img, healthicon1_rect)
        screen.blit(healthicon2_img, healthicon2_rect)

    if health == 1:
        screen.blit(damageicon_img, damageicon_rect)
        screen.blit(damageicon1_img, damageicon1_rect)
        screen.blit(healthicon2_img, healthicon2_rect)
    
    #draw ground
    pygame.draw.rect(screen, (0, 200, 0), ground_rect)

    # ================= DRAW FOOD =================
    for f in foods:

        if not f.sliced:

            rotated_image = pygame.transform.rotate(
                f.image,
                f.angle
            )

            rotated_rect = rotated_image.get_rect(
                center=f.rect.center
            )

            screen.blit(rotated_image, rotated_rect)

    # ================= EFFECTS =================
    for effect in effects:
        effect.draw(screen)

    # ================= SCORE =================
    score_text = font.render(
        f"Score: {score}",
        True,
        (255, 0, 0)
    )

    screen.blit(score_img, (100, 5))
    screen.blit(score_text, (120, 15))

    # Timer display
    timer_text = font.render(f"{game_timer_minutes:02.0f}:{game_timer_seconds%60:02.0f}", True, (255, 255, 255))
    screen.blit(timer_text, (screen.get_width() // 2 - timer_text.get_width() // 2, 15))

    if health == 0:

        foods.clear()

        screen.blit(damageicon_img, damageicon_rect)
        screen.blit(damageicon1_img, damageicon1_rect)
        screen.blit(damageicon2_img, damageicon2_rect)

        #gameover
        if game_over_time is None:
            game_over_time = pygame.time.get_ticks()

        #2seconds before going back to main menu
        if pygame.time.get_ticks() - game_over_time >= 2000:
            save_score("John Wayne", score, final_time)
            game_timer = 0
            health = 3
            score = 0
            print("Game Over! Returning to Main Menu...")
            print(f"Final Time: {final_time}")
            print(f"Final Score: {score}")
            main_menu()

        
    pygame.display.update()

# ================= CLEANUP =================
cap.release()
cv2.destroyAllWindows()
pygame.quit()