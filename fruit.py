"""
fruit.py  (UPGRADED)
====================
Ab har fruit ACTUALLY draw hota hai — watermelon, orange, banana, strawberry,
grapes, pineapple, mango, kiwi + special fruits + bomb.
Sab kuch pygame draw calls se — koi image file ki zaroorat nahi.
"""

import math, random
import pygame
from settings import (
    SCREEN_W, SCREEN_H, GRAVITY,
    FRUIT_RADIUS_MIN, FRUIT_RADIUS_MAX,
    FRUIT_SPEED_Y_MIN, FRUIT_SPEED_Y_MAX,
    FRUIT_SPEED_X_MIN, FRUIT_SPEED_X_MAX,
    FRUIT_SPAWN_MARGIN, WHITE, DEBUG_MODE,
)

# ─── Utility ────────────────────────────────────────────────────────────────

def _circ(surf, color, cx, cy, r, alpha=255):
    if r < 1: return
    s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color[:3], alpha), (r+1, r+1), r)
    surf.blit(s, (int(cx)-r-1, int(cy)-r-1))

def _glow(surf, color, cx, cy, r, alpha=60, passes=3):
    for i in range(passes, 0, -1):
        a = max(0, alpha // i)
        gr = r + i*5
        _circ(surf, color, cx, cy, gr, a)

# ─── Fruit drawers  (each takes surface, cx, cy, r, angle) ──────────────────

def _draw_watermelon(surf, cx, cy, r, angle):
    # Dark green outer
    _circ(surf, (20, 140, 30), cx, cy, r)
    # Lighter green stripes (rotated lines)
    for i in range(6):
        a = angle + i * 60
        rad = math.radians(a)
        x1 = cx + int((r-4) * math.cos(rad) * 0.3)
        y1 = cy + int((r-4) * math.sin(rad) * 0.3)
        x2 = cx + int((r-3) * math.cos(rad))
        y2 = cy + int((r-3) * math.sin(rad))
        s = pygame.Surface((4, max(4, int(r*1.8))), pygame.SRCALPHA)
        s.fill((80, 200, 60, 120))
        rs = pygame.transform.rotate(s, -a)
        surf.blit(rs, rs.get_rect(center=(int((x1+x2)//2), int((y1+y2)//2))))
    # Shine
    _circ(surf, (180, 255, 120), cx - r//3, cy - r//3, max(3, r//5), 180)

def _draw_orange(surf, cx, cy, r, angle):
    _circ(surf, (230, 100, 0), cx, cy, r)
    # texture bumps
    for i in range(8):
        a = math.radians(angle + i * 45)
        bx = cx + int(r * 0.55 * math.cos(a))
        by = cy + int(r * 0.55 * math.sin(a))
        _circ(surf, (200, 80, 0), bx, by, max(2, r//7), 160)
    # Shine
    _circ(surf, (255, 210, 120), cx - r//3, cy - r//3, max(3, r//5), 200)
    # navel dot
    _circ(surf, (180, 70, 0), cx + r//4, cy + r//4, max(2, r//8))

def _draw_banana(surf, cx, cy, r, angle):
    # Banana = curved yellow shape using polygon
    pts = []
    for i in range(20):
        t = i / 19
        a = math.radians(angle + t * 160 - 80)
        # outer arc
        outer_r = r
        inner_r = r * 0.45
        mid_x = cx + int(inner_r * math.cos(math.radians(angle)))
        mid_y = cy + int(inner_r * math.sin(math.radians(angle)))
        x = mid_x + int(outer_r * 0.9 * math.cos(a))
        y = mid_y + int(outer_r * 0.9 * math.sin(a))
        pts.append((x, y))
    for i in range(20):
        t = (19-i) / 19
        a = math.radians(angle + t * 160 - 80)
        inner_r = r * 0.35
        mid_x = cx + int(inner_r * math.cos(math.radians(angle)))
        mid_y = cy + int(inner_r * math.sin(math.radians(angle)))
        x = mid_x + int(r * 0.55 * math.cos(a))
        y = mid_y + int(r * 0.55 * math.sin(a))
        pts.append((x, y))
    if len(pts) >= 3:
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.polygon(s, (240, 220, 20, 240), pts)
        pygame.draw.polygon(s, (200, 160, 0, 180), pts, 2)
        surf.blit(s, (0,0))
    _circ(surf, (255, 240, 100), cx - r//4, cy - r//4, max(3, r//5), 180)

def _draw_strawberry(surf, cx, cy, r, angle):
    # Red heart-ish shape
    pts = []
    for i in range(36):
        a = math.radians(i * 10 + angle)
        # heart parametric
        t = math.radians(i * 10)
        sx = 16 * (math.sin(t)**3)
        sy = -(13*math.cos(t) - 5*math.cos(2*t) - 2*math.cos(3*t) - math.cos(4*t))
        scale = r / 17
        pts.append((int(cx + sx*scale), int(cy + sy*scale)))
    if len(pts) >= 3:
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.polygon(s, (210, 30, 40, 240), pts)
        surf.blit(s, (0,0))
    # Seeds
    for i in range(6):
        a = math.radians(angle + i * 60)
        sx2 = cx + int(r * 0.4 * math.cos(a))
        sy2 = cy + int(r * 0.35 * math.sin(a))
        _circ(surf, (255, 220, 180), sx2, sy2, max(2, r//9), 200)
    # Leaves on top
    for i in range(3):
        a = math.radians(-90 + angle + (i-1)*25)
        lx = cx + int(r*0.5 * math.cos(a))
        ly = cy - r + int(r*0.3 * math.sin(a))
        _circ(surf, (30, 160, 30), lx, ly, max(3, r//5), 220)

def _draw_grapes(surf, cx, cy, r, angle):
    # Cluster of small purple circles
    positions = [
        (0, -0.6), (-0.4, -0.2), (0.4, -0.2),
        (-0.6,  0.3), (0,  0.3), (0.6,  0.3),
        (-0.2,  0.85),(0.2, 0.85),
    ]
    gr = max(5, int(r * 0.42))
    for (dx, dy) in positions:
        # rotate by angle
        rad = math.radians(angle)
        rx2 = dx*math.cos(rad) - dy*math.sin(rad)
        ry2 = dx*math.sin(rad) + dy*math.cos(rad)
        gx = cx + int(rx2 * r * 0.9)
        gy = cy + int(ry2 * r * 0.9)
        _circ(surf, (90, 10, 140), gx, gy, gr)
        _circ(surf, (160, 80, 210), gx, gy, gr, 180)
        _circ(surf, (220, 180, 255), gx - gr//3, gy - gr//3, max(2, gr//3), 180)
    # Stem
    pygame.draw.line(surf, (100, 60, 20),
                     (cx, cy - r + 4), (cx, cy - r - 10), 3)

def _draw_pineapple(surf, cx, cy, r, angle):
    # Body — golden oval
    body_surf = pygame.Surface((r*2+4, int(r*2.4)+4), pygame.SRCALPHA)
    pygame.draw.ellipse(body_surf, (210, 155, 20), (2, int(r*0.4)+2, r*2, int(r*1.8)))
    # Diamond grid
    for row in range(5):
        for col in range(4):
            gx = int(r*0.3 + col*r*0.45 - row*0.1)
            gy = int(r*0.55 + row*r*0.32 + col*0.15)
            pygame.draw.rect(body_surf, (170, 110, 0), (gx, gy, max(3, r//6), max(3, r//6)), 1)
    surf.blit(body_surf, (cx - r - 2, cy - int(r*1.2) - 2))
    # Crown leaves
    for i in range(5):
        a = math.radians(-90 + (i-2)*22 + angle*0.1)
        leaf_len = r * 0.7
        lx = cx + int(leaf_len * math.cos(a))
        ly = (cy - r) + int(leaf_len * math.sin(a))
        pygame.draw.line(surf, (30, 150, 30),
                         (cx, cy - r), (lx, ly), max(2, r//7))

def _draw_mango(surf, cx, cy, r, angle):
    # Teardrop shape
    pts = []
    for i in range(36):
        t = math.radians(i * 10)
        rx2 = r * 0.85 * math.sin(t)
        ry2 = r * (math.cos(t) - 0.2) * 0.95
        rad = math.radians(angle)
        rx3 = rx2*math.cos(rad) - ry2*math.sin(rad)
        ry3 = rx2*math.sin(rad) + ry2*math.cos(rad)
        pts.append((int(cx + rx3), int(cy + ry3)))
    if len(pts) >= 3:
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.polygon(s, (230, 130, 10, 240), pts)
        pygame.draw.polygon(s, (200, 80, 0, 120), pts, 2)
        surf.blit(s, (0,0))
    # Red blush
    _circ(surf, (220, 60, 20), cx + r//4, cy - r//4, max(4, r//3), 80)
    # Shine
    _circ(surf, (255, 240, 180), cx - r//4, cy - r//3, max(3, r//5), 200)

def _draw_kiwi(surf, cx, cy, r, angle):
    # Outer brown
    _circ(surf, (100, 65, 25), cx, cy, r)
    # Fuzzy texture dots
    for i in range(12):
        a = math.radians(angle + i * 30)
        fx = cx + int(r * 0.75 * math.cos(a))
        fy = cy + int(r * 0.75 * math.sin(a))
        _circ(surf, (130, 85, 35), fx, fy, max(2, r//8), 200)
    # Inner green slice
    _circ(surf, (90, 170, 50), cx, cy, int(r * 0.78))
    # White center
    _circ(surf, (240, 240, 220), cx, cy, int(r * 0.22))
    # Seed lines radiating
    for i in range(8):
        a = math.radians(angle + i * 45)
        sx2 = cx + int(r * 0.28 * math.cos(a))
        sy2 = cy + int(r * 0.28 * math.sin(a))
        ex = cx + int(r * 0.65 * math.cos(a))
        ey = cy + int(r * 0.65 * math.sin(a))
        pygame.draw.line(surf, (30, 80, 10), (sx2, sy2), (ex, ey), 1)
        # Seed dot
        _circ(surf, (20, 20, 10), cx + int(r*0.52*math.cos(a)),
              cy + int(r*0.52*math.sin(a)), max(2, r//9), 220)

# ─── Drawers map ────────────────────────────────────────────────────────────
FRUIT_DRAWERS = {
    "watermelon": _draw_watermelon,
    "orange":     _draw_orange,
    "banana":     _draw_banana,
    "strawberry": _draw_strawberry,
    "grapes":     _draw_grapes,
    "pineapple":  _draw_pineapple,
    "mango":      _draw_mango,
    "kiwi":       _draw_kiwi,
}

FRUIT_DATA = {
    "watermelon": {"color": (20,140,30),   "inner": (220,50,50),   "points": 10},
    "orange":     {"color": (230,100,0),   "inner": (255,200,50),  "points": 10},
    "banana":     {"color": (240,220,20),  "inner": (255,250,180), "points": 10},
    "strawberry": {"color": (210,30,40),   "inner": (255,150,150), "points": 15},
    "grapes":     {"color": (90,10,140),   "inner": (200,130,255), "points": 15},
    "pineapple":  {"color": (210,155,20),  "inner": (255,235,100), "points": 20},
    "mango":      {"color": (230,130,10),  "inner": (255,210,80),  "points": 20},
    "kiwi":       {"color": (100,65,25),   "inner": (90,170,50),   "points": 25},
}

SPECIAL_DATA = {
    "freeze":       {"color": (0,200,220),   "inner": (180,255,255), "label": "❄"},
    "double_score": {"color": (220,200,0),   "inner": (255,255,120), "label": "×2"},
    "slow_mo":      {"color": (120,0,220),   "inner": (210,140,255), "label": "⏱"},
    "bomb_diffuse": {"color": (0,200,80),    "inner": (150,255,180), "label": "🛡"},
}

# ─── Base Object ─────────────────────────────────────────────────────────────
class BaseObject:
    def __init__(self, x, y, vx, vy, radius):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.radius = radius
        self.alive  = True
        self.sliced = False
        self.angle  = random.uniform(0, 360)
        self.spin   = random.uniform(-3, 3)
        self._tick  = 0

    def update(self, ts=1.0):
        self.vy    += GRAVITY * ts
        self.x     += self.vx * ts
        self.y     += self.vy * ts
        self.angle += self.spin * ts
        self._tick += 1

    def is_off_screen(self):
        return (self.y > SCREEN_H + self.radius + 20 or
                self.x < -self.radius - 100 or
                self.x > SCREEN_W + self.radius + 100)

    def contains_point(self, px, py):
        return (self.x-px)**2 + (self.y-py)**2 <= self.radius**2

    def draw(self, surface): pass


# ─── Fruit ───────────────────────────────────────────────────────────────────
class Fruit(BaseObject):
    def __init__(self, kind=None):
        x  = random.randint(FRUIT_SPAWN_MARGIN, SCREEN_W - FRUIT_SPAWN_MARGIN)
        vx = random.uniform(FRUIT_SPEED_X_MIN, FRUIT_SPEED_X_MAX)
        vy = random.uniform(FRUIT_SPEED_Y_MIN, FRUIT_SPEED_Y_MAX)
        r  = random.randint(FRUIT_RADIUS_MIN, FRUIT_RADIUS_MAX)
        super().__init__(x, SCREEN_H + 20, vx, vy, r)

        if kind is None:
            kind = random.choice(list(FRUIT_DATA.keys()))
        self.kind        = kind
        d                = FRUIT_DATA[kind]
        self.color_outer = d["color"]
        self.color_inner = d["inner"]
        self.points      = d["points"]
        self.is_special  = False
        self._drawer     = FRUIT_DRAWERS[kind]

    def draw(self, surface):
        ix, iy = int(self.x), int(self.y)
        # Soft glow behind fruit
        _glow(surface, self.color_outer, ix, iy, self.radius, alpha=40, passes=2)
        # Draw actual fruit shape
        self._drawer(surface, ix, iy, self.radius, self.angle)
        if DEBUG_MODE:
            pygame.draw.circle(surface, (255,0,0), (ix,iy), self.radius, 1)


# ─── Special fruits ──────────────────────────────────────────────────────────
class SpecialFruit(BaseObject):
    def __init__(self, power):
        x  = random.randint(FRUIT_SPAWN_MARGIN, SCREEN_W - FRUIT_SPAWN_MARGIN)
        vx = random.uniform(FRUIT_SPEED_X_MIN, FRUIT_SPEED_X_MAX)
        vy = random.uniform(FRUIT_SPEED_Y_MIN, FRUIT_SPEED_Y_MAX)
        r  = random.randint(FRUIT_RADIUS_MIN, FRUIT_RADIUS_MAX)
        super().__init__(x, SCREEN_H + 20, vx, vy, r)

        d = SPECIAL_DATA[power]
        self.power       = power
        self.color_outer = d["color"]
        self.color_inner = d["inner"]
        self.label       = d["label"]
        self.points      = 5
        self.is_special  = True
        self.is_bomb     = False
        self.kind        = power

    def draw(self, surface):
        ix, iy = int(self.x), int(self.y)
        pulse = 0.7 + 0.3 * math.sin(self._tick * 0.12)
        _glow(surface, self.color_outer, ix, iy, int(self.radius * pulse) + 6, alpha=80, passes=3)

        # Pulsing outer ring
        ring_r = int(self.radius * (1 + 0.1 * math.sin(self._tick * 0.15)))
        _circ(surface, self.color_outer, ix, iy, ring_r, 200)
        _circ(surface, self.color_inner, ix, iy, int(ring_r * 0.72), 230)

        # Rotating star points
        for i in range(6):
            a = math.radians(self.angle + i * 60)
            sx2 = ix + int((self.radius + 6) * math.cos(a))
            sy2 = iy + int((self.radius + 6) * math.sin(a))
            _circ(surface, self.color_outer, sx2, sy2, max(3, self.radius // 7), 200)

        # Label text
        try:
            font = pygame.font.SysFont("Arial", max(14, self.radius // 2), bold=True)
            t    = font.render(self.label, True, WHITE)
            surface.blit(t, t.get_rect(center=(ix, iy)))
        except Exception:
            pass


class FreezeFruit(SpecialFruit):
    def __init__(self): super().__init__("freeze")

class DoubleScoreFruit(SpecialFruit):
    def __init__(self): super().__init__("double_score")

class SlowMoFruit(SpecialFruit):
    def __init__(self): super().__init__("slow_mo")

class BombDiffuserFruit(SpecialFruit):
    def __init__(self): super().__init__("bomb_diffuse")


# ─── Bomb ────────────────────────────────────────────────────────────────────
class Bomb(BaseObject):
    def __init__(self):
        x  = random.randint(FRUIT_SPAWN_MARGIN, SCREEN_W - FRUIT_SPAWN_MARGIN)
        vx = random.uniform(FRUIT_SPEED_X_MIN, FRUIT_SPEED_X_MAX)
        vy = random.uniform(FRUIT_SPEED_Y_MIN * 0.85, FRUIT_SPEED_Y_MAX * 0.85)
        r  = random.randint(FRUIT_RADIUS_MIN, FRUIT_RADIUS_MAX - 4)
        super().__init__(x, SCREEN_H + 20, vx, vy, r)
        self.is_bomb    = True
        self.color_outer= (40, 40, 40)
        self.color_inner= (80, 80, 80)

    def draw(self, surface):
        ix, iy = int(self.x), int(self.y)
        pulse = abs(math.sin(self._tick * 0.15))

        # Red danger glow
        _glow(surface, (200, 30, 30), ix, iy, self.radius, alpha=int(50*pulse)+20, passes=2)

        # Body — dark sphere
        _circ(surface, (30, 30, 30), ix, iy, self.radius)
        _circ(surface, (65, 65, 65), ix, iy, int(self.radius * 0.75), 200)
        # Sheen
        _circ(surface, (110, 110, 110), ix - self.radius//3, iy - self.radius//3,
              max(3, self.radius//5), 160)

        # Fuse rope
        fuse_x = ix + self.radius - 4
        fuse_y = iy - self.radius + 4
        pygame.draw.line(surface, (140, 100, 40),
                         (ix + self.radius//2, iy - self.radius//2),
                         (fuse_x, fuse_y - 14), 3)
        # Spark at fuse tip
        spark_colors = [(255,220,0), (255,140,0), (255,60,0)]
        sc = spark_colors[self._tick % 3]
        _circ(surface, sc, fuse_x, fuse_y - 14, max(3, int(5*pulse)+2), 230)

        # ✕ cross
        sz = self.radius // 2 - 2
        for dx, dy in [(-1,-1),(1,1),(-1,1),(1,-1)]:
            pygame.draw.line(surface, (200,30,30),
                             (ix - sz + dx, iy - sz + dy),
                             (ix + sz + dx, iy + sz + dy), 2)
        pygame.draw.line(surface, (220,50,50), (ix-sz,iy-sz), (ix+sz,iy+sz), 2)
        pygame.draw.line(surface, (220,50,50), (ix+sz,iy-sz), (ix-sz,iy+sz), 2)

    def update(self, ts=1.0):
        super().update(ts)


# ─── Factory ─────────────────────────────────────────────────────────────────
SPECIAL_CLASSES = [FreezeFruit, DoubleScoreFruit, SlowMoFruit, BombDiffuserFruit]

def spawn_object(bomb_chance, special_chance):
    roll = random.random()
    if roll < bomb_chance:
        return Bomb()
    if roll < bomb_chance + special_chance:
        return random.choice(SPECIAL_CLASSES)()
    return Fruit()