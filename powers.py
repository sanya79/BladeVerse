"""
powers.py
=========
Blade Modes & Gesture Powers — the most spectacular visual layer of the game.

Classes:
  BladeModeManager  — handles Fire / Ice / Normal blade switching
  FireTrail         — animated flame particles along the blade
  IceTrail          — crystal/frost particles along the blade
  ShockwaveBlast    — expanding ring from fist gesture
  SlashArc          — anime-style directional slash streak
  SpeedLines        — manga speed-line burst (cinematic slow-mo entry)
  ImpactFlash       — directional screen-edge flash on heavy hit
  VoiceReactor      — triggers browser-TTS voice lines (if desired)
"""

import math
import random
import pygame
from settings import (
    SCREEN_W, SCREEN_H, TARGET_FPS,
    NEON_CYAN, NEON_PINK, NEON_GREEN, NEON_ORANGE, NEON_PURPLE,
    WHITE, BLACK, RED, GOLD,
)

# ── Blade mode constants ─────────────────────────────────────────────────────
BLADE_NORMAL = "normal"
BLADE_FIRE   = "fire"
BLADE_ICE    = "ice"

BLADE_FIRE_DURATION  = 300   # frames
BLADE_ICE_DURATION   = 300

# ── Color tables ─────────────────────────────────────────────────────────────
FIRE_COLORS = [(255, 40, 0), (255, 120, 0), (255, 200, 30), (255, 255, 120)]
ICE_COLORS  = [(180, 240, 255), (80, 200, 255), (200, 240, 255), (255, 255, 255)]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def _alpha_circle(surface, color, cx, cy, r, alpha):
    if r < 1 or alpha < 1:
        return
    s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color[:3], int(alpha)), (r + 1, r + 1), r)
    surface.blit(s, (int(cx) - r - 1, int(cy) - r - 1))


# ─────────────────────────────────────────────────────────────────────────────
# FIRE PARTICLE
# ─────────────────────────────────────────────────────────────────────────────
class FlameParticle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'max_life', 'r', 'color']

    def __init__(self, x, y, mode=BLADE_FIRE):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1, 4)
        self.x = float(x) + random.uniform(-4, 4)
        self.y = float(y) + random.uniform(-4, 4)
        self.vx = math.cos(angle) * speed * 0.6
        self.vy = math.sin(angle) * speed * 0.6 - random.uniform(0.5, 2.5)
        self.life = random.randint(10, 28)
        self.max_life = self.life
        self.r = random.randint(3, 9)
        palette = FIRE_COLORS if mode == BLADE_FIRE else ICE_COLORS
        self.color = random.choice(palette)

    def update(self):
        self.vy += 0.08 if self.color[0] > 200 else -0.05  # fire rises, ice falls
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.96
        self.life -= 1

    @property
    def alive(self): return self.life > 0

    def draw(self, surface):
        t = self.life / self.max_life
        r = max(1, int(self.r * t))
        a = int(220 * t)
        _alpha_circle(surface, self.color, self.x, self.y, r, a)
        # inner bright core
        _alpha_circle(surface, WHITE, self.x, self.y, max(1, r // 2), int(160 * t))


# ─────────────────────────────────────────────────────────────────────────────
# ICE CRYSTAL PARTICLE
# ─────────────────────────────────────────────────────────────────────────────
class IceCrystal:
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'max_life', 'size', 'angle', 'spin']

    def __init__(self, x, y):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(0.5, 3)
        self.x = float(x) + random.uniform(-6, 6)
        self.y = float(y) + random.uniform(-6, 6)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.randint(18, 35)
        self.max_life = self.life
        self.size = random.randint(4, 10)
        self.angle = random.uniform(0, 360)
        self.spin = random.uniform(-5, 5)

    def update(self):
        self.vy += 0.12
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.94
        self.angle += self.spin
        self.life -= 1

    @property
    def alive(self): return self.life > 0

    def draw(self, surface):
        t = self.life / self.max_life
        a = int(220 * t)
        s = max(2, int(self.size * t))
        surf = pygame.Surface((s * 4 + 2, s * 4 + 2), pygame.SRCALPHA)
        cx, cy = s * 2 + 1, s * 2 + 1
        # 6-pointed crystal
        for i in range(6):
            ang = math.radians(self.angle + i * 60)
            x2 = cx + int(s * 1.8 * math.cos(ang))
            y2 = cy + int(s * 1.8 * math.sin(ang))
            pygame.draw.line(surf, (*ICE_COLORS[1], a), (cx, cy), (x2, y2), max(1, s // 3))
        _alpha_circle(surf, ICE_COLORS[2], cx, cy, s // 2, a)
        surface.blit(surf, (int(self.x) - s * 2 - 1, int(self.y) - s * 2 - 1))


# ─────────────────────────────────────────────────────────────────────────────
# BLADE MODE MANAGER
# ─────────────────────────────────────────────────────────────────────────────
class BladeModeManager:
    """
    Tracks the current blade mode (normal / fire / ice) and emits the
    correct particles along the trail.  Also draws the activation flash
    when a mode is first triggered.
    """

    def __init__(self):
        self.mode          = BLADE_NORMAL
        self._timer        = 0
        self._particles    = []
        self._activate_anim= 0   # frames of activation burst
        self._burst_color  = WHITE

    # ── Public API ────────────────────────────────────────────────────────
    def activate_fire(self):
        self.mode = BLADE_FIRE
        self._timer = BLADE_FIRE_DURATION
        self._activate_anim = 25
        self._burst_color = (255, 120, 0)
        self._emit_activation_burst(50)

    def activate_ice(self):
        self.mode = BLADE_ICE
        self._timer = BLADE_ICE_DURATION
        self._activate_anim = 25
        self._burst_color = (100, 220, 255)
        self._emit_activation_burst(50)

    def deactivate(self):
        self.mode = BLADE_NORMAL
        self._timer = 0
        self._particles.clear()

    @property
    def is_active(self):
        return self.mode != BLADE_NORMAL

    @property
    def frames_left(self):
        return self._timer

    # ── Per-frame ─────────────────────────────────────────────────────────
    def update(self, tip_pos):
        """Call every frame with current fingertip position."""
        if self._timer > 0:
            self._timer -= 1
            if self._timer == 0:
                self.mode = BLADE_NORMAL

        if self._activate_anim > 0:
            self._activate_anim -= 1

        # Emit trail particles when tip is moving
        if tip_pos and self.mode != BLADE_NORMAL:
            count = 4 if self.mode == BLADE_FIRE else 3
            for _ in range(count):
                if self.mode == BLADE_FIRE:
                    self._particles.append(FlameParticle(tip_pos[0], tip_pos[1], BLADE_FIRE))
                else:
                    self._particles.append(IceCrystal(tip_pos[0], tip_pos[1]))

        # Update and prune
        self._particles = [p for p in self._particles if p.alive]
        for p in self._particles:
            p.update()

    def draw(self, surface: pygame.Surface, tip_pos):
        """Draw all blade particles + activation burst."""
        for p in self._particles:
            p.draw(surface)

        # Activation burst flash
        if self._activate_anim > 0 and tip_pos:
            t = self._activate_anim / 25
            r = int((25 - self._activate_anim) * 8)
            _alpha_circle(surface, self._burst_color, tip_pos[0], tip_pos[1],
                          r, int(200 * t))
            _alpha_circle(surface, WHITE, tip_pos[0], tip_pos[1],
                          r // 2, int(180 * t))

        # Mode timer arc around tip
        if self.mode != BLADE_NORMAL and tip_pos and self._timer > 0:
            self._draw_mode_hud(surface, tip_pos)

    def get_damage_mult(self):
        """Fire blade deals 1.5× damage (points), ice blade 1.3×."""
        if self.mode == BLADE_FIRE:  return 1.5
        if self.mode == BLADE_ICE:   return 1.3
        return 1.0

    def get_trail_color(self):
        if self.mode == BLADE_FIRE: return (255, 120, 0)
        if self.mode == BLADE_ICE:  return (80, 200, 255)
        return (0, 220, 255)

    # ── Private ───────────────────────────────────────────────────────────
    def _emit_activation_burst(self, count):
        cx, cy = SCREEN_W // 2, SCREEN_H // 2
        for _ in range(count):
            if self.mode == BLADE_FIRE:
                self._particles.append(FlameParticle(cx, cy, BLADE_FIRE))
            else:
                self._particles.append(IceCrystal(cx, cy))

    def _draw_mode_hud(self, surface, tip_pos):
        """Small arc timer around the fingertip."""
        max_t = BLADE_FIRE_DURATION if self.mode == BLADE_FIRE else BLADE_ICE_DURATION
        frac  = self._timer / max_t
        color = FIRE_COLORS[0] if self.mode == BLADE_FIRE else ICE_COLORS[1]
        r_arc = 22
        try:
            rect = pygame.Rect(tip_pos[0] - r_arc, tip_pos[1] - r_arc,
                               r_arc * 2, r_arc * 2)
            pygame.draw.arc(surface, (*color, 200), rect,
                            math.radians(90), math.radians(90 + 360 * frac), 3)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# SHOCKWAVE BLAST  (fist gesture)
# ─────────────────────────────────────────────────────────────────────────────
class ShockwaveBlast:
    """
    Expanding concentric rings that radiate out from the hand origin.
    Kills / pushes all fruits in radius.
    """

    def __init__(self, cx, cy, color=(0, 220, 255)):
        self.cx     = cx
        self.cy     = cy
        self.color  = color
        self.rings  = [{'r': 0, 'life': 40, 'max': 40, 'speed': 14 + i * 4}
                       for i in range(3)]
        self.alive  = True
        # Debris particles
        self._debris = [_DebrisParticle(cx, cy) for _ in range(30)]

    def update(self):
        for ring in self.rings:
            ring['r']    += ring['speed']
            ring['life'] -= 1
        for d in self._debris:
            d.update()
        self._debris = [d for d in self._debris if d.alive]
        self.alive = any(r['life'] > 0 for r in self.rings)

    def draw(self, surface):
        for d in self._debris:
            d.draw(surface)
        for ring in self.rings:
            if ring['life'] <= 0:
                continue
            t   = ring['life'] / ring['max']
            a   = int(220 * t ** 0.5)
            r   = int(ring['r'])
            w   = max(1, int(5 * t))
            s   = pygame.Surface((r * 2 + w + 2, r * 2 + w + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*self.color, a),
                               (r + w // 2 + 1, r + w // 2 + 1), r, w)
            # outer glow
            pygame.draw.circle(s, (*self.color, a // 3),
                               (r + w // 2 + 1, r + w // 2 + 1), r + 4, 2)
            surface.blit(s, (int(self.cx) - r - w // 2 - 1,
                              int(self.cy) - r - w // 2 - 1))

    def get_radius(self):
        return max(r['r'] for r in self.rings)


class _DebrisParticle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'max_life', 'r']

    def __init__(self, cx, cy):
        a = random.uniform(0, math.tau)
        s = random.uniform(2, 10)
        self.x  = float(cx);   self.y  = float(cy)
        self.vx = math.cos(a) * s;   self.vy = math.sin(a) * s
        self.life = random.randint(15, 35); self.max_life = self.life
        self.r = random.randint(2, 5)

    def update(self):
        self.vy += 0.3; self.x += self.vx; self.y += self.vy
        self.vx *= 0.92; self.life -= 1

    @property
    def alive(self): return self.life > 0

    def draw(self, surface):
        t = self.life / self.max_life
        _alpha_circle(surface, (0, 220, 255), self.x, self.y,
                      max(1, int(self.r * t)), int(200 * t))


# ─────────────────────────────────────────────────────────────────────────────
# SLASH ARC  (anime directional slash streak)
# ─────────────────────────────────────────────────────────────────────────────
class SlashArc:
    """
    Single curved arc drawn between two points — like an anime sword slash.
    Created whenever the blade moves fast enough.
    """

    def __init__(self, p1, p2, color=(255, 255, 255), speed_mult=1.0):
        self.p1    = p1
        self.p2    = p2
        self.color = color
        self.life  = 18
        self.max_l = 18
        self.width = max(2, int(8 * min(speed_mult / 20, 1.5)))
        # Midpoint offset for curve
        mx = (p1[0] + p2[0]) / 2
        my = (p1[1] + p2[1]) / 2
        dx = p2[0] - p1[0]; dy = p2[1] - p1[1]
        perp = (-dy, dx)
        mag  = (perp[0]**2 + perp[1]**2) ** 0.5 or 1
        off  = random.uniform(-20, 20)
        self.ctrl = (mx + perp[0] / mag * off, my + perp[1] / mag * off)

    @property
    def alive(self): return self.life > 0

    def update(self): self.life -= 1

    def draw(self, surface):
        if not self.alive: return
        t = self.life / self.max_l
        a = int(240 * t ** 0.6)
        pts = []
        for i in range(16):
            s = i / 15
            # Quadratic bezier
            x = int((1-s)**2 * self.p1[0] + 2*(1-s)*s*self.ctrl[0] + s**2*self.p2[0])
            y = int((1-s)**2 * self.p1[1] + 2*(1-s)*s*self.ctrl[1] + s**2*self.p2[1])
            pts.append((x, y))
        if len(pts) >= 2:
            w = max(1, int(self.width * t))
            # Outer glow
            surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.lines(surf, (*self.color, a // 3), False, pts, w + 6)
            pygame.draw.lines(surf, (*self.color, a),      False, pts, w)
            # White core
            pygame.draw.lines(surf, (255, 255, 255, int(180 * t)), False, pts, max(1, w // 2))
            surface.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)


# ─────────────────────────────────────────────────────────────────────────────
# SPEED LINES  (manga burst — triggers at combo entry)
# ─────────────────────────────────────────────────────────────────────────────
class SpeedLines:
    """Radial manga-style speed lines from screen centre."""

    def __init__(self, cx=None, cy=None, count=40, color=(255, 255, 255)):
        self.cx    = cx or SCREEN_W // 2
        self.cy    = cy or SCREEN_H // 2
        self.life  = 22
        self.max_l = 22
        self.color = color
        self.lines = []
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            near  = random.uniform(60, 120)
            far   = random.uniform(300, max(SCREEN_W, SCREEN_H))
            self.lines.append((angle, near, far))

    @property
    def alive(self): return self.life > 0

    def update(self): self.life -= 1

    def draw(self, surface):
        if not self.alive: return
        t = self.life / self.max_l
        a = int(160 * t ** 0.5)
        surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for angle, near, far in self.lines:
            nx = int(self.cx + math.cos(angle) * near)
            ny = int(self.cy + math.sin(angle) * near)
            fx = int(self.cx + math.cos(angle) * far)
            fy = int(self.cy + math.sin(angle) * far)
            pygame.draw.line(surf, (*self.color, a), (nx, ny), (fx, fy), 1)
        surface.blit(surf, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)


# ─────────────────────────────────────────────────────────────────────────────
# IMPACT FLASH  (edge vignette flash)
# ─────────────────────────────────────────────────────────────────────────────
class ImpactFlash:
    """Directional edge glow — different colour per event type."""

    def __init__(self, color=(255, 80, 0), duration=12):
        self.color    = color
        self.life     = duration
        self.max_life = duration

    @property
    def alive(self): return self.life > 0

    def update(self): self.life -= 1

    def draw(self, surface):
        if not self.alive: return
        t = self.life / self.max_life
        a = int(140 * t ** 0.7)
        surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        # Radial gradient border (4 corners)
        border = 80
        pygame.draw.rect(surf, (*self.color, a),
                         (0, 0, SCREEN_W, border))
        pygame.draw.rect(surf, (*self.color, a),
                         (0, SCREEN_H - border, SCREEN_W, border))
        pygame.draw.rect(surf, (*self.color, a),
                         (0, 0, border, SCREEN_H))
        pygame.draw.rect(surf, (*self.color, a),
                         (SCREEN_W - border, 0, border, SCREEN_H))
        surface.blit(surf, (0, 0))


# ─────────────────────────────────────────────────────────────────────────────
# VOICE REACTOR  (browser-TTS wrapper — works via subprocess on desktop)
# ─────────────────────────────────────────────────────────────────────────────
class VoiceReactor:
    """
    Optional voice feedback.  Uses espeak/say if available.
    Silently skips on platforms where it's not.
    Falls back to in-game text popups (always enabled).
    """
    LINES = {
        "combo"       : ["COMBO!", "Keep going!", "Chain!", "Nice!"],
        "perfect"     : ["Perfect slice!", "Excellent!", "Flawless!"],
        "ultra"       : ["ULTRA SLASH!", "LEGENDARY!"],
        "boss"        : ["Boss incoming!", "Watch out!"],
        "victory"     : ["Victory!", "You win!", "Outstanding!"],
        "shield"      : ["Shield activated!"],
        "fire_blade"  : ["Fire blade!"],
        "ice_blade"   : ["Ice blade!"],
    }

    def __init__(self, enabled=False):
        self.enabled = enabled
        self._cooldown = 0
        self._import_ok = False
        if enabled:
            try:
                import subprocess
                self._subprocess = subprocess
                self._import_ok  = True
            except ImportError:
                pass

    def say(self, event_key: str):
        self._cooldown = max(0, self._cooldown - 1)
        if not self.enabled or not self._import_ok or self._cooldown > 0:
            return
        lines = self.LINES.get(event_key, [])
        if not lines:
            return
        text = random.choice(lines)
        try:
            import sys
            if sys.platform == "darwin":
                self._subprocess.Popen(["say", text],
                                       stdout=self._subprocess.DEVNULL,
                                       stderr=self._subprocess.DEVNULL)
            else:
                self._subprocess.Popen(["espeak", text],
                                       stdout=self._subprocess.DEVNULL,
                                       stderr=self._subprocess.DEVNULL)
            self._cooldown = 60
        except Exception:
            pass

    def update(self):
        if self._cooldown > 0:
            self._cooldown -= 1