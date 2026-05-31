# ⚡ BLADE HAND — Gesture-Controlled Fruit Ninja

> A real-time, webcam-based Fruit Ninja game powered by **MediaPipe hand tracking**, **OpenCV**, and **Pygame**.  
> Slice fruits with your index finger. No controller needed.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8-green?logo=opencv)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-orange)
![Pygame](https://img.shields.io/badge/Pygame-2.4-red)

---

## 📸 Demo

```
Point your INDEX FINGER at the webcam → slice fruits flying up the screen
Make a FIST to activate a temporary shield
Show TWO FINGERS for combo multiplier mode
Open PALM for slow-motion
```

---

## 🗂 Project Structure

```
fruit_ninja_cv/
├── main.py             # Entry point — game loop & state routing
├── settings.py         # All constants & tunable parameters
├── hand_tracking.py    # MediaPipe wrapper — tip position + gesture detection
├── fruit.py            # Fruit, Bomb, and Special Fruit classes + spawn factory
├── effects.py          # BladeTrail, ParticleSystem, ScreenShake, BackgroundRenderer
├── sound_manager.py    # Procedural audio synthesis + file-based audio loader
├── ui.py               # All UI screens: menus, HUD, leaderboard, settings
├── game_manager.py     # State machine, scoring, power-up timers, leaderboard I/O
├── requirements.txt
├── assets/
│   ├── fonts/          # Drop any .ttf font here to use it in-game
│   ├── sounds/         # Drop .ogg/.wav files here (slice.ogg, bomb.ogg …)
│   └── images/         # Reserved for future sprite sheets
└── saves/
    └── leaderboard.json   # Auto-created on first run
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install opencv-python mediapipe pygame numpy
# or
pip install -r requirements.txt
```

> **Python 3.10+ required.**  
> **MediaPipe 0.10+ requires Python ≤ 3.11** on some platforms.

### 2. Run the Game

```bash
python main.py
```

> Make sure your webcam is plugged in and accessible.  
> Change `CAMERA_INDEX` in `settings.py` if you have multiple cameras.

---

## 🎮 Controls

| Action | Input |
|---|---|
| Slice fruit | Move index finger fast across screen |
| Pause | Press `ESC` |
| Toggle FPS | Press `F3` |
| Toggle debug mode | Press `F4` |
| Fullscreen | Press `F11` |

### Hand Gestures

| Gesture | Effect |
|---|---|
| ☝️ Index finger (pointing) | Normal blade mode |
| ✊ Fist | Activate shield (absorbs 1 bomb) |
| ✌️ Two fingers (peace sign) | 1.5× combo multiplier for 5 seconds |
| 🖐 Open palm | Slow-motion for ~3 seconds |

---

## 🍉 Fruit Types

| Fruit | Points | Notes |
|---|---|---|
| Watermelon | 10 | Common |
| Orange | 10 | Common |
| Lemon | 10 | Common |
| Blueberry | 15 | — |
| Strawberry | 15 | — |
| Kiwi | 20 | — |
| Grape | 20 | — |
| Pineapple | 25 | Rare |

### Special Fruits (cyan/purple/gold glow)

| Fruit | Power |
|---|---|
| 🔵 Freeze | Pauses all fruits for 3 seconds |
| 🟡 Double Score | 2× points for 5 seconds |
| 🟣 Slow-Mo | Slow-motion for 4 seconds |
| 🟢 Bomb Diffuser | Removes all bombs from screen |

### 💣 Bombs

Slicing a bomb costs **1 life** and triggers screen shake + red flash.  
Use Shield (fist gesture) or Bomb Diffuser fruit to stay safe.

---

## 🎯 Game Modes

| Mode | Rules |
|---|---|
| **Arcade** | Endless play, 3 lives, beat your high score |
| **Survival** | 1 life only — how long can you last? |
| **Time Attack** | 60 seconds, maximise your score |

---

## ⚙️ Configuration (`settings.py`)

All game parameters are in `settings.py`.  Tune these to adjust difficulty:

```python
GRAVITY               = 0.25    # How fast fruits fall
INITIAL_SPAWN_INTERVAL= 90      # Frames between spawns at start
MIN_SPAWN_INTERVAL    = 20      # Maximum spawn rate
BOMB_CHANCE           = 0.12    # Probability of bomb spawn
SPECIAL_FRUIT_CHANCE  = 0.08    # Probability of special fruit
FAST_SWIPE_THRESHOLD  = 25      # Min pixels/frame for bonus points
CAMERA_INDEX          = 0       # Change if webcam not detected
FLIP_CAMERA           = True    # Mirror — feels more natural
```

---

## 🔊 Custom Audio

Drop `.ogg` or `.wav` files in `assets/sounds/` with these names:

```
slice.ogg        bomb.ogg         combo.ogg
power.ogg        miss.ogg         menu_tick.ogg
game_over.ogg    shield.ogg       double.ogg
bgm.ogg          ← background music (looped)
```

If a file is missing the game generates a synthetic sound automatically.

---

## 🖋 Custom Fonts

Drop any `.ttf` font file in `assets/fonts/`.  
The first `.ttf` found is used for all UI text.

Recommendations: **Orbitron**, **Exo 2**, **Rajdhani** (Google Fonts, free).

---

## 🐛 Troubleshooting

| Problem | Fix |
|---|---|
| `No webcam found` | Check `CAMERA_INDEX` in `settings.py`; try 0, 1, 2 |
| `mediapipe not found` | `pip install mediapipe` — needs Python 3.10/3.11 |
| `pygame error: No video mode` | Run with display connected; no headless mode |
| Low FPS | Set `DETECTION_CONFIDENCE = 0.5`, lower resolution in `hand_tracking.py` |
| Hand not detected | Improve lighting; keep hand within frame |
| `numpy` dtype errors | `pip install --upgrade numpy` |
| Webcam flipped wrong | Toggle `FLIP_CAMERA = False` in settings |

---

## 🏗 Architecture Overview

```
main.py  ──► GameManager (state machine)
              │
              ├─► HandTracker (MediaPipe + OpenCV)
              ├─► BackgroundRenderer (theme layers)
              ├─► ParticleSystem (juice effects)
              ├─► BladeTrail (neon sword)
              ├─► ScreenShake / HitFlash (cinematic)
              ├─► SoundManager (audio)
              └─► UI screens (Pygame surfaces + GlowButtons)
                     └─► HUD overlay
```

---

## 📈 Resume Description

> **Blade Hand — Real-Time Gesture-Controlled Game** *(Python, OpenCV, MediaPipe, Pygame)*  
> Developed a production-quality computer vision game where players slice virtual fruits by moving their index finger in front of a webcam. Built a real-time hand tracking pipeline using MediaPipe Hands (21-landmark model), mapped finger-tip coordinates to screen space, and implemented gesture classification (fist / open-palm / two-finger) for in-game power-ups. Engineered a physics engine with gravity, adaptive difficulty scaling, and a particle system with 22-particle juice-splash effects. Achieved stable 60 FPS with a modular OOP architecture across 8 production files.

---

## 🔮 Future Improvements

- Multiplayer split-screen (two hands / two players)
- Custom fruit sprite sheets
- Online leaderboard (Flask + SQLite backend)
- Hand skeleton visualisation overlay
- Voice command integration
- Android/iOS port via Kivy or BeeWare
- Difficulty presets (Easy / Medium / Hard / Insane)
- Achievement system
- Replay recording (save frame buffer to video)

---

## 📄 License

MIT — free for personal, educational, and portfolio use.
