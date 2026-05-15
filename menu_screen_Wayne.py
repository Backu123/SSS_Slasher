import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import pygame
import random
import math
from PIL import Image

#screen size
width, height = 1280, 720

pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Siopao, Siomai, Suman Slasher")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 25)

cap = cv2.VideoCapture(0)

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

running = True

while running:

    clock.tick(60)

    success, frame = cap.read()
    if not success:
        break

    #screen
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    frame = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
    frame = pygame.transform.scale(frame, (width, height)) 

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
        #play button
        if event.type == pygame.MOUSEBUTTONDOWN:
            if playbttn_rect.collidepoint(pygame.mouse.get_pos()):
                print("Clicked!")
        
        #about button
        if event.type == pygame.MOUSEBUTTONDOWN:
            if aboutbttn_rect.collidepoint(pygame.mouse.get_pos()):
                print("About")

        #exit button
        if event.type == pygame.MOUSEBUTTONDOWN:
            if exitbttn_rect.collidepoint(pygame.mouse.get_pos()):
                print("Exit")

    screen.fill((0, 0, 0))      # optional background color
    screen.blit(frame, (0, 0))  # camera FIRST layer
    
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

cap.release()
cv2.destroyAllWindows()
pygame.quit()