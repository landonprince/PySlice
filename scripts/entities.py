import math
import random
import pygame

from scripts.particle import Particle
from scripts.spark import Spark


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.initialize_entity(game, e_type, pos, size)
        self.set_action('idle')

    def initialize_entity(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0.0, 0.0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        self.last_movement = [0, 0]

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    def update(self, tilemap, movement=(0, 0)):
        self.handle_collisions(tilemap, movement)
        self.apply_gravity()
        self.animation.update()

    def handle_collisions(self, tilemap, movement):
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])
        self.pos[0] += frame_movement[0]
        self.check_horizontal_collisions(tilemap, frame_movement)
        self.pos[1] += frame_movement[1]
        self.check_vertical_collisions(tilemap, frame_movement)
        self.update_flip_state(movement)
        self.last_movement = movement

    def check_horizontal_collisions(self, tilemap, frame_movement):
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                self.pos[0] = entity_rect.x

    def check_vertical_collisions(self, tilemap, frame_movement):
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                self.pos[1] = entity_rect.y

    def update_flip_state(self, movement):
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

    def apply_gravity(self):
        self.velocity[1] = min(5.0, self.velocity[1] + 0.2)
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)
        self.walking = 0
        self.weapon = random.choice(['gun', 'rifle', 'shotgun'])

    def update(self, tilemap, movement=(0, 0)):
        movement = self.update_behavior(tilemap, movement)
        super().update(tilemap, movement)
        self.update_action(movement)
        return self.handle_collision_with_player()

    def update_behavior(self, tilemap, movement):
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if self.collisions['right'] or self.collisions['left']:
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)
            self.shoot_projectile()
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)
        return movement

    import random

    def shoot_projectile(self):
        if self.walking:
            return

        dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
        if abs(dis[1]) >= 16:
            return

        projectiles_to_add = self.create_projectiles(dis)

        for projectile in projectiles_to_add:
            self.game.projectiles.append(projectile)
            self.add_sparks(projectile[0])

    def create_projectiles(self, dis):
        projectiles_to_add = []
        if self.flip and dis[0] < 0:
            if self.weapon == 'gun':
                self.game.sfx['shoot'].play()
                projectiles_to_add.append([[self.rect().centerx - 7, self.rect().centery],
                                           [-1.5, 0], 0, 'gun', 0, 0])
            elif self.weapon == 'shotgun':
                self.game.sfx['shotgun'].play()
                projectiles_to_add.extend(self.create_shotgun_projectiles(-1.5))
            elif self.weapon == 'rifle':
                projectiles_to_add.extend(self.create_rifle_projectiles(-1.5))
        elif not self.flip and dis[0] > 0:
            if self.weapon == 'gun':
                self.game.sfx['shoot'].play()
                projectiles_to_add.append([[self.rect().centerx + 7, self.rect().centery],
                                           [1.5, 0], 0, 'gun', 0, 0])
            elif self.weapon == 'shotgun':
                self.game.sfx['shotgun'].play()
                projectiles_to_add.extend(self.create_shotgun_projectiles(1.5))
            elif self.weapon == 'rifle':
                projectiles_to_add.extend(self.create_rifle_projectiles(1.5))
        return projectiles_to_add

    def create_shotgun_projectiles(self, x_velocity):
        if self.flip:
            return [[[self.rect().centerx - 20, self.rect().centery],
                     [x_velocity * random.uniform(1.2, 1.5), spread], 0, 'shotgun', 0, 0]
                    for spread in [-0.15, -0.075, 0, 0.075, 0.15]]
        else:
            return [[[self.rect().centerx + 20, self.rect().centery],
                     [x_velocity * random.uniform(1.2, 1.5), spread], 0, 'shotgun', 0, 0]
                    for spread in [-0.15, -0.075, 0, 0.075, 0.15]]

    def create_rifle_projectiles(self, x_velocity):
        projectiles = []
        for i in range(3):
            angle_offset = random.uniform(-0.2, 0.2)
            if self.flip:
                projectiles.append(
                    [[self.rect().centerx - 20, self.rect().centery],
                     [x_velocity, angle_offset], i * 10, 'rifle', 1, i * 5])
            else:
                projectiles.append(
                    [[self.rect().centerx + 20, self.rect().centery],
                     [x_velocity, angle_offset], i * 10, 'rifle', 1,
                     i * 5])
        return projectiles

    def add_sparks(self, position):
        for _ in range(4):
            self.game.sparks.append(
                Spark(position, random.random() - 0.5 + (math.pi if self.flip else 0), 2 + random.random()))

    def update_action(self, movement):
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

    def handle_collision_with_player(self):
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.game.screenshake = max(16, self.game.screenshake)
                self.game.sfx['hit'].play()
                self.game.particles.append(Particle(self.game, 'blood', self.rect().center))
                self.create_collision_effects()

                for i in range(1):
                    self.game.particles.append(Particle(self.game, 'coin', self.rect().center))
                return True
        return False

    def create_collision_effects(self):
        for i in range(30):
            angle = random.random() * math.pi * 2
            speed = random.random() * 5
            self.game.sparks.append(Spark(self.rect().center, angle, 2 + random.random()))
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center,
                                                velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                                          math.sin(angle + math.pi) * speed * 0.5],
                                                frame=random.randint(0, 7)))
        self.game.sparks.append(Spark(self.rect().center, 0, 5 + random.random()))
        self.game.sparks.append(Spark(self.rect().center, math.pi, 5 + random.random()))

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)
        self.render_gun(surf, offset)

    def render_gun(self, surf, offset):
        if self.weapon == 'gun':
            if self.flip:
                surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False),
                          (self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0],
                           self.rect().centery - offset[1]))
            else:
                surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0],
                                                    self.rect().centery - offset[1]))
        elif self.weapon == 'shotgun':
            if self.flip:
                surf.blit(pygame.transform.flip(self.game.assets['shotgun'], True, False),
                          (self.rect().centerx + 2 - self.game.assets['shotgun'].get_width() - offset[0],
                           self.rect().centery - 5 - offset[1]))
            else:
                surf.blit(self.game.assets['shotgun'], (self.rect().centerx - 2 - offset[0],
                                                        self.rect().centery - 5 - offset[1]))

        elif self.weapon == 'rifle':
            if self.flip:
                surf.blit(pygame.transform.flip(self.game.assets['rifle'], True, False),
                          (self.rect().centerx + 2 - self.game.assets['rifle'].get_width() - offset[0],
                           self.rect().centery - 5 - offset[1]))
            else:
                surf.blit(self.game.assets['rifle'], (self.rect().centerx - 2 - offset[0],
                                                      self.rect().centery - 5 - offset[1]))


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.initialize_player()

    def initialize_player(self):
        self.air_time = 0
        self.jumps = 1
        self.wall_slide = False
        self.dashing = 0
        self.speed = 1.5

    def update(self, tilemap, movement=(0, 0)):
        movement = (movement[0] * self.speed, movement[1])
        super().update(tilemap, movement)
        self.update_air_time()
        self.handle_landing()
        self.handle_wall_slide()
        self.update_action()
        self.handle_dash()
        self.apply_friction()

    def update_air_time(self):
        if not self.wall_slide:
            self.air_time += 1
        if self.air_time > 120 and not self.game.dead:
            self.game.screenshake = max(16, self.game.screenshake)
            self.game.dead += 1

    def handle_landing(self):
        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1

    def handle_wall_slide(self):
        self.wall_slide = False
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            self.flip = not self.collisions['right']
            self.set_action('wall_slide')

    def update_action(self):
        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif self.last_movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')

    def handle_dash(self):
        if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(
                    Particle(self.game, 'particle', self.rect().center, velocity=pvelocity,
                             frame=random.randint(0, 7)))

        self.update_dash_state()

        if abs(self.dashing) > 50:
            self.game.screenshake = max(16, self.game.screenshake)
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1

            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity,
                                                frame=random.randint(0, 7)))

    def update_dash_state(self):
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)

    def apply_friction(self):
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)
            self.render_katana(surf, offset)

    def render_katana(self, surf, offset):
        katana_image = pygame.transform.rotate(self.game.assets['katana'], -20)

        if self.flip:
            katana_image = pygame.transform.flip(katana_image, True, False)
            surf.blit(katana_image,
                      (self.rect().centerx - katana_image.get_width() + 8 - offset[0],
                       self.rect().centery - 20 - offset[1]))
        else:
            surf.blit(katana_image, (self.rect().centerx - 8 - offset[0], self.rect().centery - 20 - offset[1]))

    def jump(self):
        if self.wall_slide:
            return self.wall_jump()
        elif self.jumps:
            return self.normal_jump()
        return False

    def wall_jump(self):
        if self.flip and self.last_movement[0] < 0:
            self.velocity[0] = 2.7
            self.velocity[1] = -4.0
        elif not self.flip and self.last_movement[0] > 0:
            self.velocity[0] = -2.7
            self.velocity[1] = -4.0
        else:
            return False
        self.air_time = 5
        self.jumps = max(0, self.jumps - 1)
        return True

    def normal_jump(self):
        self.velocity[1] = -4
        self.jumps -= 1
        self.air_time = 5
        return True

    def dash(self):
        if not self.dashing:
            self.game.sfx['dash'].play()
            self.dashing = -60 if self.flip else 60
