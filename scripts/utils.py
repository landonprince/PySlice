import os
import pygame

# Base path for images
BASE_IMG_PATH = 'assets/images/'


def load_image(path):
    # Load a single image with a specified path
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    return img


def load_images(path):
    # Load multiple images from a directory
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name))
    return images


class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        # Initialize animation properties
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0

    def copy(self):
        # Create a copy of the animation
        return Animation(self.images, self.img_duration, self.loop)

    def update(self):
        # Update the animation frame
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True

    def img(self):
        # Get the current image of the animation
        return self.images[int(self.frame / self.img_duration)]
