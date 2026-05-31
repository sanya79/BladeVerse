"""
effects.py  (FULL UPGRADE)
==========================
• BladeTrail      — multi-layer neon glow trail, color-mode aware
• ParticleSystem  — physics juice / sparks / boss explosion
• ComboPopup      — floating score text
• ScreenShake     — camera shake (normal + heavy for boss)
• HitFlash        — full-screen flash
• BackgroundRenderer — thin wrapper; DynamicBackground is now primary
• HandCursor      — glowing finger cursor + gesture badge
• JuiceSplash     — realistic arced droplets per fruit color
• AnimeSlash      — speed lines + arc on fast swipe
"""

import math, random
import pygame
from settings import (
    SCREEN_W, SCREEN_H,
    TRAIL_LENGTH, TRAIL_MIN_ALPHA, TRAIL_MAX_ALPHA,
    TRAIL_BASE_WIDTH, TRAIL_GLOW_PASSES,
    NEON_CYAN, NEON_PINK, NEON_GREEN, NEON_ORANGE, NEON_PURPLE,
    PARTICLE_COUNT, PARTICLE_LIFE, PARTICLE_SPEED,
    JUICE_SPLASH_COUNT,
    SCREEN_SHAKE_FRAMES, SCREEN_SHAKE_INTENSITY,
    THEME_CYBERPUNK, THEME_DOJO, THEME_SPACE, THEME_GRADIENTS,
    WHITE, BLACK,
)


def _circ(surf, color, cx, cy, r, alpha=255):
    if r < 1: return
    s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color[:3], int(alpha)), (r+1, r+1), r)
    surf.blit(s, (int(cx)-r-1, int(cy)-r-1))

def _lerp_color(c1, c2, t):
    return tuple(int(c1[i]+(c2[i]-c1[i])*t) for i in range(3))


# ─── BLADE TRAIL ─────────────────────────────────────────────────────────────
class BladeTrail:
    def __init__(self):
        self.points: list = []
        self._surf   = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self._color1 = NEON_CYAN
        self._color2 = NEON_PINK
        self._mode   = "normal"   # "normal" | "fire" | "ice"

    def set_mode(self, mode: str):
        self._mode = mode
        if mode == "fire":
            self._color1 = (255, 120, 0)
            self._color2 = (255, 40,  0)
        elif mode == "ice":
            self._color1 = (80,  200, 255)
            self._color2 = (200, 240, 255)
        else:
            self._color1 = NEON_CYAN
            self._color2 = NEON_PINK

    def add_point(self, pos):
        if pos is None:
            if self.points: self.points.pop(0)
            return
        self.points.append(pos)
        if len(self.points) > TRAIL_LENGTH:
            self.points.pop(0)

    def draw(self, surface: pygame.Surface):
        if len(self.points) < 2: return
        self._surf.fill((0, 0, 0, 0))
        n = len(self.points)

        for i in range(1, n):
            t      = i / n
            alpha  = int(TRAIL_MIN_ALPHA + t*(TRAIL_MAX_ALPHA-TRAIL_MIN_ALPHA))
            width  = max(1, int(TRAIL_BASE_WIDTH * t))
            p1, p2 = self.points[i-1], self.points[i]
            hue_t  = (t + 0.1) % 1.0
            gc     = _lerp_color(self._color1, self._color2, hue_t)

            # White core
            pygame.draw.line(self._surf, (*WHITE, alpha), p1, p2, width)
            # Colour glow layers
            for g in range(1, TRAIL_GLOW_PASSES+1):
                gw = width + g*5
                ga = max(0, alpha//(g+1))
                pygame.draw.line(self._surf, (*gc, ga), p1, p2, gw)

        surface.blit(self._surf, (0,0), special_flags=pygame.BLEND_RGBA_ADD)

        # Tip dot
        if self.points:
            tip = self.points[-1]
            _circ(surface, WHITE,           tip[0], tip[1], TRAIL_BASE_WIDTH+2, 200)
            _circ(surface, self._color1,    tip[0], tip[1], TRAIL_BASE_WIDTH+7, 80)


# ─── JUICE DROPLET ───────────────────────────────────────────────────────────
class JuiceDroplet:
    __slots__ = ['x','y','vx','vy','life','max_life','r','color']
    def __init__(self, x, y, color):
        a     = random.uniform(0, math.tau)
        speed = random.uniform(2, 9)
        self.x = float(x); self.y = float(y)
        self.vx = math.cos(a)*speed; self.vy = math.sin(a)*speed - random.uniform(1,4)
        self.life = random.randint(25, 50); self.max_life = self.life
        self.r = random.randint(2, 7)
        self.color = color

    def update(self):
        self.vy += 0.25; self.x += self.vx; self.y += self.vy
        self.vx *= 0.95; self.life -= 1

    @property
    def alive(self): return self.life > 0

    def draw(self, surface):
        t = self.life/self.max_life
        r = max(1, int(self.r*t))
        a = int(240*t)
        _circ(surface, self.color, self.x, self.y, r, a)
        # Tiny white glint
        _circ(surface, WHITE, self.x - r//3, self.y - r//3, max(1,r//3), int(180*t))


# ─── PARTICLE ────────────────────────────────────────────────────────────────
class Particle:
    __slots__ = ['x','y','vx','vy','life','max_life','color','radius','gravity']
    def __init__(self, x, y, color, speed_mult=1.0):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.5, PARTICLE_SPEED)*speed_mult
        self.x = float(x); self.y = float(y)
        self.vx = math.cos(angle)*speed; self.vy = math.sin(angle)*speed - random.uniform(0,2)
        self.life = PARTICLE_LIFE; self.max_life = PARTICLE_LIFE
        self.color  = color
        self.radius = random.randint(2, 6)
        self.gravity= 0.18

    def update(self):
        self.vy += self.gravity; self.x += self.vx; self.y += self.vy; self.life -= 1

    @property
    def alive(self): return self.life > 0

    def draw(self, surface):
        a = int(255*self.life/self.max_life)
        r = max(1, int(self.radius*self.life/self.max_life))
        _circ(surface, self.color, self.x, self.y, r, a)


# ─── PARTICLE SYSTEM ─────────────────────────────────────────────────────────
class ParticleSystem:
    def __init__(self):
        self.particles: list = []
        self._juice:    list = []

    def emit_slice(self, x, y, color_outer, color_inner):
        for _ in range(PARTICLE_COUNT):
            c = random.choice([color_outer, color_inner, WHITE])
            self.particles.append(Particle(x, y, c))
        for _ in range(JUICE_SPLASH_COUNT):
            self._juice.append(JuiceDroplet(x, y, color_outer))
            self._juice.append(JuiceDroplet(x, y, color_inner))

    def emit_bomb(self, x, y):
        for _ in range(PARTICLE_COUNT*2):
            c = random.choice([(255,80,0),(255,200,0),(220,30,30),WHITE])
            self.particles.append(Particle(x, y, c, speed_mult=1.8))

    def emit_power(self, x, y, color):
        for _ in range(PARTICLE_COUNT):
            self.particles.append(Particle(x, y, color, speed_mult=0.8))

    def emit_boss_explosion(self, x, y):
        """Extra-large burst for boss death."""
        for _ in range(PARTICLE_COUNT*4):
            c = random.choice([(255,40,80),(255,120,0),(255,200,0),(200,0,255),WHITE])
            self.particles.append(Particle(x, y, c, speed_mult=2.5))
        for _ in range(40):
            self._juice.append(JuiceDroplet(x, y, (255,80,0)))

    def update(self):
        self.particles = [p for p in self.particles if p.alive]
        self._juice     = [j for j in self._juice if j.alive]
        for p in self.particles: p.update()
        for j in self._juice:    j.update()

    def draw(self, surface: pygame.Surface):
        for j in self._juice:    j.draw(surface)
        for p in self.particles: p.draw(surface)

    def clear(self):
        self.particles.clear(); self._juice.clear()


# ─── COMBO POPUP ─────────────────────────────────────────────────────────────
class ComboPopup:
    def __init__(self, text, x, y, color=NEON_GREEN, font=None):
        self.text  = text; self.x = float(x); self.y = float(y)
        self.color = color; self.life = 60; self.max_l = 60; self.vy = -1.5
        self.font  = font or pygame.font.SysFont("Consolas", 32, bold=True)
        self._rendered = self.font.render(text, True, color)

    @property
    def alive(self): return self.life > 0

    def update(self):
        self.y += self.vy; self.life -= 1; self.vy *= 0.97

    def draw(self, surface):
        a = int(255*(self.life/self.max_l)**0.5)
        s = self._rendered.copy(); s.set_alpha(a)
        surface.blit(s, s.get_rect(center=(int(self.x),int(self.y))))


# ─── SCREEN SHAKE ────────────────────────────────────────────────────────────
class ScreenShake:
    def __init__(self):
        self._frames_left = 0; self._intensity = 0

    def trigger(self, intensity=SCREEN_SHAKE_INTENSITY, duration=SCREEN_SHAKE_FRAMES):
        self._intensity = intensity; self._frames_left = duration

    def trigger_heavy(self):
        """Boss hit / ultra combo."""
        self.trigger(intensity=22, duration=28)

    def update(self):
        if self._frames_left > 0: self._frames_left -= 1

    @property
    def offset(self):
        if self._frames_left <= 0: return (0,0)
        decay = self._frames_left/SCREEN_SHAKE_FRAMES
        mag   = int(self._intensity*decay)
        return (random.randint(-mag,mag), random.randint(-mag,mag))


# ─── HIT FLASH ───────────────────────────────────────────────────────────────
class HitFlash:
    def __init__(self):
        self._life = 0; self._color = (255,0,0)
        self._surf = pygame.Surface((SCREEN_W,SCREEN_H), pygame.SRCALPHA)

    def trigger(self, color=(255,255,255), duration=12):
        self._color=color; self._life=duration; self._max=duration

    def update(self):
        if self._life > 0: self._life -= 1

    def draw(self, surface):
        if self._life <= 0: return
        a = int(160*(self._life/self._max))
        self._surf.fill((*self._color, a))
        surface.blit(self._surf, (0,0))


# ─── BACKGROUND RENDERER (legacy thin wrapper) ───────────────────────────────
class BackgroundRenderer:
    """
    Thin wrapper kept for compatibility with the original main.py.
    The heavy lifting is now done by DynamicBackground in animations.py.
    This class draws a simple gradient + minimal overlay.
    """
    def __init__(self, theme=THEME_CYBERPUNK):
        self.theme = theme
        self._tick = 0
        self._gradient = self._make_gradient(theme)

    def set_theme(self, theme):
        self.theme = theme
        self._gradient = self._make_gradient(theme)

    def _make_gradient(self, theme):
        stops = THEME_GRADIENTS.get(theme, THEME_GRADIENTS[THEME_CYBERPUNK])
        surf  = pygame.Surface((SCREEN_W, SCREEN_H))
        top, bot = stops[0], stops[1]
        for y in range(SCREEN_H):
            t = y/SCREEN_H
            c = tuple(int(top[i]+(bot[i]-top[i])*t) for i in range(3))
            pygame.draw.line(surf, c, (0,y), (SCREEN_W,y))
        return surf

    def draw(self, surface):
        self._tick += 1
        surface.blit(self._gradient, (0,0))
        # Subtle scanlines
        scan = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        offset = (self._tick*2) % SCREEN_H
        for y in range(0, SCREEN_H, 4):
            ys = (y+offset) % SCREEN_H
            pygame.draw.line(scan, (0,255,255,5), (0,ys), (SCREEN_W,ys))
        surface.blit(scan, (0,0))


# ─── HAND CURSOR ─────────────────────────────────────────────────────────────
class HandCursor:
    GESTURE_COLORS = {
        "POINTING":   (0,   255, 255),
        "FIST":       (0,   255, 100),
        "TWO_FINGER": (255, 200, 0),
        "OPEN_PALM":  (180, 80,  255),
        "OTHER":      (200, 200, 200),
        "NONE":       (80,  80,  80),
    }
    GESTURE_LABELS = {
        "POINTING":   "BLADE",
        "FIST":       "SHIELD",
        "TWO_FINGER": "COMBO",
        "OPEN_PALM":  "SLOW-MO",
    }

    def __init__(self):
        self._tick = 0; self._font = None
        self._last_gesture = "NONE"; self._label_alpha = 0

    def _get_font(self):
        if not self._font:
            self._font = pygame.font.SysFont("Consolas", 22, bold=True)
        return self._font

    def draw(self, surface, tip_pos, gesture, swipe_speed):
        self._tick += 1
        if tip_pos is None:
            self._label_alpha = max(0, self._label_alpha-8); return
        ix, iy = tip_pos
        color  = self.GESTURE_COLORS.get(gesture, (200,200,200))
        pulse  = 0.6 + 0.4*math.sin(self._tick*0.15)

        # Multi-ring glow
        for r in range(5, 0, -1):
            a = int(35*(r/5)*pulse)
            _circ(surface, color, ix, iy, 8+r*5, a)

        # Core dot
        _circ(surface, color, ix, iy, 10, int(220*pulse))
        _circ(surface, WHITE, ix, iy, 5,  int(180*pulse))

        # Speed ring
        if swipe_speed > 5:
            sr = min(55, int(swipe_speed*1.6))
            _circ(surface, color, ix, iy, sr, int(min(180,swipe_speed*3)))
            # Decrement ring (outline only)
            s2 = pygame.Surface((sr*2+6, sr*2+6), pygame.SRCALPHA)
            pygame.draw.circle(s2, (*color, int(min(180,swipe_speed*2))), (sr+3,sr+3), sr, 2)
            surface.blit(s2, (ix-sr-3, iy-sr-3))

        # Gesture label
        label = self.GESTURE_LABELS.get(gesture,"")
        if gesture != self._last_gesture and label:
            self._label_alpha = 255; self._last_gesture = gesture
        else:
            self._label_alpha = max(0, self._label_alpha-4)

        if label and self._label_alpha > 10:
            font = self._get_font()
            sh   = font.render(label, True, (0,0,0))
            sh.set_alpha(self._label_alpha//2)
            txt  = font.render(label, True, color)
            txt.set_alpha(self._label_alpha)
            lx, ly = ix+18, iy-32
            surface.blit(sh,  (lx+2, ly+2))
            surface.blit(txt, (lx, ly))