import random


class Cloud:
    def __init__(self, pos, img, speed, depth):
        # Initialize cloud position, image, speed, and depth
        self.pos = list(pos)
        self.img = img
        self.speed = speed
        self.depth = depth

    def update(self):
        # Update cloud position based on its speed
        self.pos[0] += self.speed

    def render(self, surf, offset=(0, 0)):
        # Calculate the position to render the cloud on the surface
        render_pos = (self.pos[0] - offset[0] * self.depth, self.pos[1] - offset[1] * self.depth)

        # Draw the cloud image on the surface, considering wrapping around screen edges
        surf.blit(self.img, (render_pos[0] % (surf.get_width() + self.img.get_width()) - self.img.get_width(),
                             render_pos[1] % (surf.get_height() + self.img.get_height()) - self.img.get_height()))


class Clouds:
    def __init__(self, cloud_images, count=16):
        # Initialize the clouds list
        self.clouds = []

        # Create and initialize a specified number of cloud objects
        for i in range(count):
            self.clouds.append(Cloud((random.random() * 99999, random.random() * 99999),
                                     random.choice(cloud_images), random.random() * 0.05 + 0.05,
                                     random.random() * 0.6 + 0.2))

        # Sort clouds by depth to ensure correct rendering order
        self.clouds.sort(key=lambda x: x.depth)

    def update(self):
        # Update each cloud in the list
        for cloud in self.clouds:
            cloud.update()

    def render(self, surf, offset=(0, 0)):
        # Render each cloud on the given surface with the specified offset
        for cloud in self.clouds:
            cloud.render(surf, offset=offset)
