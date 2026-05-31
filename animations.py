"""
animations.py
=============
High-level cinematic animation controller.

Classes:
  SlowMoController   — manages time-scale, zoom, motion blur overlay
  ComboAnimator      — big animated combo pop (×2 / ×5 / ×10 / ULTRA)
  DynamicBackground  — score-reactive background that transitions between
                       5 themes: Cyber City → Neon Grid → Space →
                       Energy Storm → Holographic
  ZoomController     — smooth camera zoom-in / zoom-out
  MotionBlurOverlay  — semi-transparent previous-frame composite
  CinematicBars      — letterbox bars that slide in on slow-mo
"""

import math
import random
import pygame
from settings import (
    SCREEN_W, SCREEN_H, TARGET_FPS,
    NEON_CYAN, NEON_PINK, NEON_GREEN, NEON_ORANGE, NEON_PURPLE,
    WHITE, BLACK, GOLD,
)


# ─────────────────────────────────────────────────────────────────────────────
# SLOW-MO CONTROLLER
# ─────────────────────────────────────────────────────────────────────────────
class SlowMoController:
    """
    When triggered (multi-slice or gesture):
      • time_scale drops to 0.25 and eases back to 1.0
      • zoom controller zooms in slightly
      • motion blur overlay is applied
      • cinematic bars slide in
    """

    def __init__(self, zoom_ctrl, blur_overlay, bars):
        self.zoom   = zoom_ctrl
        self.blur   = blur_overlay
        self.bars   = bars
        self._active  = False
        self._timer   = 0
        self._max_dur = 90         # frames

    def trigger(self, duration: int = 90):
        self._active = True
        self._timer  = duration
        self._max_dur= duration
        self.zoom.zoom_to(1.10, speed=0.04)
        self.bars.show()

    @property
    def active(self): return self._active

    @property
    def time_scale(self) -> float:
        if not self._active: return 1.0
        t = self._timer / self._max_dur
        # Ease: slow at start, ramp back up at end
        if t > 0.7:
            return 0.28 + (1 - t) / 0.3 * 0.12
        else:
            return 0.28 + (0.7 - t) / 0.7 * 0.72

    def update(self):
        if not self._active: return
        self._timer -= 1
        if self._timer <= 0:
            self._active = False
            self.zoom.zoom_to(1.0, speed=0.03)
            self.bars.hide()


# ─────────────────────────────────────────────────────────────────────────────
# ZOOM CONTROLLER
# ─────────────────────────────────────────────────────────────────────────────
class ZoomController:
    """Smooth zoom that blits the game surface scaled around centre."""

    def __init__(self):
        self._current = 1.0
        self._target  = 1.0
        self._speed   = 0.05

    def zoom_to(self, target: float, speed: float = 0.05):
        self._target = target
        self._speed  = speed

    def update(self):
        diff = self._target - self._current
        self._current += diff * self._speed * 2

    def apply(self, source: pygame.Surface) -> tuple[pygame.Surface, tuple]:
        """Returns (scaled_surface, blit_offset) for screen.blit."""
        z = self._current
        if abs(z - 1.0) < 0.003:
            return source, (0, 0)
        nw = int(SCREEN_W * z)
        nh = int(SCREEN_H * z)
        scaled = pygame.transform.smoothscale(source, (nw, nh))
        ox = (SCREEN_W - nw) // 2
        oy = (SCREEN_H - nh) // 2
        return scaled, (ox, oy)

    @property
    def current(self): return self._current


# ─────────────────────────────────────────────────────────────────────────────
# MOTION BLUR OVERLAY
# ─────────────────────────────────────────────────────────────────────────────
class MotionBlurOverlay:
    """
    Keeps the previous frame and blends it back with low alpha —
    creates an in-engine motion blur effect.
    Only active during slow-mo.
    """

    def __init__(self):
        self._prev   = pygame.Surface((SCREEN_W, SCREEN_H))
        self._active = False
        self._alpha  = 0

    def set_active(self, on: bool):
        self._active = on
        self._alpha  = 80 if on else 0

    def capture(self, surface: pygame.Surface):
        if self._active:
            self._prev.blit(surface, (0, 0))

    def apply(self, surface: pygame.Surface):
        if self._active and self._alpha > 0:
            self._prev.set_alpha(self._alpha)
            surface.blit(self._prev, (0, 0))


# ─────────────────────────────────────────────────────────────────────────────
# CINEMATIC BARS
# ─────────────────────────────────────────────────────────────────────────────
class CinematicBars:
    """Black letterbox bars that slide in (top and bottom) during slow-mo."""

    BAR_H = 55

    def __init__(self):
        self._top_h    = 0.0
        self._bot_h    = 0.0
        self._target   = 0.0
        self._speed    = 5.0

    def show(self): self._target = self.BAR_H
    def hide(self): self._target = 0.0

    def update(self):
        diff = self._target - self._top_h
        self._top_h += diff * 0.18
        self._bot_h  = self._top_h

    def draw(self, surface: pygame.Surface):
        h = int(self._top_h)
        if h < 1: return
        surf = pygame.Surface((SCREEN_W, h), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 230))
        surface.blit(surf, (0, 0))
        surface.blit(surf, (0, SCREEN_H - h))


# ─────────────────────────────────────────────────────────────────────────────
# COMBO ANIMATOR
# ─────────────────────────────────────────────────────────────────────────────
class ComboAnimator:
    """
    Big cinematic combo text shown at screen centre.
    Scales in, pulses, then fades out.
    """

    TIERS = {
        2:  ("×2  COMBO",  (0,   220, 255), 52),
        5:  ("×5  COMBO!", (255, 200, 0),   64),
        10: ("×10 ULTRA!", (255, 40,  160), 80),
        20: ("×20 GODLIKE",(255, 255, 255), 96),
    }

    def __init__(self):
        self._anims: list[dict] = []

    def trigger(self, combo: int):
        tier = None
        for t in sorted(self.TIERS.keys(), reverse=True):
            if combo >= t:
                tier = t
                break
        if tier is None: return
        text, color, size = self.TIERS[tier]
        try:
            font = pygame.font.SysFont("Consolas", size, bold=True)
        except Exception:
            font = pygame.font.SysFont("Arial", size, bold=True)
        self._anims.append({
            "text":  text,
            "color": color,
            "font":  font,
            "life":  55,
            "max":   55,
            "y":     SCREEN_H // 2 - 40,
            "scale": 2.5,
            "vy":    -0.6,
        })

    def update(self):
        for a in self._anims:
            t = a["life"] / a["max"]
            a["scale"] = max(1.0, a["scale"] * 0.88 + 0.005)
            a["y"]    += a["vy"]
            a["life"] -= 1
        self._anims = [a for a in self._anims if a["life"] > 0]

    def draw(self, surface: pygame.Surface):
        for a in self._anims:
            t     = a["life"] / a["max"]
            alpha = int(255 * min(1.0, t * 2) if t > 0.5 else 255 * (t * 2))
            try:
                raw = a["font"].render(a["text"], True, a["color"])
                # Scale
                s = a["scale"]
                w, h = int(raw.get_width() * s), int(raw.get_height() * s)
                if w < 1 or h < 1: continue
                scaled = pygame.transform.smoothscale(raw, (w, h))
                scaled.set_alpha(alpha)
                # Glow pass
                for r in range(3, 0, -1):
                    gw, gh = w + r*8, h + r*8
                    if gw < 1 or gh < 1: continue
                    gsurf = pygame.transform.smoothscale(raw, (gw, gh))
                    gsurf.set_alpha(int(40 * t / r))
                    surface.blit(gsurf,
                                 (SCREEN_W//2 - gw//2, int(a["y"]) - gh//2),
                                 special_flags=pygame.BLEND_RGBA_ADD)
                surface.blit(scaled,
                             (SCREEN_W//2 - w//2, int(a["y"]) - h//2))
            except Exception:
                pass


# ─────────────────────────────────────────────────────────────────────────────
# DYNAMIC BACKGROUND
# ─────────────────────────────────────────────────────────────────────────────
class DynamicBackground:
    """
    Score-reactive animated background.
    Themes (by score bracket):
      0-99    → Cyber City   (neon grid + city silhouette)
      100-299 → Neon Grid    (expanding warp grid)
      300-599 → Space        (star field + nebula)
      600-999 → Energy Storm (lightning + plasma)
      1000+   → Holographic  (rainbow grid + prism particles)

    Transitions smoothly between themes with alpha blending.
    """

    THEMES = ["cyber", "neon", "space", "storm", "holo"]
    THRESHOLDS = [0, 100, 300, 600, 1000]
    GRADIENTS = {
        "cyber": [(5,   5,   30),  (10,  0,   40)],
        "neon":  [(0,   0,   20),  (20,  0,   30)],
        "space": [(0,   0,   8),   (5,   0,   18)],
        "storm": [(15,  0,   25),  (5,   0,   10)],
        "holo":  [(0,   10,  30),  (10,  0,   25)],
    }

    def __init__(self):
        self._tick      = 0
        self._theme     = "cyber"
        self._next      = "cyber"
        self._blend     = 1.0        # 0 = prev, 1 = current
        self._blend_spd = 0.025
        self._stars     = [(random.randint(0, SCREEN_W),
                            random.randint(0, SCREEN_H),
                            random.uniform(0.3, 2.0)) for _ in range(220)]
        self._lightning = []
        self._holo_pts  = [(random.randint(0, SCREEN_W),
                            random.randint(0, SCREEN_H),
                            random.uniform(0, math.tau)) for _ in range(80)]
        self._gradient_cache: dict[str, pygame.Surface] = {}
        self._make_gradients()
        self._city_surf = self._make_city()

    # ── Public ────────────────────────────────────────────────────────────
    def update(self, score: int):
        self._tick += 1

        # Determine target theme
        target = "cyber"
        for i, thresh in enumerate(self.THRESHOLDS):
            if score >= thresh:
                target = self.THEMES[i]

        if target != self._next:
            self._next  = target
            self._blend = 0.0

        if self._blend < 1.0:
            self._blend = min(1.0, self._blend + self._blend_spd)
            if self._blend >= 1.0:
                self._theme = self._next

        # Lightning
        if self._theme in ("storm", "holo") and random.random() < 0.04:
            self._lightning.append(self._make_bolt())
        self._lightning = [b for b in self._lightning if b["life"] > 0]
        for b in self._lightning:
            b["life"] -= 1

        # Stars drift
        for i, (sx, sy, spd) in enumerate(self._stars):
            self._stars[i] = (sx, (sy + spd) % SCREEN_H, spd)

        # Holo particles rotate
        for i, (hx, hy, ha) in enumerate(self._holo_pts):
            self._holo_pts[i] = (hx, hy, ha + 0.02)

    def draw(self, surface: pygame.Surface):
        # Base gradient
        active = self._next if self._blend < 1.0 else self._theme
        g = self._gradient_cache.get(active)
        if g: surface.blit(g, (0, 0))

        # Theme overlays
        if active == "cyber":
            self._draw_city(surface)
            self._draw_grid(surface, (0, 30, 60), 80)
        elif active == "neon":
            self._draw_warp_grid(surface)
        elif active == "space":
            self._draw_stars(surface)
            self._draw_nebula(surface)
        elif active == "storm":
            self._draw_grid(surface, (30, 0, 60), 60)
            self._draw_lightning(surface)
            self._draw_plasma(surface)
        elif active == "holo":
            self._draw_holo(surface)
            self._draw_stars(surface)

    # ── Gradient ──────────────────────────────────────────────────────────
    def _make_gradients(self):
        for name, (top, bot) in self.GRADIENTS.items():
            s = pygame.Surface((SCREEN_W, SCREEN_H))
            for y in range(SCREEN_H):
                t = y / SCREEN_H
                c = tuple(int(top[i] + (bot[i]-top[i])*t) for i in range(3))
                pygame.draw.line(s, c, (0, y), (SCREEN_W, y))
            self._gradient_cache[name] = s

    def _make_city(self) -> pygame.Surface:
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        # Simple silhouette of buildings
        buildings = []
        x = 0
        while x < SCREEN_W:
            w = random.randint(40, 100)
            h = random.randint(80, 260)
            buildings.append((x, SCREEN_H - h, w, h))
            x += w + random.randint(4, 20)
        for bx, by, bw, bh in buildings:
            pygame.draw.rect(s, (8, 4, 22, 200), (bx, by, bw, bh))
            # Windows
            for wy in range(by + 10, SCREEN_H - 20, 18):
                for wx2 in range(bx + 6, bx + bw - 6, 12):
                    if random.random() < 0.6:
                        pygame.draw.rect(s, (0, 180, 255, 80), (wx2, wy, 6, 8))
        return s

    def _make_bolt(self) -> dict:
        x = random.randint(0, SCREEN_W)
        pts = [(x, 0)]
        y = 0
        while y < SCREEN_H:
            y += random.randint(20, 60)
            pts.append((x + random.randint(-30, 30), y))
        return {"pts": pts, "life": random.randint(4, 10), "max": 10}

    # ── Theme renderers ───────────────────────────────────────────────────
    def _draw_city(self, surface):
        surface.blit(self._city_surf, (0, 0))

    def _draw_grid(self, surface, color, spacing):
        for x in range(0, SCREEN_W, spacing):
            pygame.draw.line(surface, color, (x, 0), (x, SCREEN_H), 1)
        for y in range(0, SCREEN_H, spacing):
            pygame.draw.line(surface, color, (0, y), (SCREEN_W, y), 1)

    def _draw_warp_grid(self, surface):
        """Perspective warp grid converging at a vanishing point."""
        vx, vy = SCREEN_W // 2, SCREEN_H // 2 + 50
        color = (0, 50, 80)
        for i in range(0, SCREEN_W, 60):
            pygame.draw.line(surface, color, (i, SCREEN_H), (vx, vy), 1)
        for y in range(vy, SCREEN_H, 40):
            pygame.draw.line(surface, color, (0, y), (SCREEN_W, y), 1)

    def _draw_stars(self, surface):
        for sx, sy, spd in self._stars:
            r = max(1, int(spd * 1.2))
            a = min(255, int(spd * 100))
            s2 = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
            pygame.draw.circle(s2, (a, a, a, a), (r+1, r+1), r)
            surface.blit(s2, (int(sx)-r-1, int(sy)-r-1))

    def _draw_nebula(self, surface):
        """Soft colour blobs."""
        tick = self._tick
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for i, color in enumerate([(20, 0, 60), (0, 20, 60), (40, 0, 40)]):
            r = 180 + int(30 * math.sin(tick * 0.01 + i * 2))
            cx = SCREEN_W // 4 * (i + 1)
            cy = SCREEN_H // 2 + int(40 * math.sin(tick * 0.008 + i))
            pygame.draw.circle(s, (*color, 35), (cx, cy), r)
        surface.blit(s, (0, 0))

    def _draw_lightning(self, surface):
        for bolt in self._lightning:
            t = bolt["life"] / bolt["max"]
            a = int(200 * t)
            pts = bolt["pts"]
            if len(pts) >= 2:
                s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
                pygame.draw.lines(s, (180, 140, 255, a), False, pts, 2)
                pygame.draw.lines(s, (255, 255, 255, a//2), False, pts, 1)
                surface.blit(s, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_plasma(self, surface):
        """Shifting plasma colours."""
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for i in range(0, SCREEN_W, 80):
            for j in range(0, SCREEN_H, 80):
                v = math.sin(i/60 + self._tick*0.04) + math.sin(j/60 + self._tick*0.03)
                c = int(abs(v) * 20)
                pygame.draw.circle(s, (c, 0, c*2, 30), (i, j), 40)
        surface.blit(s, (0, 0))

    def _draw_holo(self, surface):
        """Rainbow holographic grid."""
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        spacing = 55
        for i, x in enumerate(range(0, SCREEN_W, spacing)):
            hue = (self._tick * 2 + i * 20) % 360
            c   = self._hsv(hue, 1.0, 1.0)
            pygame.draw.line(s, (*c, 35), (x, 0), (x, SCREEN_H), 1)
        for j, y in enumerate(range(0, SCREEN_H, spacing)):
            hue = (self._tick * 2 + j * 20 + 120) % 360
            c   = self._hsv(hue, 1.0, 1.0)
            pygame.draw.line(s, (*c, 35), (0, y), (SCREEN_W, y), 1)
        # Holo floating diamonds
        for hx, hy, ha in self._holo_pts:
            hue = (self._tick + int(ha * 60)) % 360
            c   = self._hsv(hue, 1.0, 1.0)
            pts = [
                (hx,         hy - 6),
                (hx + 5,     hy),
                (hx,         hy + 6),
                (hx - 5,     hy),
            ]
            pygame.draw.polygon(s, (*c, 80), pts)
        surface.blit(s, (0, 0))

    @staticmethod
    def _hsv(h, s, v):
        h = h / 360
        if s == 0: return (int(v*255),)*3
        i = int(h*6); f = h*6-i; p=v*(1-s); q=v*(1-s*f); t2=v*(1-s*(1-f))
        i %= 6
        r,g,b = [(v,t2,p),(q,v,p),(p,v,t2),(p,q,v),(t2,p,v),(v,p,q)][i]
        return (int(r*255), int(g*255), int(b*255))