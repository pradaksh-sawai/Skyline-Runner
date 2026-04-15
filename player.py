"""
player.py — Player logic for Skyline Runner.

Handles player physics, gravity switching, jumping, sliding,
rendering (with glow effects and trail), and collision rect management.
"""

import pygame
import math
from utils import (
    PLAYER_X, PLAYER_WIDTH, PLAYER_HEIGHT, PLAYER_SLIDE_HEIGHT,
    GROUND_Y, CEILING_Y, GRAVITY_STRENGTH, JUMP_FORCE, MAX_FALL_SPEED,
    GRAVITY_SWITCH_COOLDOWN, SLIDE_DURATION, SCREEN_WIDTH, SCREEN_HEIGHT,
    NEON_CYAN, NEON_MAGENTA, NEON_PURPLE, WHITE, PLAYER_BODY, PLAYER_TRAIL,
    GRAVITY_SWITCH_BONUS, clamp, pulse, lerp
)


class Player:
    """The player character with anti-gravity mechanics."""

    def __init__(self):
        self.x = PLAYER_X
        self.y = GROUND_Y - PLAYER_HEIGHT
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.velocity_y = 0
        self.gravity = 1  # 1 = normal, -1 = inverted
        self.on_ground = True
        self.is_sliding = False
        self.slide_timer = 0
        self.gravity_cooldown = 0
        self.alive = True
        self.score_bonus = 0  # accumulated bonus from gravity switches
        self.gravity_switches = 0

        # Visual state
        self.trail_positions = []
        self.glow_intensity = 1.0
        self.squash_stretch = 1.0  # for juice
        self.tilt_angle = 0
        self.flash_timer = 0  # flash on gravity switch
        self.run_frame = 0

    def handle_input(self, keys, events):
        """Process player input for jump, slide, and gravity switch."""
        current_time = pygame.time.get_ticks()

        for event in events:
            if event.type == pygame.KEYDOWN:
                # Jump
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    self._jump()

                # Gravity switch
                if event.key == pygame.K_n:
                    self._switch_gravity(current_time)

        # Slide (hold)
        if keys[pygame.K_DOWN]:
            if not self.is_sliding and self.on_ground:
                self.is_sliding = True
                self.slide_timer = current_time
                self.height = PLAYER_SLIDE_HEIGHT
                # Adjust y position based on gravity
                if self.gravity == 1:
                    self.y = GROUND_Y - PLAYER_SLIDE_HEIGHT
                else:
                    self.y = CEILING_Y
        else:
            if self.is_sliding:
                self.is_sliding = False
                self.height = PLAYER_HEIGHT
                if self.gravity == 1:
                    self.y = GROUND_Y - PLAYER_HEIGHT
                else:
                    self.y = CEILING_Y

    def _jump(self):
        """Apply jump force if player is on the ground."""
        if self.on_ground:
            self.velocity_y = JUMP_FORCE * self.gravity
            self.on_ground = False
            self.squash_stretch = 0.6  # squash on jump

    def _switch_gravity(self, current_time):
        """Toggle gravity direction with cooldown."""
        if current_time - self.gravity_cooldown >= GRAVITY_SWITCH_COOLDOWN:
            self.gravity *= -1
            self.gravity_cooldown = current_time
            self.on_ground = False
            self.velocity_y = 2 * self.gravity  # small push in new direction
            self.flash_timer = 15  # visual flash frames
            self.score_bonus += GRAVITY_SWITCH_BONUS
            self.gravity_switches += 1

    def update(self):
        """Update player physics and position."""
        if not self.alive:
            return

        # Apply gravity
        self.velocity_y += GRAVITY_STRENGTH * self.gravity
        self.velocity_y = clamp(self.velocity_y,
                                -MAX_FALL_SPEED, MAX_FALL_SPEED)

        # Update position
        self.y += self.velocity_y

        # Ground collision (normal gravity)
        if self.gravity == 1:
            ground_level = GROUND_Y - self.height
            if self.y >= ground_level:
                self.y = ground_level
                self.velocity_y = 0
                if not self.on_ground:
                    self.squash_stretch = 1.3  # stretch on land
                self.on_ground = True
            else:
                self.on_ground = False

            # Ceiling check
            if self.y < CEILING_Y:
                self.y = CEILING_Y
                self.velocity_y = 0

        # Ceiling collision (inverted gravity)
        else:
            ceiling_level = CEILING_Y
            if self.y <= ceiling_level:
                self.y = ceiling_level
                self.velocity_y = 0
                if not self.on_ground:
                    self.squash_stretch = 1.3
                self.on_ground = True
            else:
                self.on_ground = False

            # Ground check (inverted)
            if self.y + self.height > GROUND_Y:
                self.y = GROUND_Y - self.height
                self.velocity_y = 0

        # Update visual effects
        self._update_visuals()

    def _update_visuals(self):
        """Update trail, squash/stretch, tilt, and other visual effects."""
        # Trail
        self.trail_positions.append((self.x + self.width // 2,
                                     self.y + self.height // 2))
        if len(self.trail_positions) > 15:
            self.trail_positions.pop(0)

        # Squash/stretch recovery
        self.squash_stretch = lerp(self.squash_stretch, 1.0, 0.15)

        # Tilt based on velocity
        target_tilt = clamp(self.velocity_y * 2, -25, 25)
        self.tilt_angle = lerp(self.tilt_angle, target_tilt, 0.1)

        # Flash timer
        if self.flash_timer > 0:
            self.flash_timer -= 1

        # Run animation
        if self.on_ground and not self.is_sliding:
            self.run_frame += 0.3

    def get_rect(self):
        """Return the player's collision rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, surface):
        """Render the player with glow, trail, and visual effects."""
        time_ms = pygame.time.get_ticks()

        # Draw trail
        self._draw_trail(surface)

        # Determine body color
        if self.flash_timer > 0:
            body_color = NEON_MAGENTA if self.flash_timer % 3 != 0 else WHITE
        else:
            body_color = PLAYER_BODY

        # Glow effect (create a glow surface)
        glow_size = int(max(self.width, self.height) * 2.5)
        glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_alpha = int(pulse(time_ms, speed=2.0, min_val=25, max_val=60))
        glow_color = (*NEON_CYAN[:3], glow_alpha)
        pygame.draw.ellipse(glow_surface, glow_color,
                            (0, 0, glow_size, glow_size))
        glow_x = self.x + self.width // 2 - glow_size // 2
        glow_y = self.y + self.height // 2 - glow_size // 2
        surface.blit(glow_surface, (glow_x, glow_y))

        # Build player body shape
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2

        # Apply squash/stretch
        draw_w = int(self.width * (2 - self.squash_stretch))
        draw_h = int(self.height * self.squash_stretch)

        # Main body (rounded rectangle)
        body_rect = pygame.Rect(
            cx - draw_w // 2, cy - draw_h // 2,
            draw_w, draw_h
        )
        pygame.draw.rect(surface, body_color, body_rect, border_radius=8)

        # Inner highlight
        highlight_rect = body_rect.inflate(-8, -8)
        highlight_color = tuple(min(c + 60, 255) for c in body_color[:3])
        pygame.draw.rect(surface, highlight_color, highlight_rect,
                         border_radius=5, width=2)

        # Eye / visor
        visor_y = cy - draw_h // 6
        if self.gravity == -1:
            visor_y = cy + draw_h // 6
        visor_w = draw_w - 12
        visor_h = 6
        visor_rect = pygame.Rect(cx - visor_w // 2, visor_y - visor_h // 2,
                                 visor_w, visor_h)
        visor_color = NEON_CYAN if self.gravity == 1 else NEON_MAGENTA
        pygame.draw.rect(surface, visor_color, visor_rect, border_radius=3)

        # Legs animation (only when running on ground)
        if self.on_ground and not self.is_sliding:
            leg_offset = int(math.sin(self.run_frame) * 6)
            leg_y = cy + draw_h // 2
            if self.gravity == -1:
                leg_y = cy - draw_h // 2
                leg_offset = -leg_offset

            # Left leg
            pygame.draw.line(surface, body_color,
                             (cx - 6, leg_y),
                             (cx - 8, leg_y + (8 + leg_offset) * self.gravity), 3)
            # Right leg
            pygame.draw.line(surface, body_color,
                             (cx + 6, leg_y),
                             (cx + 8, leg_y + (8 - leg_offset) * self.gravity), 3)

        # Gravity indicator arrow
        arrow_y = cy - draw_h // 2 - 12 if self.gravity == 1 else cy + draw_h // 2 + 12
        arrow_size = 6
        arrow_alpha = int(pulse(time_ms, speed=3.0, min_val=80, max_val=200))
        arrow_color = NEON_CYAN if self.gravity == 1 else NEON_MAGENTA
        if self.gravity == 1:
            points = [
                (cx, arrow_y - arrow_size),
                (cx - arrow_size, arrow_y + arrow_size),
                (cx + arrow_size, arrow_y + arrow_size),
            ]
        else:
            points = [
                (cx, arrow_y + arrow_size),
                (cx - arrow_size, arrow_y - arrow_size),
                (cx + arrow_size, arrow_y - arrow_size),
            ]
        pygame.draw.polygon(surface, arrow_color, points)

    def _draw_trail(self, surface):
        """Draw the motion trail behind the player."""
        if len(self.trail_positions) < 2:
            return

        for i, pos in enumerate(self.trail_positions):
            alpha = int((i / len(self.trail_positions)) * 40)
            radius = int((i / len(self.trail_positions)) * 6) + 1
            trail_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            color = NEON_CYAN if self.gravity == 1 else NEON_MAGENTA
            pygame.draw.circle(trail_surf, (*color[:3], alpha),
                               (radius, radius), radius)
            surface.blit(trail_surf, (pos[0] - radius, pos[1] - radius))

    def reset(self):
        """Reset player to initial state."""
        self.__init__()
