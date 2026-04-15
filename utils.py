"""
utils.py — Helper functions and constants for Skyline Runner.

Contains all game constants, color definitions, utility functions,
and shared configuration values used across the game modules.
"""

import math
import random

# ─────────────────────────────────────────────
# Screen & Display
# ─────────────────────────────────────────────
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60
CAPTION = "Skyline Runner"

# ─────────────────────────────────────────────
# Color Palette (Cyberpunk / Neon Theme)
# ─────────────────────────────────────────────
# Backgrounds
BG_DARK = (10, 10, 30)
BG_MID = (15, 15, 45)
BG_GRADIENT_TOP = (5, 5, 20)
BG_GRADIENT_BOTTOM = (20, 10, 50)

# Neon accent colors
NEON_CYAN = (0, 255, 255)
NEON_MAGENTA = (255, 0, 200)
NEON_PINK = (255, 50, 150)
NEON_BLUE = (30, 144, 255)
NEON_PURPLE = (150, 50, 255)
NEON_GREEN = (0, 255, 150)
NEON_YELLOW = (255, 255, 50)
NEON_ORANGE = (255, 150, 30)

# UI Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 120)
DARK_GRAY = (40, 40, 60)
LIGHT_GRAY = (180, 180, 200)

# Player colors
PLAYER_BODY = (0, 220, 255)
PLAYER_GLOW = (0, 180, 255, 80)
PLAYER_TRAIL = (0, 255, 255, 60)

# Obstacle colors
OBSTACLE_RED = (255, 60, 80)
OBSTACLE_ORANGE = (255, 140, 50)
OBSTACLE_MOVING = (255, 80, 200)

# Collectible colors
COIN_GOLD = (255, 215, 0)
COIN_GLOW = (255, 235, 100)

# ─────────────────────────────────────────────
# Physics
# ─────────────────────────────────────────────
GRAVITY_STRENGTH = 0.6
JUMP_FORCE = -12
MAX_FALL_SPEED = 15
GRAVITY_SWITCH_COOLDOWN = 500  # milliseconds

# ─────────────────────────────────────────────
# Player
# ─────────────────────────────────────────────
PLAYER_X = 120
PLAYER_WIDTH = 36
PLAYER_HEIGHT = 44
PLAYER_SLIDE_HEIGHT = 22
SLIDE_DURATION = 500  # milliseconds

# ─────────────────────────────────────────────
# Ground / Ceiling
# ─────────────────────────────────────────────
GROUND_Y = SCREEN_HEIGHT - 60
CEILING_Y = 60
PLATFORM_HEIGHT = 4

# ─────────────────────────────────────────────
# Obstacles
# ─────────────────────────────────────────────
MIN_OBSTACLE_GAP = 220
OBSTACLE_BASE_SPEED = 5
OBSTACLE_SPAWN_RATE = 90  # frames between spawns (initial)
MIN_SPAWN_RATE = 35

# ─────────────────────────────────────────────
# Collectibles
# ─────────────────────────────────────────────
COIN_SIZE = 16
COIN_SPAWN_CHANCE = 0.75  # 75% per obstacle spawn cycle
COIN_POINTS = 50
GRAVITY_SWITCH_BONUS = 25

# ─────────────────────────────────────────────
# Difficulty Scaling
# ─────────────────────────────────────────────
SPEED_INCREASE_RATE = 0.002  # per frame
MAX_GAME_SPEED = 12
DIFFICULTY_INTERVAL = 600  # frames between difficulty bumps

# ─────────────────────────────────────────────
# Particle System
# ─────────────────────────────────────────────
MAX_PARTICLES = 150
TRAIL_PARTICLE_RATE = 3  # particles per frame
PARTICLE_LIFETIME = 30  # frames

# ─────────────────────────────────────────────
# Stars / Background
# ─────────────────────────────────────────────
NUM_STARS = 80
NUM_BUILDINGS = 12


# ─────────────────────────────────────────────
# Utility Functions
# ─────────────────────────────────────────────

def lerp(a, b, t):
    """Linear interpolation between a and b by factor t."""
    return a + (b - a) * t


def clamp(value, min_val, max_val):
    """Clamp a value within [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def ease_out_cubic(t):
    """Ease-out cubic for smooth deceleration."""
    return 1 - (1 - t) ** 3


def ease_in_out_sine(t):
    """Ease-in-out sine for smooth oscillations."""
    return -(math.cos(math.pi * t) - 1) / 2


def pulse(time_ms, speed=1.0, min_val=0.5, max_val=1.0):
    """Generate a pulsing value based on time."""
    t = (math.sin(time_ms * speed * 0.001 * math.pi * 2) + 1) / 2
    return lerp(min_val, max_val, t)


def random_color_shift(base_color, variance=30):
    """Return a slightly shifted version of a base color."""
    r = clamp(base_color[0] + random.randint(-variance, variance), 0, 255)
    g = clamp(base_color[1] + random.randint(-variance, variance), 0, 255)
    b = clamp(base_color[2] + random.randint(-variance, variance), 0, 255)
    return (r, g, b)


def format_score(score):
    """Format score with leading zeros."""
    return f"{int(score):08d}"


def get_difficulty_multiplier(frame_count):
    """Calculate difficulty multiplier based on game progress."""
    return 1.0 + (frame_count / DIFFICULTY_INTERVAL) * 0.15


def get_spawn_rate(frame_count):
    """Calculate current obstacle spawn rate based on difficulty."""
    rate = OBSTACLE_SPAWN_RATE - (frame_count // DIFFICULTY_INTERVAL) * 5
    return max(MIN_SPAWN_RATE, rate)


def get_game_speed(base_speed, frame_count):
    """Calculate current game speed based on progress."""
    speed = base_speed + frame_count * SPEED_INCREASE_RATE
    return min(MAX_GAME_SPEED, speed)
