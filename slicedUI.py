import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pygame
import random
import math
from PIL import Image

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
rect_y = height - 1   # 50px from bottom
rect_width = width
rect_height = 1
ground_rect = pygame.Rect(rect_x, rect_y, rect_width, rect_height)

#health
health = 3

#for game over timer
game_over_time = None

#score
score = 0

#Game Initialization
pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Siopao, Siomai, Suman Slasher")
clock = pygame.time.Clock()
spawn_timer = 0
spawn_interval = 500 #2000 before # milliseconds 
font = pygame.font.SysFont("Arial", 25)

def now_ms():
    return pygame.time.get_ticks()

base_options = python.BaseOptions(model_asset_path="hand_landmarker.task")
options = vision.HandLandmarkerOptions(base_options=base_options, 
                                      num_hands=2, 
                                      min_hand_detection_confidence=0.5,
                                      min_hand_presence_confidence=0.8,
                                      min_tracking_confidence=0.6)

detector = vision.HandLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

#GIF animation
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

#GIF images
siopao_frames = load_gif_frames("Siopao.gif", (100, 100))
siomai_frames = load_gif_frames("Siomai.gif", (100, 100))
suman_frames = load_gif_frames("Suman.gif", (100, 100))
chili_frames = load_gif_frames("Chili.gif", (100, 100))

#game exit icon
gameexitbttn_img = pygame.image.load("Gameexit.png").convert_alpha()
gameexitbttn_img = pygame.transform.scale(gameexitbttn_img, (50, 50))
gameexitbttn_hover_img = pygame.image.load("Gameexit1.png").convert_alpha()
gameexitbttn_hover_img = pygame.transform.scale(gameexitbttn_hover_img, (50, 50))
gameexitbttn_rect = gameexitbttn_img.get_rect(topleft=(1, 1))

#health icon
healthicon_img = pygame.image.load("Health.png")
healthicon_img = pygame.transform.scale(healthicon_img, (50, 50))
healthicon_rect = healthicon_img.get_rect(topright=(width, 0))

healthicon1_img = pygame.image.load("Health.png")
healthicon1_img = pygame.transform.scale(healthicon1_img, (50, 50))
healthicon1_rect = healthicon1_img.get_rect(topright=(width - 50, 0))

healthicon2_img = pygame.image.load("Health.png")
healthicon2_img = pygame.transform.scale(healthicon2_img, (50, 50))
healthicon2_rect = healthicon2_img.get_rect(topright=(width - 100, 0))

#incase needed extra life
#healthicon3_img = pygame.image.load("Health.png")
#healthicon3_img = pygame.transform.scale(healthicon3_img, (50, 50))
#healthicon3_rect = healthicon3_img.get_rect(topright=(width - 150, 0))

#healthicon4_img = pygame.image.load("Health.png")
#healthicon4_img = pygame.transform.scale(healthicon4_img, (50, 50))
#healthicon4_rect = healthicon4_img.get_rect(topright=(width - 200, 0))

#health damage icon
damageicon_img = pygame.image.load("Damage.png")
damageicon_img = pygame.transform.scale(damageicon_img, (50, 50))
damageicon_rect = damageicon_img.get_rect(topright=(width, 0))

damageicon1_img = pygame.image.load("Damage.png")
damageicon1_img = pygame.transform.scale(damageicon1_img, (50, 50))
damageicon1_rect = damageicon1_img.get_rect(topright=(width - 50, 0))

damageicon2_img = pygame.image.load("Damage.png")
damageicon2_img = pygame.transform.scale(damageicon2_img, (50, 50))
damageicon2_rect = damageicon2_img.get_rect(topright=(width - 100, 0))

#sliced GIF animation
chili_sliced = load_gif_frames("Chili slashed.gif", (100, 100))
food_sliced = load_gif_frames("Food sliced.gif", (100, 100))

class Food:
    def __init__(self, frames, foodtype):
        self.radius = random.randint(22, 36)
        #self.color = color

        #spawn near bottom
        self.x = random.randint(80, width - 80)
        self.y = ground_rect.top - self.radius - 10

        #upward launch
        self.vx = random.uniform(-3.5, 3.5)
        self.vy = -random.uniform(intial_vy_min, intial_vy_max)

        #self.image = amongus_img   # 👈 ADD THIS

        #GIF TEST
        #self.frames = amongus_frames
        self.frames = frames
        self.frame_index = 0
        self.animation_speed = 0.25

        self.image = self.frames[0] #GIF

        self.rect = self.image.get_rect(center=(self.x, self.y)) #GIF

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
        #self.rect.center = (self.x, self.y) # keep image aligned
        self.rect = self.image.get_rect(center=(self.x, self.y)) #GIF
        self.angle = (self.angle + self.angle_speed) % 360

        #GIF
        self.frame_index += self.animation_speed

        if self.frame_index >= len(self.frames):
            self.frame_index = 0

        self.image = self.frames[int(self.frame_index)]

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

# configs before main loop
current_index_tips = []  # store current frame index tips for both hands
prev_index_tips = []     # for single hand swipe
running = True

#GIF loop spawn
foods = []
effects = [] #when chili was sliced

for count in range(5):

    if count % 4 == 0:
        foods.append(Food(chili_frames, "chili"))

    elif count % 3 == 0:
        foods.append(Food(suman_frames, "suman"))

    elif count % 2 == 0:
        foods.append(Food(siomai_frames, "siomai"))

    else:
        foods.append(Food(siopao_frames, "siopao"))

#for sliced anaimation
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

# Main Game Loop
while running:
    dt = clock.tick(fps)

    success, frame = cap.read()
    if not success:
        break

    #sliced animation
    for effect in effects[:]:
        effect.update()

        #sliced animation
        if effect.finished:
            effects.remove(effect)

    #gameexit button
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if gameexitbttn_rect.collidepoint(pygame.mouse.get_pos()):
                running = False
    
    #gameexit button hover
    mouse_pos_play = pygame.mouse.get_pos()

    if gameexitbttn_rect.collidepoint(mouse_pos_play):
        current_img = gameexitbttn_hover_img
    else:
        current_img = gameexitbttn_img
        
    frame = cv2.flip(frame, 1)
    h,w,_ = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb)
    result = detector.detect(mp_image)

    # Get current frame index tips
    current_index_tips.clear()
    
    if result.hand_landmarks:
        for hand_landmarks in result.hand_landmarks:
            index_tip = hand_landmarks[8]
            x, y = int(index_tip.x * w), int(index_tip.y * h)
            cv2.circle(frame, (x, y), 10, (0, 255, 0), -2)  # Green for index tips
            current_index_tips.append((x, y))

    # slicing logic inside loop
    if len(current_index_tips) >= 1: 
        # Case 1: One hand detected - slice from previous position to current
        if len(current_index_tips) == 1 and len(prev_index_tips) >= 1:
            p1 = prev_index_tips[0]  # Previous position
            p2 = current_index_tips[0]  # Current position
            
            # Only slice if there's accurate movement
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            distance = math.hypot(dx, dy)

            MAX_SWIPE = 100

            #Wayne change
            MIN_SWIPE = 45

            if MIN_SWIPE < distance < MAX_SWIPE:# Wayne change
                scale = MAX_SWIPE / distance
                p2 = (int(p1[0] + dx * scale), int(p1[1] + dy * scale))
                for f in foods:

                    if not f.sliced and segment_circle_intersection(p1, p2, (f.x, f.y), f.radius):
                        f.sliced = True

                        #slice animation
                        if f.foodtype == "chili":
                            effects.append(Effect(f.x, f.y, chili_sliced))
                            health -= 1

                        if f.foodtype == "siopao":
                            effects.append(Effect(f.x, f.y, food_sliced))
                            score += 1

                        if f.foodtype == "siomai":
                            effects.append(Effect(f.x, f.y, food_sliced))
                            score += 1
                        
                        if f.foodtype == "suman":
                            effects.append(Effect(f.x, f.y, food_sliced))
                            score += 1

                # Draw swipe trail
                cv2.line(frame, p1, p2, (255, 0, 0), 4)
    
    # Update previous positions for next frame
    prev_index_tips = current_index_tips.copy()

    #GIF involve wayne
    spawn_timer += dt

    if spawn_timer >= spawn_interval:
    
        if len(foods) < max_food:

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
    
    for food in foods[:]:  # copy of list
        food.update()

    # Remove foods that fell off screen
    foods = [f for f in foods if not f.sliced and f.y < height + 100]

    foods = [food for food in foods
         if not pygame.Rect(
             food.x - food.radius,
             food.y - food.radius,
             food.radius * 2,
             food.radius * 2
         ).colliderect(ground_rect)]


    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
    frame = pygame.transform.scale(frame, (width, height)) 

    screen.blit(frame, (0, 0))
    screen.blit(current_img, gameexitbttn_rect) #button game exit round
    pygame.draw.rect(screen, (255,0,0), gameexitbttn_rect, 2) #button game exit round

    #health condition display
    if health == 3:
        screen.blit(healthicon_img, healthicon_rect)#health icon
        screen.blit(healthicon1_img, healthicon1_rect)#health icon
        screen.blit(healthicon2_img, healthicon2_rect)#health icon
        
    if health == 2:
        screen.blit(damageicon_img, damageicon_rect)#damage icon
        screen.blit(healthicon1_img, healthicon1_rect)#health icon
        screen.blit(healthicon2_img, healthicon2_rect)#health icon

    if health == 1:
        screen.blit(damageicon_img, damageicon_rect)#damage icon
        screen.blit(damageicon1_img, damageicon1_rect)#damage icon
        screen.blit(healthicon2_img, healthicon2_rect)#health icon

    if health == 0:
        screen.blit(damageicon_img, damageicon_rect)
        screen.blit(damageicon1_img, damageicon1_rect)
        screen.blit(damageicon2_img, damageicon2_rect)

        #gameover
        if game_over_time is None:
            game_over_time = pygame.time.get_ticks()
        
        #3seconds before the program closed
        if pygame.time.get_ticks() - game_over_time >= 3000:
            running = False

    #screen.blit(healthicon3_img, healthicon3_rect)#health icon
    #screen.blit(healthicon4_img, healthicon4_rect)#health icon

    #draw ground
    pygame.draw.rect(screen, (0, 200, 0), ground_rect)

    for f in foods:
        if not f.sliced:
            screen.blit(f.image, f.rect)
    
    #sliced animation chili
    for effect in effects:
        effect.draw(screen)

    pygame.display.update()

cap.release()
cv2.destroyAllWindows()
pygame.quit()