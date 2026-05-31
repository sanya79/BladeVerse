# ⚡ BLADE HAND — Gesture-Controlled Fruit Ninja

> A real-time, webcam-based Fruit Ninja game powered by **MediaPipe hand tracking**, **OpenCV**, and **Pygame**.  
> Slice fruits with your index finger. No controller needed.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8-green?logo=opencv)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10-orange)
![Pygame](https://img.shields.io/badge/Pygame-2.4-red)

---

## 📸 Gameplay Features

```
🎮 NORMAL MODE (Index Finger Pointing)
   Point your INDEX FINGER at the webcam and move it to slice fruits
   Faster swipes = bonus points!

🛡️ SHIELD MODE (Fist)
   Make a FIST to activate a temporary protective shield
   Shields protect you from bombs for a limited time

🔥 COMBO MODE (Two Fingers)
   Show INDEX + MIDDLE FINGER to enter combo multiplier mode
   Every fruit sliced increases your combo multiplier!

⏱️ SLOW-MOTION (Open Palm)
   Open your entire PALM to activate slow-motion effect
   Gives you more time to react to incoming fruits
```

---

## 🗂️ Project Structure

```
FRUITNINJA/
├── main.py                    # Entry point — game loop & state routing
├── settings.py                # All constants & tunable parameters
├── hand_tracking.py           # MediaPipe wrapper — tip position + gesture
├── fruit.py                   # Fruit, Bomb, Special Fruit classes + spawn logic
├── effects.py                 # BladeTrail, ParticleSystem, ScreenShake, etc.
├── sound_manager.py           # Audio synthesis + file-based audio loader
├── ui.py                      # UI screens: menus, HUD, leaderboard, settings
├── game_manager.py            # State machine, scoring, leaderboard
├── requirements (1).txt       # Python dependencies
├── setup.bat                  # Windows setup script
├── README.md                  # This file
│
├── assets/
│   ├── fonts/                 # Drop .ttf fonts here to use in-game
│   ├── sounds/                # Drop .ogg files here (see Optional section)
│   └── images/                # Reserved for future sprite sheets
│
└── saves/
    └── leaderboard.json       # Auto-created on first run
```

---

## 🚀 Quick Start

### Step 1: Install Python
- Download Python **3.10+** from [python.org](https://www.python.org/)
- ✅ **Important**: Check "Add Python to PATH" during installation

### Step 2: Create Virtual Environment (Recommended)

**Windows (PowerShell):**
```powershell
cd C:\Users\YourName\Downloads\FRUITNINJA
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
cd ~/Downloads/FRUITNINJA
python3 -m venv venv
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt after activation.

### Step 3: Install Dependencies

```bash
pip install -r "requirements (1).txt"
```

This installs:
- `opencv-python` — webcam capture & image processing
- `mediapipe` — hand tracking & gesture detection (~50 MB)
- `pygame` — game engine & graphics
- `numpy` — numerical computations

**Installation takes 1–3 minutes** depending on your internet speed.

### Step 4: Run the Game

```bash
python main.py
```

A **1280×720 window** opens. Point your index finger at your webcam and move it to slice fruits!

---

## ⌨️ Keyboard Shortcuts (In-Game)

| Key | Action |
|-----|--------|
| **ESC** | Pause / Unpause game |
| **F3** | Toggle FPS counter (top-left) |
| **F4** | Toggle debug mode (shows hand landmarks on webcam) |
| **F11** | Toggle fullscreen mode |

---

## 🎨 Optional: Add Custom Fonts

Makes the game look much better!

1. Go to [fonts.google.com](https://fonts.google.com)
2. Download a font (recommended: **Orbitron** or **Exo 2**)
3. Extract the `.ttf` file
4. Drop it into `assets/fonts/`
5. Restart the game — it picks it up automatically

---

## 🔊 Optional: Add Sound Effects

Drop `.ogg` files with these exact names into `assets/sounds/`:

| Filename | Purpose |
|----------|---------|
| `slice.ogg` | Fruit slice sound |
| `bomb.ogg` | Bomb explosion |
| `combo.ogg` | Combo milestone reached |
| `power.ogg` | Power-up activated |
| `miss.ogg` | Fruit missed (fell off screen) |
| `menu_tick.ogg` | Menu selection click |
| `game_over.ogg` | Game over fanfare |
| `shield.ogg` | Shield activation |
| `double.ogg` | Double points power-up |
| `bgm.ogg` | Background music (looped) |

**Free sound sources:**
- [freesound.org](https://freesound.org)
- [zapsplat.com](https://www.zapsplat.com)
- [opengameart.org](https://opengameart.org)

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| **"No module named mediapipe"** | Run `pip install mediapipe` (needs Python 3.10/3.11) |
| **Webcam not detected** | Try changing `CAMERA_INDEX = 0` to `1` or `2` in `settings.py` |
| **Hand not detected** | Improve room lighting; keep hand 40–80 cm from camera |
| **Very low FPS** | Lower `DETECTION_CONFIDENCE = 0.5` in `settings.py` |
| **Screen too small/big** | Change `SCREEN_W` and `SCREEN_H` in `settings.py` |
| **Pygame display error** | Make sure a monitor is connected (no headless mode) |
| **NumPy dtype error** | Run `pip install --upgrade numpy` |
| **Camera appears flipped** | Set `FLIP_CAMERA = False` in `settings.py` |

---

## 📊 Game Modes

### Classic Mode
- Slice fruits to score points
- Each fruit = 10 points
- Fast swipe bonus = +5 points
- Miss penalties = -1 life
- Bomb hits = -1 life
- 3 lives total

### Features
- **Difficulty scaling**: Fruit spawn rate increases with score
- **Combo system**: Chain slices for multiplier bonuses
- **Power-ups**: Shield, double points, slow-motion
- **Leaderboard**: Top 10 scores saved to `saves/leaderboard.json`

---

## 🔧 Customization

All game parameters are in `settings.py`:

```python
# Window size
SCREEN_W = 1280
SCREEN_H = 720

# Hand tracking confidence (0.0 - 1.0)
DETECTION_CONFIDENCE = 0.7
TRACKING_CONFIDENCE = 0.6

# Swipe speed thresholds (pixels/frame)
FAST_SWIPE_THRESHOLD = 25   # Bonus points if faster
SLOW_SWIPE_THRESHOLD = 5    # Minimum to register slice

# Difficulty scaling
INITIAL_SPAWN_INTERVAL = 90  # Frames between spawns
MIN_SPAWN_INTERVAL = 20      # Fastest spawn rate
BOMB_CHANCE = 0.12          # 12% chance per spawn

# Scoring
BASE_SLICE_POINTS = 10
FAST_SWIPE_BONUS = 5
MISS_PENALTY = 1
BOMB_LIVES_PENALTY = 1
```

---

## 📝 API Reference

### HandTracker (`hand_tracking.py`)
```python
tracker = HandTracker(cam_index=0)
tracker.update()  # Process one frame

# Access hand position & gesture
print(tracker.tip_pos)      # (x, y) in screen coords or None
print(tracker.gesture)      # "POINTING", "FIST", "TWO_FINGER", "OPEN_PALM", "NONE"
print(tracker.swipe_speed)  # pixels/frame
print(tracker.is_slicing)   # bool: moving fast enough to slice?
print(tracker.is_fast_swipe)# bool: fast enough for bonus?

tracker.release()  # Clean up webcam
```

### GameManager (`game_manager.py`)
```python
gm = GameManager(sound, particles, trail, shake, flash, bg, hud_ui)
gm.update_playing(tip_pos, gesture, swipe_speed, popups, fps)
gm.goto(STATE_PLAYING)  # Change game state
gm.start_game(mode="classic")
```

### Sound Manager (`sound_manager.py`)
```python
sound = SoundManager()
sound.play("slice")      # Play sound from assets/sounds/slice.ogg
sound.play_music()       # Loop background music
sound.stop_music()
sound.set_volume(0.5)    # 0.0 - 1.0
```

---

## 🎓 Learning Resources

- **MediaPipe Hands**: https://developers.google.com/mediapipe/solutions/vision/hand_landmarker
- **OpenCV**: https://opencv.org/
- **Pygame**: https://www.pygame.org/docs/
- **Hand Landmark Indices**: See `hand_tracking.py` for landmark definitions

---

## 📄 License

This project is provided as-is for educational purposes.

---

## ✨ Future Enhancements

- [ ] Multiplayer (split-screen)
- [ ] Different game modes (time attack, zen mode)
- [ ] Fruit combos (matched pairs = bonus)
- [ ] Leaderboard with dates/times
- [ ] Settings persistence (volume, brightness, etc.)
- [ ] Mobile version (Android/iOS)
- [ ] AI opponent mode

---

**Happy slicing! 🍎🍌🍉**
