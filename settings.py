"""
settings.py
===========
Central configuration hub for the entire game.
All constants, colors, thresholds, and tunable parameters live here.
Changing a value here propagates everywhere — no magic numbers in other files.
"""

import os

# ─────────────────────────────────────────────
# WINDOW & DISPLAY
# ─────────────────────────────────────────────
WINDOW_TITLE   = "⚡ BLADE HAND — Gesture Fruit Ninja"
SCREEN_W       = 1280
SCREEN_H       = 720
TARGET_FPS     = 60
FULLSCREEN     = False          # Toggle via Settings menu at runtime

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR     = os.path.join(BASE_DIR, "assets")
SOUNDS_DIR     = os.path.join(ASSETS_DIR, "sounds")
FONTS_DIR      = os.path.join(ASSETS_DIR, "fonts")
IMAGES_DIR     = os.path.join(ASSETS_DIR, "images")
SAVES_DIR      = os.path.join(BASE_DIR, "saves")
LEADERBOARD_FILE = os.path.join(SAVES_DIR, "leaderboard.json")
SETTINGS_FILE  = os.path.join(SAVES_DIR, "settings.json")

# ─────────────────────────────────────────────
# COLORS  (R, G, B) or (R, G, B, A)
# ─────────────────────────────────────────────
BLACK          = (0,   0,   0)
WHITE          = (255, 255, 255)
NEON_CYAN      = (0,   255, 255)
NEON_PINK      = (255, 0,   128)
NEON_GREEN     = (57,  255, 20)
NEON_YELLOW    = (255, 234, 0)
NEON_ORANGE    = (255, 100, 0)
NEON_PURPLE    = (180, 0,   255)
DEEP_BLUE      = (5,   5,   30)
DARK_PANEL     = (10,  10,  40,  200)
RED            = (220, 30,  30)
GOLD           = (255, 200, 0)
BLADE_COLOR    = (180, 230, 255)   # base sword trail colour
BOMB_COLOR     = (220, 50,  50)

# ─────────────────────────────────────────────
# HAND TRACKING
# ─────────────────────────────────────────────
MAX_HANDS              = 1
DETECTION_CONFIDENCE   = 0.7
TRACKING_CONFIDENCE    = 0.6
FLIP_CAMERA            = True      # mirror so it feels natural
CAMERA_INDEX           = 0

# Swipe speed thresholds (pixels per frame)
FAST_SWIPE_THRESHOLD   = 25        # gives bonus points
SLOW_SWIPE_THRESHOLD   = 5         # minimum to register a slice

# ─────────────────────────────────────────────
# BLADE / TRAIL
# ─────────────────────────────────────────────
TRAIL_LENGTH           = 22        # number of saved trail positions
TRAIL_MIN_ALPHA        = 10
TRAIL_MAX_ALPHA        = 220
TRAIL_BASE_WIDTH       = 6
TRAIL_GLOW_PASSES      = 3         # layered glow iterations

# ─────────────────────────────────────────────
# FRUIT PHYSICS
# ─────────────────────────────────────────────
GRAVITY                = 0.25      # pixels / frame²  (added to vy each frame)
FRUIT_RADIUS_MIN       = 28
FRUIT_RADIUS_MAX       = 46
FRUIT_SPEED_Y_MIN      = -18       # initial upward velocity (negative = up)
FRUIT_SPEED_Y_MAX      = -12
FRUIT_SPEED_X_MIN      = -4
FRUIT_SPEED_X_MAX      = 4
FRUIT_SPAWN_MARGIN     = 60        # don't spawn within this many px of edge

# ─────────────────────────────────────────────
# SPAWN / DIFFICULTY
# ─────────────────────────────────────────────
INITIAL_SPAWN_INTERVAL = 90        # frames between spawns at start
MIN_SPAWN_INTERVAL     = 20        # fastest possible spawn rate
SPAWN_INTERVAL_DECAY   = 2         # reduce interval every N points
BOMB_CHANCE            = 0.12      # 12 % of spawns are bombs
SPECIAL_FRUIT_CHANCE   = 0.08      # 8 % chance per spawn for a special fruit
SPEED_SCALE_FACTOR     = 0.003     # how much score boosts fruit speed

# ─────────────────────────────────────────────
# SCORING
# ─────────────────────────────────────────────
BASE_SLICE_POINTS      = 10
FAST_SWIPE_BONUS       = 5         # extra pts for fast swipe
MISS_PENALTY           = 1         # lives lost when fruit exits bottom
BOMB_LIVES_PENALTY     = 1         # lives lost when bomb hit
STARTING_LIVES         = 3
MAX_LIVES              = 3

# COMBO
COMBO_WINDOW           = 45        # frames within which next slice keeps combo
COMBO_2_MULT           = 1.5
COMBO_3_MULT           = 2.0
COMBO_5_MULT           = 3.0
COMBO_10_MULT          = 5.0

# ─────────────────────────────────────────────
# SPECIAL FRUITS
# ─────────────────────────────────────────────
FREEZE_DURATION        = 180       # frames all fruits are frozen
SLOW_MO_DURATION       = 240       # frames of slow-motion
DOUBLE_SCORE_DURATION  = 300       # frames of 2× score
SHIELD_DURATION        = 240       # frames of gesture-based shield

# ─────────────────────────────────────────────
# GESTURE POWERS
# ─────────────────────────────────────────────
FIST_SHIELD_DURATION   = 240       # frames shield stays after fist
TWOFINGER_COMBO_FRAMES = 150       # frames combo mode from two-finger
PALM_SLOWMO_FRAMES     = 200       # frames slow-motion from open palm

# ─────────────────────────────────────────────
# EFFECTS
# ─────────────────────────────────────────────
PARTICLE_COUNT         = 22        # particles per slice
PARTICLE_LIFE          = 35        # frames each particle lives
PARTICLE_SPEED         = 6
JUICE_SPLASH_COUNT     = 8
SCREEN_SHAKE_FRAMES    = 18        # on bomb hit
SCREEN_SHAKE_INTENSITY = 12

# ─────────────────────────────────────────────
# SOUND
# ─────────────────────────────────────────────
MUSIC_VOLUME           = 0.35
SFX_VOLUME             = 0.7
VOICE_VOLUME           = 0.85

# ─────────────────────────────────────────────
# UI / FONTS
# ─────────────────────────────────────────────
FONT_LARGE             = 72
FONT_MEDIUM            = 42
FONT_SMALL             = 28
FONT_TINY              = 20
HUD_PADDING            = 18

# ─────────────────────────────────────────────
# GAME MODES
# ─────────────────────────────────────────────
MODE_ARCADE            = "Arcade"
MODE_SURVIVAL          = "Survival"
MODE_TIME_ATTACK       = "Time Attack"
TIME_ATTACK_DURATION   = 60 * TARGET_FPS   # 60 seconds

# ─────────────────────────────────────────────
# BACKGROUND THEMES
# ─────────────────────────────────────────────
THEME_CYBERPUNK        = "Cyberpunk"
THEME_DOJO             = "Ninja Dojo"
THEME_SPACE            = "Space"
DEFAULT_THEME          = THEME_CYBERPUNK

# gradient stops per theme: list of (R, G, B) top → bottom
THEME_GRADIENTS = {
    THEME_CYBERPUNK: [(5,  5,  30), (15, 0,  40)],
    THEME_DOJO:      [(20, 5,  0),  (5,  15, 5)],
    THEME_SPACE:     [(0,  0,  10), (0,  5,  20)],
}

# ─────────────────────────────────────────────
# DEBUG
# ─────────────────────────────────────────────
DEBUG_MODE             = False     # Show bounding boxes, landmarks, fps graph
SHOW_FPS               = True