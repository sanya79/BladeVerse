# 🚀 FRUIT NINJA - Complete Installation Guide

This guide walks you through setting up and running the Gesture-Controlled Fruit Ninja game on your Windows, macOS, or Linux computer.

---

## ✅ System Requirements

- **Python**: 3.10 or higher
- **RAM**: 4 GB minimum
- **Webcam**: Required (built-in or USB)
- **Display**: 1280×720 or higher recommended

---

## 📦 Installation Steps

### Windows Setup (Easiest Method)

#### Method 1: Automatic Setup Script

1. **Open PowerShell** in the FRUITNINJA folder
   - Right-click the folder → "Open with PowerShell"

2. **Run the setup script**:
   ```powershell
   .\setup.bat
   ```

3. The script will:
   - ✓ Create a virtual environment
   - ✓ Install all dependencies
   - ✓ Show you next steps

#### Method 2: Manual Setup

1. **Create virtual environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   
   You should see `(venv)` in your terminal prompt.

2. **Install dependencies**:
   ```powershell
   pip install -r "requirements (1).txt"
   ```

3. **Run the game**:
   ```powershell
   python launcher.py
   ```
   
   Or directly:
   ```powershell
   python main.py
   ```

---

### macOS / Linux Setup

1. **Open Terminal** in the FRUITNINJA folder

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
   
   You should see `(venv)` in your terminal prompt.

3. **Install dependencies**:
   ```bash
   pip install -r "requirements (1).txt"
   ```

4. **Run the game**:
   ```bash
   python launcher.py
   ```
   
   Or directly:
   ```bash
   python main.py
   ```

---

## 🎮 Running the Game

### Quick Start (Once Setup Complete)

**Windows (PowerShell)**:
```powershell
.\venv\Scripts\Activate.ps1
python main.py
```

**macOS / Linux (Terminal)**:
```bash
source venv/bin/activate
python main.py
```

### Using the Launcher (Recommended)

```bash
python launcher.py
```

The launcher will:
- ✓ Check Python version
- ✓ Verify all dependencies are installed
- ✓ Create missing directories
- ✓ Display game controls
- ✓ Start the game

---

## 🎮 In-Game Controls

### Gestures (Webcam)

| Gesture | Action |
|---------|--------|
| **Index Finger Pointing** | Normal slicing mode (default) |
| **Fist** | Activate shield for 8 seconds |
| **Two Fingers** (Index + Middle) | Combo multiplier mode |
| **Open Palm** | Slow-motion effect (6 seconds) |

### Keyboard

| Key | Action |
|-----|--------|
| **ESC** | Pause / Unpause game |
| **F3** | Toggle FPS counter (top-left corner) |
| **F4** | Toggle debug mode (shows hand landmarks) |
| **F11** | Toggle fullscreen mode |
| **Q** | Quit game |

---

## 🎨 Customization

### Adding Custom Fonts

1. Download a font from [Google Fonts](https://fonts.google.com)
   - Recommended: **Orbitron**, **Exo 2**, or **JetBrains Mono**

2. Extract the `.ttf` file

3. Copy it to `assets/fonts/`

4. Restart the game

The game will automatically use any `.ttf` font found in `assets/fonts/`.

### Adding Sound Effects

1. Find `.ogg` or `.wav` files from:
   - [Freesound.org](https://freesound.org)
   - [Zapsplat](https://www.zapsplat.com)
   - [OpenGameArt](https://opengameart.org)

2. Place files in `assets/sounds/` with these exact names:
   - `slice.ogg` - Fruit slice
   - `bomb.ogg` - Bomb explosion
   - `combo.ogg` - Combo reached
   - `power.ogg` - Power-up
   - `miss.ogg` - Fruit missed
   - `menu_tick.ogg` - Menu click
   - `game_over.ogg` - Game over
   - `shield.ogg` - Shield activated
   - `double.ogg` - 2× multiplier
   - `bgm.ogg` - Background music (looped)

3. Restart the game

### Tuning Game Parameters

Edit `settings.py` to customize:

```python
# Window size
SCREEN_W = 1280
SCREEN_H = 720

# Hand detection sensitivity (0.0-1.0, higher = stricter)
DETECTION_CONFIDENCE = 0.7
TRACKING_CONFIDENCE = 0.6

# Swipe speed thresholds
FAST_SWIPE_THRESHOLD = 25      # Pixels/frame for bonus
SLOW_SWIPE_THRESHOLD = 5       # Minimum for slice

# Spawn rates
INITIAL_SPAWN_INTERVAL = 90    # Frames between spawns at start
MIN_SPAWN_INTERVAL = 20        # Fastest spawn rate
BOMB_CHANCE = 0.12            # 12% chance per spawn

# Scoring
BASE_SLICE_POINTS = 10
FAST_SWIPE_BONUS = 5
MISS_PENALTY = 1
BOMB_LIVES_PENALTY = 1

# Volume levels (0.0-1.0)
MUSIC_VOLUME = 0.35
SFX_VOLUME = 0.7
VOICE_VOLUME = 0.85
```

Save and restart the game for changes to take effect.

---

## 🔧 Troubleshooting

### "No module named 'mediapipe'"

**Windows**:
```powershell
.\venv\Scripts\Activate.ps1
pip install --upgrade mediapipe
```

**macOS / Linux**:
```bash
source venv/bin/activate
pip install --upgrade mediapipe
```

### Webcam Not Detected

1. **Check camera permission**: Ensure the app has webcam access
   - Windows: Settings → Privacy & Security → Webcam
   - macOS: System Preferences → Security & Privacy → Camera
   - Linux: Check `/etc/group` permissions

2. **Try different camera index** in `settings.py`:
   ```python
   CAMERA_INDEX = 0  # Try 1, 2, 3, etc.
   ```

3. **Test webcam**:
   ```bash
   python -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"
   ```

### Hand Not Detected in Game

1. **Improve lighting**: Ensure good room lighting (no shadows)

2. **Keep proper distance**: Hold hand 40-80 cm from camera

3. **Reduce detection confidence** in `settings.py`:
   ```python
   DETECTION_CONFIDENCE = 0.5  # Lower = more lenient
   ```

4. **Enable debug mode** (F4) to see hand landmarks

### Game Runs Slowly (Low FPS)

1. **Lower detection confidence** in `settings.py`:
   ```python
   DETECTION_CONFIDENCE = 0.5
   ```

2. **Reduce window size**:
   ```python
   SCREEN_W = 1024
   SCREEN_H = 576
   ```

3. **Close other applications** to free up CPU/GPU

### Camera Image Appears Flipped

Edit `settings.py`:
```python
FLIP_CAMERA = False  # Default is True for mirrored view
```

### No Sound

1. Check `MUSIC_VOLUME` and `SFX_VOLUME` in `settings.py`
2. Verify `.ogg` files exist in `assets/sounds/`
3. Check system volume is not muted

### "pygame display error"

Ensure:
- A monitor is connected (game doesn't run in headless mode)
- GPU drivers are up-to-date
- Try toggling fullscreen (F11)

---

## 📊 Game Features

### Scoring System

- **Fruit slice**: +10 points (base)
- **Fast swipe bonus**: +5 points (if swipe speed > FAST_SWIPE_THRESHOLD)
- **Combo multiplier**: 1.5× to 5× depending on combo level
- **Miss penalty**: -1 life
- **Bomb hit**: -1 life

### Power-Ups

| Power-Up | Duration | Effect |
|----------|----------|--------|
| **Shield (Fist)** | 8 sec | Protects from 1 bomb |
| **Double Score** | 10 sec | All points × 2 |
| **Slow-Motion** | 8 sec | Game runs at 50% speed |
| **Freeze** | 6 sec | All fruits stop moving |

### Difficulty Scaling

- Fruit spawn rate increases with score
- Special fruits appear more frequently
- Bombs become more common at higher scores

---

## 📚 Project Files Reference

| File | Purpose |
|------|---------|
| `main.py` | Game loop and state manager |
| `settings.py` | All configuration constants |
| `hand_tracking.py` | MediaPipe hand detection wrapper |
| `fruit.py` | Fruit and bomb classes |
| `effects.py` | Visual effects (particles, trails, shake) |
| `sound_manager.py` | Audio system |
| `ui.py` | All UI screens and menus |
| `game_manager.py` | Game state and scoring logic |
| `launcher.py` | Game launcher with dependency check |
| `setup.bat` | Windows quick setup script |
| `requirements (1).txt` | Python dependencies |
| `SETUP_GUIDE.md` | Complete feature documentation |
| `INSTALL.md` | This file |

---

## 🎓 Learning Resources

- **MediaPipe Documentation**: https://developers.google.com/mediapipe
- **OpenCV Tutorials**: https://docs.opencv.org/master/d9/df8/tutorial_root.html
- **Pygame Documentation**: https://www.pygame.org/docs/
- **Python Hand Landmarks**: [MediaPipe Hand Landmarker](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker)

---

## 🐛 Reporting Issues

If you encounter problems:

1. **Check the Troubleshooting section** above
2. **Enable debug mode** (F4 in-game) to see hand detection
3. **Check console output** for error messages
4. **Verify all files** are in the correct directories
5. **Reinstall dependencies**: `pip install --upgrade -r "requirements (1).txt"`

---

## 🎉 You're Ready!

Everything is set up! Now:

1. **Activate the virtual environment** (Windows/macOS/Linux)
2. **Run the game**: `python main.py`
3. **Point your finger at the webcam**
4. **Start slicing fruits!**

Happy gaming! 🍎🍌🍉

---

**Need help?** Check the FAQ in `SETUP_GUIDE.md` or visit the project repository.
