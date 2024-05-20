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
        self.velocity = [0, 0]
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
        self.update_animation()

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
        self.velocity[1] = min(5, self.velocity[1] + 0.2)
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

    def update_animation(self):
        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, 'enemy', pos, size)
        self.walking = 0

    def update(self, tilemap, movement=(0, 0)):
        movement = self.update_behavior(tilemap, movement)
        super().update(tilemap, movement)
        self.update_action(movement)
        return self.handle_collision_with_player()

    def update_behavior(self, tilemap, movement):
        if self.walking:
            movement = self.handle_walking(tilemap, movement)
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)
        return movement

    def handle_walking(self, tilemap, movement):
        if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
            if self.collisions['right'] or self.collisions['left']:
                self.flip = not self.flip
            else:
                movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
        else:
            self.flip = not self.flip
        self.walking = max(0, self.walking - 1)
        self.shoot_projectiles_if_needed()
        return movement

    def shoot_projectiles_if_needed(self):
        if not self.walking:
            dis = (self.game.player.pos[0] - self.pos[0], self.game.player.pos[1] - self.pos[1])
            if abs(dis[1]) < 16:
                self.shoot_projectile(dis)

    def shoot_projectile(self, dis):
        if self.flip and dis[0] < 0:
            self.shoot_left()
        if not self.flip and dis[0] > 0:
            self.shoot_right()

    def shoot_left(self):
        self.game.sfx['shoot'].play()
        self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
        for i in range(4):
            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5 + math.pi,
                                          2 + random.random()))

    def shoot_right(self):
        self.game.sfx['shoot'].play()
        self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 1.5, 0])
        for i in range(4):
            self.game.sparks.append(Spark(self.game.projectiles[-1][0], random.random() - 0.5, 2 + random.random()))

    def update_action(self, movement):
        if movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

    def handle_collision_with_player(self):
        if abs(self.game.player.dashing) >= 50:
            if self.rect().colliderect(self.game.player.rect()):
                self.handle_player_collision()
                return True
        return False

    def handle_player_collision(self):
        self.game.screenshake = max(16, self.game.screenshake)
        self.game.sfx['hit'].play()
        self.game.particles.append(Particle(self.game, 'blood', self.rect().center))
        self.create_collision_effects()

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
        if self.flip:
            surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False),
                      (self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0],
                       self.rect().centery - offset[1]))
        else:
            surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))


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
        self.handle_air_time()
        self.handle_landing()
        self.handle_wall_slide()
        self.handle_action()
        self.handle_dash_effects()
        self.apply_friction()

    def handle_air_time(self):
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

    def handle_action(self):
        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif self.last_movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle')

    def handle_dash_effects(self):
        if abs(self.dashing) in {60, 50}:
            self.create_dash_particles()
        self.update_dash_state()
        if abs(self.dashing) > 50:
            self.apply_dash_velocity()
            self.create_dash_trail()

    def create_dash_particles(self):
        for i in range(20):
            angle = random.random() * math.pi * 2
            speed = random.random() * 0.5 + 0.5
            pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
            self.game.particles.append(
                Particle(self.game, 'particle', self.rect().center, velocity=pvelocity,
                         frame=random.randint(0, 7)))

    def update_dash_state(self):
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)

    def apply_dash_velocity(self):
        self.velocity[0] = abs(self.dashing) / self.dashing * 8
        if abs(self.dashing) == 51:
            self.velocity[0] *= 0.1

    def create_dash_trail(self):
        pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
        self.game.particles.append(
            Particle(self.game, 'particle', self.rect().center, velocity=pvelocity,
                     frame=random.randint(0, 7)))

    def apply_friction(self):
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)

    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)

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
