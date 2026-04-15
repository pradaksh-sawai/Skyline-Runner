"""
main.py — Main game loop for Skyline Runner.

Skyline Runner — Antigravity Opus 4.6
A fast-paced endless runner with anti-gravity mechanics,
neon cyberpunk aesthetics, and adaptive difficulty.

Controls:
    SPACE  — Jump
    DOWN   — Slide (hold)
    G      — Toggle gravity direction
    R      — Restart (game over)
    ESC    — Quit
"""

import pygame
import sys
import math
import random

from utils import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, CAPTION,
    BG_DARK, BG_MID, BG_GRADIENT_TOP, BG_GRADIENT_BOTTOM,
    NEON_CYAN, NEON_MAGENTA, NEON_PINK, NEON_BLUE, NEON_PURPLE,
    NEON_GREEN, NEON_YELLOW, NEON_ORANGE,
    WHITE, BLACK, GRAY, DARK_GRAY, LIGHT_GRAY,
    GROUND_Y, CEILING_Y, PLATFORM_HEIGHT,
    OBSTACLE_BASE_SPEED, NUM_STARS, NUM_BUILDINGS,
    clamp, pulse, lerp, ease_out_cubic, format_score,
    get_game_speed, get_spawn_rate, get_difficulty_multiplier
)
from player import Player
from obstacles import ObstacleManager, ParticleSystem


# ─────────────────────────────────────────────
# Background Elements
# ─────────────────────────────────────────────

class Star:
    """A background star for the parallax sky."""

    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.size = random.uniform(0.5, 2.5)
        self.speed = random.uniform(0.2, 1.0)
        self.brightness = random.randint(100, 255)
        self.twinkle_offset = random.uniform(0, math.pi * 2)

    def update(self, game_speed):
        self.x -= self.speed * (game_speed / OBSTACLE_BASE_SPEED)
        if self.x < -5:
            self.x = SCREEN_WIDTH + random.randint(0, 20)
            self.y = random.randint(0, SCREEN_HEIGHT)

    def draw(self, surface, time_ms):
        twinkle = pulse(time_ms + self.twinkle_offset * 500,
                        speed=1.5, min_val=0.3, max_val=1.0)
        alpha = int(self.brightness * twinkle)
        color = (alpha, alpha, min(alpha + 30, 255))
        size = max(1, int(self.size * twinkle))
        if size <= 1:
            surface.set_at((int(self.x), int(self.y)), color)
        else:
            pygame.draw.circle(surface, color,
                               (int(self.x), int(self.y)), size)


class Building:
    """A silhouette building for the parallax cityscape."""

    def __init__(self, x=None):
        self.width = random.randint(40, 100)
        self.height = random.randint(80, 280)
        self.x = x if x is not None else random.randint(0, SCREEN_WIDTH)
        self.y = GROUND_Y - self.height
        self.speed = random.uniform(0.3, 1.2)
        self.shade = random.randint(12, 30)
        self.windows = self._generate_windows()
        self.has_antenna = random.random() < 0.3
        self.antenna_height = random.randint(15, 40)

    def _generate_windows(self):
        windows = []
        cols = max(1, self.width // 18)
        rows = max(1, self.height // 22)
        margin_x = 8
        margin_y = 10
        spacing_x = (self.width - margin_x * 2) / max(cols, 1)
        spacing_y = (self.height - margin_y * 2) / max(rows, 1)

        for row in range(rows):
            for col in range(cols):
                if random.random() < 0.6:
                    wx = margin_x + col * spacing_x
                    wy = margin_y + row * spacing_y
                    lit = random.random() < 0.4
                    color = random.choice([
                        NEON_CYAN, NEON_YELLOW, NEON_ORANGE, NEON_PINK
                    ]) if lit else (25, 25, 40)
                    windows.append((wx, wy, lit, color))
        return windows

    def update(self, game_speed):
        self.x -= self.speed * (game_speed / OBSTACLE_BASE_SPEED)
        if self.x + self.width < -10:
            self.x = SCREEN_WIDTH + random.randint(10, 80)
            self.width = random.randint(40, 100)
            self.height = random.randint(80, 280)
            self.y = GROUND_Y - self.height
            self.shade = random.randint(12, 30)
            self.windows = self._generate_windows()
            self.has_antenna = random.random() < 0.3
            self.antenna_height = random.randint(15, 40)

    def draw(self, surface, time_ms):
        # Building body
        body_color = (self.shade, self.shade, self.shade + 15)
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        pygame.draw.rect(surface, body_color, rect)

        # Edge highlight
        pygame.draw.line(surface, (self.shade + 20, self.shade + 20,
                                   self.shade + 35),
                         (self.x, self.y), (self.x, self.y + self.height), 1)

        # Windows
        for wx, wy, lit, color in self.windows:
            w_rect = pygame.Rect(self.x + wx, self.y + wy, 8, 10)
            if lit:
                glow_alpha = int(pulse(time_ms, speed=0.5,
                                       min_val=20, max_val=40))
                glow_surf = pygame.Surface((16, 18), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*color[:3], glow_alpha),
                                 (0, 0, 16, 18), border_radius=2)
                surface.blit(glow_surf, (w_rect.x - 4, w_rect.y - 4))
            pygame.draw.rect(surface, color, w_rect)

        # Antenna
        if self.has_antenna:
            ax = self.x + self.width // 2
            ay = self.y
            pygame.draw.line(surface, (50, 50, 70),
                             (ax, ay), (ax, ay - self.antenna_height), 2)
            # Blinking light
            blink = pulse(time_ms, speed=1.0, min_val=0, max_val=1)
            if blink > 0.5:
                pygame.draw.circle(surface, (255, 50, 50),
                                   (ax, ay - self.antenna_height), 3)


# ─────────────────────────────────────────────
# HUD (Heads-Up Display)
# ─────────────────────────────────────────────

class HUD:
    """Renders score, gravity indicator, and other UI elements."""

    def __init__(self):
        self.font_large = None
        self.font_medium = None
        self.font_small = None
        self.font_title = None
        self._init_fonts()

    def _init_fonts(self):
        """Initialize fonts."""
        try:
            self.font_title = pygame.font.SysFont("Consolas", 52, bold=True)
            self.font_large = pygame.font.SysFont("Consolas", 32, bold=True)
            self.font_medium = pygame.font.SysFont("Consolas", 22)
            self.font_small = pygame.font.SysFont("Consolas", 16)
        except Exception:
            self.font_title = pygame.font.Font(None, 52)
            self.font_large = pygame.font.Font(None, 32)
            self.font_medium = pygame.font.Font(None, 22)
            self.font_small = pygame.font.Font(None, 16)

    def draw_gameplay_hud(self, surface, score, gravity, game_speed,
                          gravity_switches):
        """Draw the in-game HUD."""
        time_ms = pygame.time.get_ticks()

        # Score
        score_text = format_score(score)
        score_surf = self.font_large.render(score_text, True, WHITE)
        score_label = self.font_small.render("SCORE", True, GRAY)
        surface.blit(score_label, (SCREEN_WIDTH - 220, 15))
        surface.blit(score_surf, (SCREEN_WIDTH - 220, 32))

        # Gravity indicator
        grav_color = NEON_CYAN if gravity == 1 else NEON_MAGENTA
        grav_text = "▼ NORMAL" if gravity == 1 else "▲ INVERTED"
        grav_label = self.font_small.render("GRAVITY", True, GRAY)
        grav_surf = self.font_medium.render(grav_text, True, grav_color)
        surface.blit(grav_label, (20, 15))
        surface.blit(grav_surf, (20, 32))

        # Speed indicator
        speed_pct = int((game_speed / 12) * 100)
        speed_text = f"SPD {speed_pct}%"
        speed_surf = self.font_small.render(speed_text, True, NEON_GREEN)
        surface.blit(speed_surf, (20, 58))

        # Gravity switch count
        gs_text = f"G-SWITCHES: {gravity_switches}"
        gs_surf = self.font_small.render(gs_text, True, NEON_PURPLE)
        surface.blit(gs_surf, (SCREEN_WIDTH - 220, 58))

        # Controls hint (fades out)
        if time_ms < 6000:
            alpha = int(255 * max(0, 1 - time_ms / 6000))
            hint_texts = [
                "SPACE: Jump  |  DOWN: Slide  |  N: Gravity Switch"
            ]
            for i, txt in enumerate(hint_texts):
                hint_surf = self.font_small.render(txt, True,
                                                   (*LIGHT_GRAY[:3],))
                hint_alpha_surf = pygame.Surface(hint_surf.get_size(),
                                                 pygame.SRCALPHA)
                hint_alpha_surf.blit(hint_surf, (0, 0))
                hint_alpha_surf.set_alpha(alpha)
                x = SCREEN_WIDTH // 2 - hint_surf.get_width() // 2
                surface.blit(hint_alpha_surf, (x, SCREEN_HEIGHT - 30))

    def draw_game_over(self, surface, score, high_score):
        """Draw the game over overlay."""
        time_ms = pygame.time.get_ticks()

        # Semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Title
        title_color = (
            int(pulse(time_ms, speed=0.5, min_val=200, max_val=255)),
            int(pulse(time_ms + 500, speed=0.5, min_val=50, max_val=150)),
            int(pulse(time_ms + 1000, speed=0.5, min_val=100, max_val=255)),
        )
        title_surf = self.font_title.render("GAME OVER", True, title_color)
        tx = SCREEN_WIDTH // 2 - title_surf.get_width() // 2
        surface.blit(title_surf, (tx, SCREEN_HEIGHT // 2 - 100))

        # Score
        score_text = f"SCORE: {format_score(score)}"
        score_surf = self.font_large.render(score_text, True, NEON_CYAN)
        sx = SCREEN_WIDTH // 2 - score_surf.get_width() // 2
        surface.blit(score_surf, (sx, SCREEN_HEIGHT // 2 - 30))

        # High score
        hs_text = f"BEST:  {format_score(high_score)}"
        hs_color = NEON_YELLOW if score >= high_score else LIGHT_GRAY
        hs_surf = self.font_medium.render(hs_text, True, hs_color)
        hx = SCREEN_WIDTH // 2 - hs_surf.get_width() // 2
        surface.blit(hs_surf, (hx, SCREEN_HEIGHT // 2 + 15))

        # New high score banner
        if score >= high_score and score > 0:
            new_hs = self.font_medium.render("** NEW HIGH SCORE! **", True,
                                             NEON_YELLOW)
            nhx = SCREEN_WIDTH // 2 - new_hs.get_width() // 2
            surface.blit(new_hs, (nhx, SCREEN_HEIGHT // 2 + 45))

        # Restart prompt
        blink = pulse(time_ms, speed=1.5, min_val=0.3, max_val=1.0)
        restart_alpha = int(255 * blink)
        restart_text = "Press R to Restart  |  ESC to Quit"
        restart_surf = self.font_medium.render(restart_text, True, WHITE)
        restart_alpha_surf = pygame.Surface(restart_surf.get_size(),
                                            pygame.SRCALPHA)
        restart_alpha_surf.blit(restart_surf, (0, 0))
        restart_alpha_surf.set_alpha(restart_alpha)
        rx = SCREEN_WIDTH // 2 - restart_surf.get_width() // 2
        surface.blit(restart_alpha_surf, (rx, SCREEN_HEIGHT // 2 + 90))

    def draw_start_screen(self, surface):
        """Draw the start/title screen."""
        time_ms = pygame.time.get_ticks()

        # Dark overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        # Title with glow
        title_text = "SKYLINE RUNNER"
        glow_color = (
            int(pulse(time_ms, speed=0.3, min_val=0, max_val=80)),
            int(pulse(time_ms, speed=0.3, min_val=100, max_val=255)),
            int(pulse(time_ms, speed=0.3, min_val=200, max_val=255)),
        )
        title_surf = self.font_title.render(title_text, True, glow_color)
        tx = SCREEN_WIDTH // 2 - title_surf.get_width() // 2
        ty = SCREEN_HEIGHT // 2 - 100

        # Title glow
        glow_surf = self.font_title.render(title_text, True, NEON_CYAN)
        glow_alpha_surf = pygame.Surface(glow_surf.get_size(), pygame.SRCALPHA)
        glow_alpha_surf.blit(glow_surf, (0, 0))
        glow_alpha_surf.set_alpha(int(pulse(time_ms, speed=1.0,
                                            min_val=30, max_val=80)))
        surface.blit(glow_alpha_surf, (tx - 2, ty - 2))
        surface.blit(title_surf, (tx, ty))


        # Controls
        controls = [
            ("SPACE", "Jump"),
            ("DOWN ↓", "Slide"),
            ("N", "Switch Gravity"),
        ]
        cy = SCREEN_HEIGHT // 2 + 10
        for key, action in controls:
            key_surf = self.font_medium.render(f"[{key}]", True, NEON_CYAN)
            act_surf = self.font_small.render(action, True, LIGHT_GRAY)
            kx = SCREEN_WIDTH // 2 - 60
            surface.blit(key_surf, (kx, cy))
            surface.blit(act_surf, (kx + key_surf.get_width() + 10, cy + 4))
            cy += 30

        # Start prompt
        blink = pulse(time_ms, speed=1.5, min_val=0.3, max_val=1.0)
        start_alpha = int(255 * blink)
        start_text = "Press SPACE to Start"
        start_surf = self.font_large.render(start_text, True, WHITE)
        start_alpha_surf = pygame.Surface(start_surf.get_size(),
                                          pygame.SRCALPHA)
        start_alpha_surf.blit(start_surf, (0, 0))
        start_alpha_surf.set_alpha(start_alpha)
        stx = SCREEN_WIDTH // 2 - start_surf.get_width() // 2
        surface.blit(start_alpha_surf, (stx, SCREEN_HEIGHT // 2 + 120))


# ─────────────────────────────────────────────
# Main Game Class
# ─────────────────────────────────────────────

class Game:
    """Main game controller — manages state, loop, and rendering."""

    # Game states
    STATE_TITLE = 0
    STATE_PLAYING = 1
    STATE_GAME_OVER = 2

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(CAPTION)
        self.clock = pygame.time.Clock()

        # Game objects
        self.player = Player()
        self.obstacle_manager = ObstacleManager()
        self.particle_system = ParticleSystem()
        self.hud = HUD()

        # Background
        self.stars = [Star() for _ in range(NUM_STARS)]
        self.buildings = []
        self._init_buildings()

        # Game state
        self.state = self.STATE_TITLE
        self.score = 0
        self.high_score = 0
        self.frame_count = 0
        self.game_speed = OBSTACLE_BASE_SPEED
        self.screen_shake = 0
        self.running = True

        # Pre-render gradient background
        self.bg_surface = self._create_bg_gradient()

    def _init_buildings(self):
        """Create initial building layout."""
        self.buildings = []
        x = 0
        while x < SCREEN_WIDTH + 100:
            b = Building(x)
            self.buildings.append(b)
            x += b.width + random.randint(5, 30)

    def _create_bg_gradient(self):
        """Create a vertical gradient background surface."""
        surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(lerp(BG_GRADIENT_TOP[0], BG_GRADIENT_BOTTOM[0], t))
            g = int(lerp(BG_GRADIENT_TOP[1], BG_GRADIENT_BOTTOM[1], t))
            b = int(lerp(BG_GRADIENT_TOP[2], BG_GRADIENT_BOTTOM[2], t))
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))
        return surface

    def run(self):
        """Main game loop."""
        while self.running:
            events = pygame.event.get()
            keys = pygame.key.get_pressed()

            # Handle global events
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False

            # State machine
            if self.state == self.STATE_TITLE:
                self._update_title(events)
            elif self.state == self.STATE_PLAYING:
                self._update_playing(keys, events)
            elif self.state == self.STATE_GAME_OVER:
                self._update_game_over(events)

            # Render
            self._render()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    # ─── State Updates ───

    def _update_title(self, events):
        """Update title screen state."""
        time_ms = pygame.time.get_ticks()

        # Update background
        for star in self.stars:
            star.update(3)
        for building in self.buildings:
            building.update(3)

        # Wait for start
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self._start_game()

    def _update_playing(self, keys, events):
        """Update gameplay state."""
        self.frame_count += 1

        # Calculate dynamic values
        self.game_speed = get_game_speed(OBSTACLE_BASE_SPEED, self.frame_count)
        spawn_rate = get_spawn_rate(self.frame_count)

        # Update player
        self.player.handle_input(keys, events)
        self.player.update()

        # Update obstacles
        self.obstacle_manager.update(self.game_speed, spawn_rate)

        # Update particles
        self.particle_system.update()

        # Emit player trail
        if self.frame_count % 2 == 0:
            trail_color = NEON_CYAN if self.player.gravity == 1 else NEON_MAGENTA
            self.particle_system.emit_trail(
                self.player.x,
                self.player.y + self.player.height // 2,
                self.player.gravity,
                trail_color
            )

        # Update background
        for star in self.stars:
            star.update(self.game_speed)
        for building in self.buildings:
            building.update(self.game_speed)

        # Score (distance-based)
        self.score += int(self.game_speed * 0.5)

        # Collect coins
        player_rect = self.player.get_rect()
        coin_points = self.obstacle_manager.check_coin_collection(player_rect)
        if coin_points > 0:
            self.score += coin_points
            self.particle_system.emit(
                self.player.x + self.player.width // 2,
                self.player.y + self.player.height // 2,
                NEON_YELLOW, count=10, spread=4, speed=3
            )

        # Gravity switch bonus
        if self.player.score_bonus > 0:
            self.score += self.player.score_bonus
            self.player.score_bonus = 0
            self.particle_system.emit(
                self.player.x + self.player.width // 2,
                self.player.y + self.player.height // 2,
                NEON_MAGENTA, count=15, spread=5, speed=4
            )

        # Collision detection
        if self.obstacle_manager.check_collision(player_rect):
            self._game_over()

    def _update_game_over(self, events):
        """Update game over state."""
        # Update particles (let them finish)
        self.particle_system.update()

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self._start_game()

    # ─── State Transitions ───

    def _start_game(self):
        """Reset and start a new game."""
        self.player.reset()
        self.obstacle_manager.reset()
        self.particle_system = ParticleSystem()
        self.score = 0
        self.frame_count = 0
        self.game_speed = OBSTACLE_BASE_SPEED
        self.screen_shake = 0
        self.state = self.STATE_PLAYING

    def _game_over(self):
        """Handle game over."""
        self.player.alive = False
        self.state = self.STATE_GAME_OVER
        self.screen_shake = 15

        # Update high score
        if self.score > self.high_score:
            self.high_score = self.score

        # Death particles
        self.particle_system.emit(
            self.player.x + self.player.width // 2,
            self.player.y + self.player.height // 2,
            NEON_CYAN, count=30, spread=6, speed=5, lifetime=40
        )
        self.particle_system.emit(
            self.player.x + self.player.width // 2,
            self.player.y + self.player.height // 2,
            NEON_MAGENTA, count=20, spread=5, speed=4, lifetime=35
        )

    # ─── Rendering ───

    def _render(self):
        """Render the current frame."""
        time_ms = pygame.time.get_ticks()

        # Screen shake offset
        shake_x, shake_y = 0, 0
        if self.screen_shake > 0:
            shake_x = random.randint(-3, 3)
            shake_y = random.randint(-3, 3)
            self.screen_shake -= 1

        # Background
        self.screen.blit(self.bg_surface, (shake_x, shake_y))

        # Stars
        for star in self.stars:
            star.draw(self.screen, time_ms)

        # Buildings (background layer)
        for building in self.buildings:
            building.draw(self.screen, time_ms)

        # Ground and ceiling platforms
        self._draw_platforms(time_ms, shake_x, shake_y)

        # Obstacles
        self.obstacle_manager.draw(self.screen)

        # Particles (behind player)
        self.particle_system.draw(self.screen)

        # Player
        if self.state != self.STATE_GAME_OVER or self.screen_shake > 0:
            self.player.draw(self.screen)

        # HUD / UI overlays
        if self.state == self.STATE_TITLE:
            self.hud.draw_start_screen(self.screen)
        elif self.state == self.STATE_PLAYING:
            self.hud.draw_gameplay_hud(
                self.screen, self.score, self.player.gravity,
                self.game_speed, self.player.gravity_switches
            )
        elif self.state == self.STATE_GAME_OVER:
            self.hud.draw_game_over(self.screen, self.score, self.high_score)

    def _draw_platforms(self, time_ms, shake_x, shake_y):
        """Draw the ground and ceiling with neon grid lines."""
        # Ground
        ground_rect = pygame.Rect(
            0 + shake_x, GROUND_Y + shake_y,
            SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y
        )
        pygame.draw.rect(self.screen, (12, 12, 35), ground_rect)

        # Ground top edge - neon line
        glow_val = pulse(time_ms, speed=0.5, min_val=0.6, max_val=1.0)
        ground_color = tuple(int(c * glow_val) for c in NEON_CYAN[:3])
        pygame.draw.line(self.screen, ground_color,
                         (0, GROUND_Y + shake_y),
                         (SCREEN_WIDTH, GROUND_Y + shake_y), 2)

        # Ground grid lines
        grid_spacing = 40
        scroll_offset = int(self.frame_count * self.game_speed * 0.5) % grid_spacing
        for gx in range(-scroll_offset, SCREEN_WIDTH + grid_spacing, grid_spacing):
            pygame.draw.line(self.screen, (20, 20, 50),
                             (gx + shake_x, GROUND_Y + 2 + shake_y),
                             (gx + shake_x, SCREEN_HEIGHT + shake_y), 1)
        for gy in range(GROUND_Y + grid_spacing, SCREEN_HEIGHT, grid_spacing):
            pygame.draw.line(self.screen, (20, 20, 50),
                             (0 + shake_x, gy + shake_y),
                             (SCREEN_WIDTH, gy + shake_y), 1)

        # Ceiling
        ceiling_rect = pygame.Rect(
            0 + shake_x, 0 + shake_y,
            SCREEN_WIDTH, CEILING_Y
        )
        pygame.draw.rect(self.screen, (12, 12, 35), ceiling_rect)

        # Ceiling bottom edge - neon line
        ceil_color = tuple(int(c * glow_val) for c in NEON_MAGENTA[:3])
        pygame.draw.line(self.screen, ceil_color,
                         (0, CEILING_Y + shake_y),
                         (SCREEN_WIDTH, CEILING_Y + shake_y), 2)

        # Ceiling grid lines
        for gx in range(-scroll_offset, SCREEN_WIDTH + grid_spacing, grid_spacing):
            pygame.draw.line(self.screen, (20, 20, 50),
                             (gx + shake_x, 0 + shake_y),
                             (gx + shake_x, CEILING_Y - 2 + shake_y), 1)


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    game = Game()
    game.run()
