import pygame
import sys
from config import *

pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Offline Chess")

clock = pygame.time.Clock()

bg = pygame.image.load("Assets/pozadina-1.png")
bg = pygame.transform.scale(bg, (WIDTH, HEIGHT))

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(BLACKY)
    screen.blit(bg, (0,0))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
