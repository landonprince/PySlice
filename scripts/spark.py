import math
import pygame


class Spark:
    def __init__(self, pos, angle, speed):
        # Initialize spark properties
        self.pos = list(pos)
        self.angle = angle
        self.speed = speed

    def update(self):
        # Update spark position based on angle and speed
        self.pos[0] += math.cos(self.angle) * self.speed
        self.pos[1] += math.sin(self.angle) * self.speed

        # Decrease speed over time
        self.speed = max(0, self.speed - 0.1)
        return not self.speed

    def render(self, surf, offset=(0, 0)):
        # Calculate render points for the spark polygon
        render_points = [
            (self.pos[0] + math.cos(self.angle) * self.speed * 3 - offset[0],
             self.pos[1] + math.sin(self.angle) * self.speed * 3 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[0],
             self.pos[1] + math.sin(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi) * self.speed * 3 - offset[0],
             self.pos[1] + math.sin(self.angle + math.pi) * self.speed * 3 - offset[1]),
            (self.pos[0] + math.cos(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[0],
             self.pos[1] + math.sin(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[1]),
        ]

        # Draw the spark as a polygon
        pygame.draw.polygon(surf, (255, 255, 255), render_points)
