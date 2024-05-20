import pygame


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        # Initialize the physics entity with game reference, type, position, and size
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        # Initialize animation variables
        self.animation = None
        self.action = ''
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action('idle')

    def rect(self):
        # Return a pygame.Rect object representing the entity's position and size
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        # Set the current action and update the animation if the action has changed
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()

    def update(self, tilemap, movement=(0, 0)):
        # Update the entity's position and handle collisions
        self.collisions = {'up': False, 'down': False, 'right': False, 'left': False}

        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

        # Move entity horizontally and check for collisions
        self.pos[0] += frame_movement[0]
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

        # Move entity vertically and check for collisions
        self.pos[1] += frame_movement[1]
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

        # Update flip state based on horizontal movement
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        # Apply gravity to the entity
        if self.velocity[1] + 0.1 <= 5:
            self.velocity[1] += 0.1
        else:
            self.velocity[1] = 5

        # Reset vertical velocity if the entity is colliding with the ground or ceiling
        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0

        # Update the animation
        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        # Render the entity's current animation frame on the surface with the specified offset
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        # Initialize the player as a PhysicsEntity
        super().__init__(game, 'player', pos, size)
        self.air_time = 0

    def update(self, tilemap, movement=(0, 0)):
        # Update the player's position and handle animations
        super().update(tilemap, movement=movement)

        # Update air time based on collision state
        self.air_time += 1
        if self.collisions['down']:
            self.air_time = 0

        # Set the appropriate animation based on the player's state
        if self.air_time > 4:
            self.set_action('jump')
        elif movement[0] != 0:
            self.set_action('run')
        else:
            self.set_action('idle')

