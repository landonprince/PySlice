import random


class Cloud:
    def __init__(self, pos, img, speed, depth):
        # Initialize cloud properties
        self.pos = list(pos)
        self.img = img
        self.speed = speed
        self.depth = depth

    def update(self):
        # Update cloud position based on its speed
        self.pos[0] += self.speed

    def render(self, surf, offset=(0, 0)):
        # Calculate render position with parallax effect based on depth
        render_pos = (self.pos[0] - offset[0] * self.depth, self.pos[1] - offset[1] * self.depth)
        surf.blit(self.img, (render_pos[0] % (surf.get_width() + self.img.get_width()) - self.img.get_width(),
                             render_pos[1] % (surf.get_height() + self.img.get_height()) - self.img.get_height()))


class Clouds:
    def __init__(self, cloud_images, count=16):
        # Initialize a list of clouds
        self.clouds = []

        # Create a specified number of clouds with random properties
        for i in range(count):
            self.clouds.append(Cloud((random.random() * 99999, random.random() * 99999),
                                     random.choice(cloud_images),
                                     random.random() * 0.05 + 0.05, random.random() * 0.6 + 0.2))

        # Sort clouds by depth for proper rendering order
        self.clouds.sort(key=lambda x: x.depth)

    def update(self):
        # Update all clouds
        for cloud in self.clouds:
            cloud.update()

    def render(self, surf, offset=(0, 0)):
        # Render all clouds
        for cloud in self.clouds:
            cloud.render(surf, offset=offset)
