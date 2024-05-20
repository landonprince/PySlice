import os
import pygame

# Base path for image assets
BASE_IMG_PATH = 'assets/images/'


def load_image(path):
    # Load a single image, set the colorkey for transparency, and return the image
    img = pygame.image.load(BASE_IMG_PATH + path).convert()
    img.set_colorkey((0, 0, 0))
    return img


def load_images(path):
    # Load multiple images from a directory, sort them, and return a list of images
    images = []
    for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
        images.append(load_image(path + '/' + img_name))
    return images


class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        # Initialize the animation with images, image duration, and looping option
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0

    def copy(self):
        # Return a copy of the animation
        return Animation(self.images, self.img_duration, self.loop)

    def update(self):
        # Update the frame index for the animation
        if self.loop:
            # Loop the animation
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            # Play the animation once
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True

    def img(self):
        # Return the current image for the animation based on the frame index
        return self.images[int(self.frame / self.img_duration)]

