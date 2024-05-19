import sys
import pygame

pygame.init()

screen = pygame.display.set_mode((640, 480))

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()

    pygame.display.update()
    clock.tick(60)