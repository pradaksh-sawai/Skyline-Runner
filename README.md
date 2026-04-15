# 🏙️ Skyline Runner

A fast-paced **endless runner** with anti-gravity mechanics, neon cyberpunk aesthetics, and adaptive difficulty — built with Python & Pygame.

![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![Pygame](https://img.shields.io/badge/Pygame-2.0%2B-green?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-blue)

---

## ✨ Features

- **Anti-Gravity Mechanics** — Toggle gravity on the fly to run on the ground *or* the ceiling. Master the switch to dodge obstacles and rack up bonus points.
- **Adaptive Difficulty** — Game speed and obstacle spawn rate scale progressively the longer you survive.
- **Neon Cyberpunk Visuals** — Parallax starfield, glowing city skyline, pulsing neon platforms, and particle trail effects.
- **Multiple Obstacle Types** — Ground barriers, ceiling spikes, and oscillating mid-air hazards keep every run unique.
- **Collectible Coins** — Grab floating coins for bonus score, complete with spinning and glow animations.
- **Particle Effects** — Trail particles, collection bursts, death explosions, and gravity-switch flashes.
- **Screen Shake** — Impactful feedback on collision.
- **HUD** — Live score, speed indicator, gravity state, and gravity-switch counter.

---

## 🎮 Controls

| Key | Action |
|---|---|
| `SPACE` / `↑` | Jump |
| `↓` | Slide (hold) |
| `N` | Toggle gravity |
| `R` | Restart (game over screen) |
| `ESC` | Quit |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Pygame 2.0+**

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-username>/skyline-runner.git
cd skyline-runner

# Install dependencies
pip install pygame

# Run the game
python main.py
```

---

## 🗂️ Project Structure

```
Skyline Runner/
├── main.py        # Game loop, rendering, background, HUD, and state management
├── player.py      # Player physics, input handling, gravity switching, and rendering
├── obstacles.py   # Obstacle types, coin collectibles, particle system, and spawn logic
├── utils.py       # Constants, color palette, physics config, and utility functions
└── README.md
```

### Module Overview

| Module | Responsibility |
|---|---|
| **`main.py`** | Initializes Pygame, runs the main loop, manages game states (title → playing → game over), renders the parallax background (stars, buildings), draws platforms with neon grid lines, and orchestrates the HUD. |
| **`player.py`** | Encapsulates all player logic — gravity-aware physics, jump/slide mechanics, gravity toggling with cooldown, squash-and-stretch animation, motion trail, and the visor + leg rendering. |
| **`obstacles.py`** | Defines three obstacle variants (ground, ceiling, moving/oscillating), the coin collectible with spin animation, a full particle system (burst + trail emitters), and the `ObstacleManager` that handles spawning and collision detection. |
| **`utils.py`** | Central config file — screen dimensions, the full neon color palette, physics constants, difficulty scaling parameters, and shared math helpers (`lerp`, `clamp`, `pulse`, `ease_out_cubic`, etc.). |

---

## ⚙️ Configuration

All tunable game parameters live in **`utils.py`**. Key values you might want to tweak:

| Constant | Default | Description |
|---|---|---|
| `SCREEN_WIDTH / HEIGHT` | 1000 × 600 | Window resolution |
| `FPS` | 60 | Target frame rate |
| `GRAVITY_STRENGTH` | 0.6 | Downward acceleration per frame |
| `JUMP_FORCE` | -12 | Initial jump velocity |
| `GRAVITY_SWITCH_COOLDOWN` | 500 ms | Minimum time between gravity toggles |
| `OBSTACLE_BASE_SPEED` | 5 | Starting scroll speed |
| `MAX_GAME_SPEED` | 12 | Speed cap |
| `SPEED_INCREASE_RATE` | 0.002 | Speed gain per frame |
| `COIN_SPAWN_CHANCE` | 0.75 | Probability of a coin per obstacle spawn |
| `COIN_POINTS` | 50 | Points per coin collected |
| `GRAVITY_SWITCH_BONUS` | 25 | Bonus points per gravity toggle |

---

## 🎨 Visuals & Design

The game uses a **cyberpunk neon** aesthetic:

- **Background** — Deep purple-to-black vertical gradient with 80 twinkling parallax stars.
- **Cityscape** — Procedurally generated silhouette buildings with randomly lit windows (cyan, yellow, orange, pink) and blinking antenna lights.
- **Platforms** — Ground and ceiling rendered as dark panels with scrolling grid lines and pulsing neon edge highlights (cyan for ground, magenta for ceiling).
- **Player** — Rounded rectangle body with inner highlight, directional visor (cyan/magenta based on gravity), animated legs, pulsing glow halo, gravity-direction arrow, and a fading motion trail.
- **Obstacles** — Glowing rectangles with warning stripes (ground/ceiling) or diamond shapes (moving). Each has its own glow aura.
- **Coins** — 3D-style spinning ellipse with golden glow and collection burst animation.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to open an issue or submit a pull request.

---

> *Run the skyline. Defy gravity. Beat your high score.*
