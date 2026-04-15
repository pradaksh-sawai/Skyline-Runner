"""
obstacles.py — Obstacle and Collectible systems for Skyline Runner.

Handles obstacle generation, movement, collision detection,
collectible coins, and the particle effects system.
"""

import pygame
import random
import math
from utils import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GROUND_Y, CEILING_Y,
    OBSTACLE_BASE_SPEED, OBSTACLE_RED, OBSTACLE_ORANGE, OBSTACLE_MOVING,
    COIN_GOLD, COIN_GLOW, COIN_SIZE, COIN_POINTS, COIN_SPAWN_CHANCE,
    NEON_CYAN, NEON_MAGENTA, NEON_GREEN, NEON_YELLOW, NEON_PURPLE,
    WHITE, MAX_PARTICLES, PARTICLE_LIFETIME,
    clamp, pulse, random_color_shift, get_game_speed
)


# ─────────────────────────────────────────────
# Obstacle Types
# ─────────────────────────────────────────────

class Obstacle:
    """Base obstacle class — a ground-level barrier."""

    def __init__(self, x, speed, variant="ground"):
        self.variant = variant
        self.speed = speed
        self.active = True

        if variant == "ground":
            self.width = random.randint(30, 55)
            self.height = random.randint(35, 65)
            self.x = x
            self.y = GROUND_Y - self.height
            self.color = OBSTACLE_RED
        elif variant == "ceiling":
            self.width = random.randint(30, 55)
            self.height = random.randint(35, 60)
            self.x = x
            self.y = CEILING_Y
            self.color = OBSTACLE_ORANGE
        elif variant == "moving":
            self.width = 35
            self.height = 35
            self.x = x
            self.base_y = random.randint(CEILING_Y + 60, GROUND_Y - 100)
            self.y = self.base_y
            self.color = OBSTACLE_MOVING
            self.oscillation_speed = random.uniform(0.02, 0.05)
            self.oscillation_amp = random.randint(30, 80)
            self.time_offset = random.uniform(0, math.pi * 2)

        # Visual
        self.glow_phase = random.uniform(0, math.pi * 2)

    def update(self, frame_count):
        """Move obstacle to the left and handle oscillation."""
        self.x -= self.speed

        if self.variant == "moving":
            self.y = self.base_y + math.sin(
                frame_count * self.oscillation_speed + self.time_offset
            ) * self.oscillation_amp

        # Deactivate if off-screen
        if self.x + self.width < -20:
            self.active = False

    def get_rect(self):
        """Return collision rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface):
        """Render obstacle with neon styling."""
        time_ms = pygame.time.get_ticks()
        glow_val = pulse(time_ms + self.glow_phase * 1000, speed=1.5,
                         min_val=0.6, max_val=1.0)

        # Glow background
        glow_size = 10
        glow_rect = pygame.Rect(
            self.x - glow_size, self.y - glow_size,
            self.width + glow_size * 2, self.height + glow_size * 2
        )
        glow_surface = pygame.Surface(
            (glow_rect.width, glow_rect.height), pygame.SRCALPHA
        )
        glow_alpha = int(30 * glow_val)
        glow_color = (*self.color[:3], glow_alpha)
        pygame.draw.rect(glow_surface, glow_color,
                         (0, 0, glow_rect.width, glow_rect.height),
                         border_radius=6)
        surface.blit(glow_surface, glow_rect.topleft)

        # Main body
        body_rect = pygame.Rect(self.x, self.y, self.width, self.height)

        if self.variant == "moving":
            # Moving obstacles are diamond/rotated
            cx = self.x + self.width // 2
            cy = self.y + self.height // 2
            half = self.width // 2
            points = [
                (cx, cy - half),
                (cx + half, cy),
                (cx, cy + half),
                (cx - half, cy),
            ]
            pygame.draw.polygon(surface, self.color, points)
            pygame.draw.polygon(surface, WHITE, points, 2)
        else:
            pygame.draw.rect(surface, self.color, body_rect, border_radius=4)

            # Warning stripes
            stripe_color = tuple(min(c + 40, 255) for c in self.color[:3])
            stripe_y = self.y + 4
            while stripe_y < self.y + self.height - 4:
                pygame.draw.line(surface, stripe_color,
                                 (self.x + 3, stripe_y),
                                 (self.x + self.width - 3, stripe_y), 1)
                stripe_y += 6

            # Border
            pygame.draw.rect(surface, WHITE, body_rect, 2, border_radius=4)


# ─────────────────────────────────────────────
# Collectible Coin
# ─────────────────────────────────────────────

class Coin:
    """Collectible coin that grants bonus points."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = COIN_SIZE
        self.active = True
        self.collected = False
        self.collect_anim = 0
        self.bob_offset = random.uniform(0, math.pi * 2)

    def update(self, speed, frame_count):
        """Move coin left and animate bobbing."""
        self.x -= speed

        # Bobbing motion
        self.y_draw = self.y + math.sin(
            frame_count * 0.08 + self.bob_offset
        ) * 5

        if self.collected:
            self.collect_anim += 1
            if self.collect_anim > 15:
                self.active = False

        if self.x + self.size < -10:
            self.active = False

    def get_rect(self):
        """Return collision rectangle."""
        return pygame.Rect(self.x - self.size, self.y - self.size,
                           self.size * 2, self.size * 2)

    def collect(self):
        """Mark as collected and start animation."""
        if not self.collected:
            self.collected = True
            self.collect_anim = 0
            return COIN_POINTS
        return 0

    def draw(self, surface):
        """Render coin with glow and rotation effect."""
        if self.collected:
            # Collection burst animation
            progress = self.collect_anim / 15.0
            alpha = int(255 * (1 - progress))
            radius = int(self.size + self.collect_anim * 2)
            burst_surf = pygame.Surface((radius * 2, radius * 2),
                                        pygame.SRCALPHA)
            pygame.draw.circle(burst_surf, (*COIN_GOLD, alpha),
                               (radius, radius), radius)
            surface.blit(burst_surf,
                         (self.x - radius, self.y_draw - radius))
            return

        time_ms = pygame.time.get_ticks()

        # Glow
        glow_radius = int(self.size * 2.0)
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2),
                                   pygame.SRCALPHA)
        glow_alpha = int(pulse(time_ms + self.bob_offset * 500,
                               speed=2.0, min_val=20, max_val=50))
        pygame.draw.circle(glow_surf, (*COIN_GLOW, glow_alpha),
                           (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surf,
                     (self.x - glow_radius, self.y_draw - glow_radius))

        # Coin body (simulate rotation with width oscillation)
        coin_width = abs(math.sin(time_ms * 0.003 + self.bob_offset))
        visual_w = max(4, int(self.size * 2 * coin_width))
        coin_rect = pygame.Rect(
            self.x - visual_w // 2, self.y_draw - self.size,
            visual_w, self.size * 2
        )
        pygame.draw.ellipse(surface, COIN_GOLD, coin_rect)
        if visual_w > 6:
            inner_rect = coin_rect.inflate(-4, -4)
            pygame.draw.ellipse(surface, COIN_GLOW, inner_rect, 2)


# ─────────────────────────────────────────────
# Particle System
# ─────────────────────────────────────────────

class Particle:
    """Single particle for visual effects."""

    def __init__(self, x, y, vx, vy, color, lifetime=None, size=None):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime or PARTICLE_LIFETIME
        self.max_lifetime = self.lifetime
        self.size = size or random.uniform(2, 5)
        self.active = True

    def update(self):
        """Update particle position and lifetime."""
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.05  # slight gravity
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.active = False

    def draw(self, surface):
        """Render particle with fading alpha."""
        progress = self.lifetime / self.max_lifetime
        alpha = int(255 * progress)
        size = max(1, int(self.size * progress))
        particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(particle_surf,
                           (*self.color[:3], alpha),
                           (size, size), size)
        surface.blit(particle_surf, (self.x - size, self.y - size))


class ParticleSystem:
    """Manages all particles in the game."""

    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=5, spread=3, speed=2,
             lifetime=None, size=None):
        """Emit a burst of particles."""
        for _ in range(count):
            vx = random.uniform(-spread, spread) * speed * 0.5
            vy = random.uniform(-spread, spread) * speed * 0.5
            p = Particle(x, y, vx, vy, color, lifetime, size)
            self.particles.append(p)

        # Limit particles
        if len(self.particles) > MAX_PARTICLES:
            self.particles = self.particles[-MAX_PARTICLES:]

    def emit_trail(self, x, y, gravity_dir, color):
        """Emit a single trail particle behind the player."""
        vx = random.uniform(-1.5, -0.5)
        vy = random.uniform(-0.5, 0.5) * gravity_dir
        p = Particle(x, y, vx, vy, color, lifetime=20)
        p.size = random.uniform(1.5, 3.5)
        self.particles.append(p)

        if len(self.particles) > MAX_PARTICLES:
            self.particles = self.particles[-MAX_PARTICLES:]

    def update(self):
        """Update all particles and remove dead ones."""
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.active]

    def draw(self, surface):
        """Render all active particles."""
        for p in self.particles:
            p.draw(surface)


# ─────────────────────────────────────────────
# Obstacle Manager
# ─────────────────────────────────────────────

class ObstacleManager:
    """Manages obstacle spawning, movement, and collision detection."""

    def __init__(self):
        self.obstacles = []
        self.coins = []
        self.spawn_timer = 0
        self.frame_count = 0

    def update(self, game_speed, spawn_rate):
        """Update all obstacles and handle spawning."""
        self.frame_count += 1
        self.spawn_timer += 1

        # Spawn new obstacles
        if self.spawn_timer >= spawn_rate:
            self.spawn_timer = 0
            self._spawn_obstacle(game_speed)

        # Update obstacles
        for obs in self.obstacles:
            obs.speed = game_speed
            obs.update(self.frame_count)

        # Update coins
        for coin in self.coins:
            coin.update(game_speed, self.frame_count)

        # Remove inactive
        self.obstacles = [o for o in self.obstacles if o.active]
        self.coins = [c for c in self.coins if c.active]

    def _spawn_obstacle(self, speed):
        """Spawn a random obstacle type."""
        x = SCREEN_WIDTH + random.randint(20, 80)

        # Choose variant
        roll = random.random()
        if roll < 0.50:
            variant = "ground"
        elif roll < 0.80:
            variant = "ceiling"
        else:
            variant = "moving"

        obs = Obstacle(x, speed, variant)
        self.obstacles.append(obs)

        # Chance to spawn a coin nearby
        if random.random() < COIN_SPAWN_CHANCE:
            coin_x = x + random.randint(60, 150)
            coin_y = random.choice([
                GROUND_Y - random.randint(60, 120),
                CEILING_Y + random.randint(30, 80),
                (GROUND_Y + CEILING_Y) // 2 + random.randint(-50, 50)
            ])
            self.coins.append(Coin(coin_x, coin_y))

    def check_collision(self, player_rect):
        """Check if player collides with any obstacle."""
        for obs in self.obstacles:
            if player_rect.colliderect(obs.get_rect()):
                return True
        return False

    def check_coin_collection(self, player_rect):
        """Check and collect coins the player touches."""
        points = 0
        for coin in self.coins:
            if not coin.collected and player_rect.colliderect(coin.get_rect()):
                points += coin.collect()
        return points

    def draw(self, surface):
        """Render all obstacles and coins."""
        for obs in self.obstacles:
            obs.draw(surface)
        for coin in self.coins:
            coin.draw(surface)

    def reset(self):
        """Clear all obstacles and coins."""
        self.obstacles.clear()
        self.coins.clear()
        self.spawn_timer = 0
        self.frame_count = 0
