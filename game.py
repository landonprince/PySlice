import os
import sys
import math
import random
import pygame
import time

from scripts.utils import load_image, load_images, Animation
from scripts.entities import Player, Enemy
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark


class Game:
    def __init__(self):
        self.initialize_pygame()
        self.setup_display()
        self.load_assets()
        self.load_sfx()
        self.initialize_game_objects()
        self.load_level(self.level)

    def initialize_pygame(self):
        pygame.init()
        pygame.display.set_caption('PySlice')

    def setup_display(self):
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font('assets/ARCADECLASSIC.TTF', 26)
        self.movement = [False, False]

    def load_assets(self):
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'enemy/idle': Animation(load_images('entities/enemy/idle'), img_dur=6),
            'enemy/run': Animation(load_images('entities/enemy/run'), img_dur=4),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'particle/blood': Animation(load_images('particles/blood'), img_dur=1, loop=False),
            'particle/coin': Animation(load_images('particles/coin'), img_dur=5, loop=True),
            'ui/coin': Animation(load_images('ui/coin'), img_dur=5, loop=True),
            'gun': load_image('gun.png'),
            'katana': load_image('katana.png'),
            'projectile': load_image('projectile.png'),
        }

    def load_sfx(self):
        self.sfx = {
            'jump': pygame.mixer.Sound('assets/sfx/jump.wav'),
            'dash': pygame.mixer.Sound('assets/sfx/dash.wav'),
            'hit': pygame.mixer.Sound('assets/sfx/hit.wav'),
            'shoot': pygame.mixer.Sound('assets/sfx/shoot.mp3'),
            'coin': pygame.mixer.Sound('assets/sfx/coin.wav'),
            'ambience': pygame.mixer.Sound('assets/sfx/ambience.wav'),
        }
        self.sfx['ambience'].set_volume(0.2)
        self.sfx['shoot'].set_volume(0.4)
        self.sfx['hit'].set_volume(0.8)
        self.sfx['dash'].set_volume(0.2)
        self.sfx['jump'].set_volume(0.7)
        self.sfx['coin'].set_volume(0.3)

    def initialize_game_objects(self):
        self.clouds = Clouds(self.assets['clouds'], count=16)
        self.player = Player(self, (50, 50), (8, 15))
        self.tilemap = Tilemap(self, tile_size=16)
        self.level = 0
        self.screenshake = 0
        self.coin_count = 0
        self.projectiles = []
        self.particles = []
        self.sparks = []

    def load_level(self, map_id):
        self.tilemap.load('assets/maps/' + str(map_id) + '.json')
        self.create_leaf_spawners()
        self.spawn_entities()
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30
        self.level_transition_delay = 0

    def create_leaf_spawners(self):
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))

    def spawn_entities(self):
        self.enemies = []
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player.pos = spawner['pos']
                self.player.air_time = 0
            else:
                self.enemies.append(Enemy(self, spawner['pos'], (8, 15)))

    def run(self):
        pygame.mixer.music.load('assets/music.wav')
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)
        self.sfx['ambience'].play(-1)

        while True:
            self.clear_display()
            self.handle_level_transition()
            self.handle_player_death()
            render_scroll = self.update_scroll()
            self.spawn_leaf_particles()
            self.clouds.update()
            self.clouds.render(self.display_2, offset=render_scroll)
            self.tilemap.render(self.display, offset=render_scroll)
            self.update_and_render_enemies(render_scroll)
            self.update_and_render_player(render_scroll)
            self.update_and_render_projectiles(render_scroll)
            self.update_and_render_sparks(render_scroll)
            self.create_display_silhouette()
            self.update_and_render_particles(render_scroll)
            self.handle_events()
            self.handle_level_transition_effect()
            self.render_final_display()
            self.clock.tick(60)

    def clear_display(self):
        self.display.fill((0, 0, 0, 0))
        self.display_2.blit(self.assets['background'], (0, 0))
        self.screenshake = max(0, self.screenshake - 1)

    def handle_level_transition(self):
        if not len(self.enemies):
            if self.level_transition_delay == 0:
                self.level_transition_delay = pygame.time.get_ticks()
            elif pygame.time.get_ticks() - self.level_transition_delay >= 750:
                self.transition += 1
                if self.transition > 30:
                    self.level = min(self.level + 1, len(os.listdir('assets/maps')) - 1)
                    self.load_level(self.level)
                    self.level_transition_delay = 0
        if self.transition < 0:
            self.transition += 1

    def handle_player_death(self):
        if self.dead:
            self.dead += 1
            if self.dead >= 10:
                self.transition = min(30, self.transition + 1)
            if self.dead > 40:
                self.load_level(self.level)

    def update_scroll(self):
        self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 30
        self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 30
        return int(self.scroll[0]), int(self.scroll[1])

    def spawn_leaf_particles(self):
        for rect in self.leaf_spawners:
            if random.random() * 49999 < rect.width * rect.height:
                pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3],
                                               frame=random.randint(0, 20)))

    def update_and_render_enemies(self, render_scroll):
        for enemy in self.enemies.copy():
            kill = enemy.update(self.tilemap, (0, 0))
            enemy.render(self.display, offset=render_scroll)
            if kill:
                self.enemies.remove(enemy)

    def update_and_render_player(self, render_scroll):
        if not self.dead:
            self.player.update(self.tilemap, (self.movement[1] - self.movement[0], 0))
            self.player.render(self.display, offset=render_scroll)

    def update_and_render_projectiles(self, render_scroll):
        for projectile in self.projectiles.copy():
            projectile[0][0] += projectile[1] * 1.5
            projectile[2] += 1
            img = self.assets['projectile']
            self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0],
                                    projectile[0][1] - img.get_height() / 2 - render_scroll[1]))

            if self.tilemap.solid_check(projectile[0]):
                self.projectiles.remove(projectile)
                for i in range(4):
                    self.sparks.append(
                        Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0),
                              2 + random.random()))

            elif projectile[2] > 360:
                self.projectiles.remove(projectile)

            elif abs(self.player.dashing) < 50:
                if self.player.rect().collidepoint(projectile[0]):
                    self.projectiles.remove(projectile)
                    self.dead += 1
                    self.sfx['hit'].play()
                    self.screenshake = max(16, self.screenshake)
                    self.particles.append(Particle(self, 'blood', self.player.rect().center))
                    for i in range(30):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.sparks.append(Spark(self.player.rect().center, angle, 2 + random.random()))
                        self.particles.append(Particle(self, 'particle', self.player.rect().center,
                                                       velocity=[math.cos(angle + math.pi) * speed * 0.5,
                                                                 math.sin(angle + math.pi) * speed * 0.5],
                                                       frame=random.randint(0, 7)))

    def update_and_render_sparks(self, render_scroll):
        for spark in self.sparks.copy():
            kill = spark.update()
            spark.render(self.display, offset=render_scroll)
            if kill:
                self.sparks.remove(spark)

    def create_display_silhouette(self):
        display_mask = pygame.mask.from_surface(self.display)
        display_silhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
        shadow = display_mask.to_surface(setcolor=(0, 0, 0, 75), unsetcolor=(0, 0, 0, 0))

        for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            self.display_2.blit(display_silhouette, offset)
        self.display_2.blit(shadow, (4, 4))

    def update_and_render_particles(self, render_scroll):
        for particle in self.particles.copy():
            kill = particle.update()
            particle.render(self.display, offset=render_scroll)

            if particle.type == 'leaf':
                particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
            if particle.type == 'coin':
                kill = self.update_coin_particle(particle)
            if kill:
                self.particles.remove(particle)
                if particle.type == 'coin':
                    self.coin_count += 1

    def update_coin_particle(self, particle):
        if not hasattr(particle, 'initialized'):
            particle.initialized = True
            particle.hover_start_time = None
            particle.returning = False
            particle.angle = random.uniform(0, 2 * math.pi)
            particle.distance = 30
            particle.hover_time = 0.3

        if not particle.returning:
            if not particle.hover_start_time:
                particle.pos[0] += math.cos(particle.angle) * 5
                particle.pos[1] += math.sin(particle.angle) * 5
                if math.hypot(particle.pos[0] - self.player.pos[0],
                              particle.pos[1] - self.player.pos[1]) >= particle.distance:
                    particle.hover_start_time = time.time()
            else:
                if time.time() - particle.hover_start_time >= particle.hover_time:
                    particle.returning = True
        else:
            direction = math.atan2(self.player.pos[1] - particle.pos[1], self.player.pos[0] - particle.pos[0])
            particle.pos[0] += math.cos(direction) * 5
            particle.pos[1] += math.sin(direction) * 5
            if math.hypot(particle.pos[0] - self.player.pos[0], particle.pos[1] - self.player.pos[1]) <= 3:
                self.sfx['coin'].play()
                return True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.player.dash()

            if event.type == pygame.KEYUP:
                self.handle_keyup(event)

    def handle_keydown(self, event):
        if event.key == pygame.K_LEFT or event.key == pygame.K_a:
            self.movement[0] = True
        if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
            self.movement[1] = True
        if event.key == pygame.K_UP or event.key == pygame.K_SPACE:
            if self.player.jump():
                self.sfx['jump'].play()
        if event.key == pygame.K_x:
            self.player.dash()

    def handle_keyup(self, event):
        if event.key == pygame.K_LEFT or event.key == pygame.K_a:
            self.movement[0] = False
        if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
            self.movement[1] = False

    def handle_level_transition_effect(self):
        if self.transition:
            transition_surf = pygame.Surface(self.display.get_size())
            pygame.draw.circle(transition_surf, (255, 255, 255),
                               (self.display.get_width() // 2, self.display.get_height() // 2),
                               (30 - abs(self.transition)) * 8)
            transition_surf.set_colorkey((255, 255, 255))
            self.display.blit(transition_surf, (0, 0))

    def render_stage_info(self):
        stage_text = f"Stage  {self.level + 1}"
        text_surface = self.font.render(stage_text, True, (255, 255, 255))

        border_size = 2
        x, y = 10, 10
        border_positions = [
            (x - border_size, y),
            (x + border_size, y),
            (x, y - border_size),
            (x, y + border_size),
            (x - border_size, y - border_size),
            (x + border_size, y - border_size),
            (x - border_size, y + border_size),
            (x + border_size, y + border_size),
        ]
        for pos in border_positions:
            border_surface = self.font.render(stage_text, True, (0, 0, 0))
            self.screen.blit(border_surface, pos)

        self.screen.blit(text_surface, (x, y))

        self.assets['ui/coin'].update()
        coin = self.assets['ui/coin'].img()
        large_coin = pygame.transform.scale(coin, (int(coin.get_width() * 2.5), int(coin.get_height() * 2.5)))

        coin_x, coin_y = x, y + text_surface.get_height() + 5
        self.screen.blit(large_coin, (coin_x, coin_y))

        coin_count_text = f"{self.coin_count}"
        coin_count_surface = self.font.render(coin_count_text, True, (255, 223, 0))
        coin_count_x = coin_x + large_coin.get_width() + 8
        coin_count_y = coin_y + large_coin.get_height() - 22
        coin_border_positions = [
            (coin_count_x - border_size, coin_count_y),
            (coin_count_x + border_size, coin_count_y),
            (coin_count_x, coin_count_y - border_size),
            (coin_count_x, coin_count_y + border_size),
            (coin_count_x - border_size, coin_count_y - border_size),
            (coin_count_x + border_size, coin_count_y - border_size),
            (coin_count_x - border_size, coin_count_y + border_size),
            (coin_count_x + border_size, coin_count_y + border_size),
        ]
        for pos in coin_border_positions:
            coin_border_surface = self.font.render(coin_count_text, True, (0, 0, 0))
            self.screen.blit(coin_border_surface, pos)

        self.screen.blit(coin_count_surface, (coin_count_x, coin_count_y))

    def render_final_display(self):
        self.display_2.blit(self.display, (0, 0))
        screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2,
                              random.random() * self.screenshake - self.screenshake / 2)
        self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)
        self.render_stage_info()
        pygame.display.update()


Game().run()
