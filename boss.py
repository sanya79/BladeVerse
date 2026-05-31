"""
boss.py
=======
Boss Fruits — rare giant enemies that require multiple slices to defeat.

BossFruit:
  • Spawns with dramatic entrance (fly-in + shake)
  • Has HP bar displayed below it
  • Takes multiple slices (HP = 3–5)
  • Each hit shows damage flash and knockback
  • Defeat triggers massive particle explosion + score bonus
  • Animated health bar with damage segments

BossManager:
  • Controls spawn probability and timing
  • Tracks active boss (only one at a time)
  • Provides draw() and update() interface
"""

import math
import random
import pygame
from settings import (
    SCREEN_W, SCREEN_H, GRAVITY,
    NEON_CYAN, NEON_PINK, NEON_GREEN, NEON_ORANGE, NEON_PURPLE,
    WHITE, BLACK, RED, GOLD,
    FRUIT_SPEED_X_MIN, FRUIT_SPEED_X_MAX,
    FRUIT_SPEED_Y_MIN, FRUIT_SPEED_Y_MAX,
    FRUIT_SPAWN_MARGIN,
)
from fruit import FRUIT_DATA, FRUIT_DRAWERS


# ── Boss constants ───────────────────────────────────────────────────────────
BOSS_CHANCE          = 0.004   # per-frame probability once eligible
BOSS_SCORE_THRESHOLD = 200     # score needed before boss can spawn
BOSS_HP_RANGE        = (3, 5)
BOSS_RADIUS_RANGE    = (68, 88)
BOSS_SPEED_MULT      = 0.65    # slower than normal fruits
BOSS_POINTS_BASE     = 200


# ── Color palette for boss aura ──────────────────────────────────────────────
BOSS_AURA_COLORS = [
    (255, 30, 80),   # hot-red
    (255, 80, 0),    # orange
    (200, 0, 255),   # electric purple
]


def _alpha_circ(surf, color, cx, cy, r, a):
    if r < 1: return
    s = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
    pygame.draw.circle(s, (*color[:3], int(a)), (r+1, r+1), r)
    surf.blit(s, (int(cx)-r-1, int(cy)-r-1))


# ─────────────────────────────────────────────────────────────────────────────
# BOSS FRUIT
# ─────────────────────────────────────────────────────────────────────────────
class BossFruit:
    """
    Behaves like a regular Fruit but with HP, animation phases, and
    a custom draw method that renders the health bar + aura.
    """

    PHASE_ENTER   = "enter"   # dramatic fly-in
    PHASE_ACTIVE  = "active"  # normal gameplay, takes hits
    PHASE_HIT     = "hit"     # flash on damage
    PHASE_DYING   = "dying"   # shake & expand before death
    PHASE_DEAD    = "dead"

    def __init__(self, score: int):
        # Choose random fruit type — prefer rarer ones
        rare = ["kiwi", "pineapple", "mango", "grapes"]
        kind = random.choice(rare)

        self.kind        = kind
        self.color_outer = FRUIT_DATA[kind]["color"]
        self.color_inner = FRUIT_DATA[kind]["inner"]
        self._drawer     = FRUIT_DRAWERS[kind]

        self.radius = random.randint(*BOSS_RADIUS_RANGE)
        self.x = float(random.randint(FRUIT_SPAWN_MARGIN + self.radius,
                                      SCREEN_W - FRUIT_SPAWN_MARGIN - self.radius))
        self.y = float(SCREEN_H + self.radius + 10)

        # Scale HP and reward with current score
        hp_max = BOSS_HP_RANGE[0] + min(2, score // 500)
        self.hp     = hp_max
        self.hp_max = hp_max
        self.points = BOSS_POINTS_BASE + score // 5

        self.vx = random.uniform(FRUIT_SPEED_X_MIN, FRUIT_SPEED_X_MAX) * BOSS_SPEED_MULT
        self.vy = (FRUIT_SPEED_Y_MIN * 0.9) * BOSS_SPEED_MULT

        self.angle  = 0.0
        self.spin   = random.uniform(-1.5, 1.5)
        self._tick  = 0

        self.alive   = True
        self.sliced  = False   # True when dead (for compatibility with game_manager)
        self.is_bomb = False
        self.is_special = False

        self.phase         = self.PHASE_ENTER
        self._enter_timer  = 40          # frames for entrance
        self._hit_timer    = 0
        self._dying_timer  = 0
        self._dying_max    = 35
        self._shake_x      = 0.0

        # Aura pulsing
        self._aura_color = random.choice(BOSS_AURA_COLORS)
        self._aura_r     = 0

        # Hit particles (small sparks on damage)
        self._sparks     = []

    # ── Physics ───────────────────────────────────────────────────────────
    def update(self, time_scale=1.0):
        self._tick += 1

        if self.phase == self.PHASE_ENTER:
            self._enter_timer -= 1
            self.vy += GRAVITY * time_scale
            self.x  += self.vx * time_scale
            self.y  += self.vy * time_scale
            self.angle += self.spin * time_scale
            if self._enter_timer <= 0:
                self.phase = self.PHASE_ACTIVE

        elif self.phase == self.PHASE_ACTIVE:
            self.vy += GRAVITY * time_scale
            self.x  += self.vx * time_scale
            self.y  += self.vy * time_scale
            self.angle += self.spin * time_scale
            # Aura pulse
            self._aura_r = self.radius + 12 + int(8 * math.sin(self._tick * 0.12))

        elif self.phase == self.PHASE_HIT:
            self._hit_timer -= 1
            self.vy += GRAVITY * time_scale
            self.x  += self.vx * time_scale + self._shake_x
            self.y  += self.vy * time_scale
            self.angle += self.spin * 2 * time_scale
            self._shake_x = -self._shake_x * 0.7
            if self._hit_timer <= 0:
                self.phase = self.PHASE_ACTIVE if self.hp > 0 else self.PHASE_DYING
                if self.hp <= 0:
                    self._dying_timer = self._dying_max

        elif self.phase == self.PHASE_DYING:
            self._dying_timer -= 1
            self.angle += 5 * time_scale
            if self._dying_timer <= 0:
                self.phase = self.PHASE_DEAD
                self.alive = False
                self.sliced = True

        # Update sparks
        for sp in self._sparks:
            sp[0] += sp[2]; sp[1] += sp[3]; sp[3] += 0.3; sp[4] -= 1
        self._sparks = [s for s in self._sparks if s[4] > 0]

    def take_hit(self):
        """Call when blade touches boss.  Returns True if boss dies."""
        if self.phase not in (self.PHASE_ACTIVE, self.PHASE_HIT):
            return False
        self.hp = max(0, self.hp - 1)
        self.phase = self.PHASE_HIT
        self._hit_timer = 12
        self._shake_x   = random.choice([-12, 12])
        # Spawn hit sparks
        for _ in range(16):
            a = random.uniform(0, math.tau)
            s = random.uniform(3, 9)
            self._sparks.append([self.x, self.y,
                                  math.cos(a)*s, math.sin(a)*s - 2,
                                  18])
        return self.hp <= 0

    def is_off_screen(self):
        return (self.y > SCREEN_H + self.radius + 40 or
                self.x < -self.radius - 100 or
                self.x > SCREEN_W + self.radius + 100)

    def contains_point(self, px, py):
        return (self.x - px)**2 + (self.y - py)**2 <= self.radius**2

    # ── Drawing ───────────────────────────────────────────────────────────
    def draw(self, surface: pygame.Surface):
        ix, iy = int(self.x), int(self.y)

        # ── Dying shake/expand ────────────────────────────────────────
        if self.phase == self.PHASE_DYING:
            t = 1 - self._dying_timer / self._dying_max
            r_exp = int(self.radius * (1 + t * 0.8))
            _alpha_circ(surface, (255, 80, 0), ix, iy, r_exp, int(200 * (1 - t)))
            _alpha_circ(surface, WHITE,         ix, iy, r_exp // 2, int(180 * (1 - t)))
            return

        if self.phase == self.PHASE_DEAD:
            return

        # ── Aura glow ─────────────────────────────────────────────────
        pulse = 0.6 + 0.4 * math.sin(self._tick * 0.12)
        for layer in range(4, 0, -1):
            r_g = self.radius + layer * 8
            a_g = int(30 * pulse * layer / 4)
            _alpha_circ(surface, self._aura_color, ix, iy, r_g, a_g)

        # ── Hit flash ─────────────────────────────────────────────────
        if self.phase == self.PHASE_HIT:
            t = self._hit_timer / 12
            _alpha_circ(surface, WHITE, ix, iy, self.radius + 6, int(220 * t))

        # ── Boss body (enlarged fruit drawer) ─────────────────────────
        # Draw to a temp surface then blit scaled
        r = self.radius
        tmp = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
        self._drawer(tmp, r + 2, r + 2, r, self.angle)
        surface.blit(tmp, (ix - r - 2, iy - r - 2))

        # ── BOSS label ────────────────────────────────────────────────
        try:
            font = pygame.font.SysFont("Consolas", 14, bold=True)
            lbl  = font.render("BOSS", True, (255, 40, 80))
            surface.blit(lbl, (ix - lbl.get_width()//2, iy - r - 24))
        except Exception:
            pass

        # ── HP bar ────────────────────────────────────────────────────
        self._draw_hp_bar(surface, ix, iy)

        # ── Hit sparks ────────────────────────────────────────────────
        for sp in self._sparks:
            _alpha_circ(surface, NEON_ORANGE, sp[0], sp[1], 4,
                        int(200 * sp[4] / 18))

        # ── Entrance arrow (enter phase) ──────────────────────────────
        if self.phase == self.PHASE_ENTER:
            t = 1 - self._enter_timer / 40
            a = int(200 * t)
            arrow_y = iy - r - 35
            pts = [(ix, arrow_y), (ix - 14, arrow_y - 22), (ix + 14, arrow_y - 22)]
            s = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.polygon(s, (*NEON_PINK, a),
                                [(p[0] - ix + 20, p[1] - arrow_y + 20) for p in pts])
            surface.blit(s, (ix - 20, arrow_y - 20))

    def _draw_hp_bar(self, surface, cx, cy):
        bar_w = self.radius * 2 + 12
        bar_h = 8
        bx    = cx - bar_w // 2
        by    = cy + self.radius + 10

        # Background
        bg = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (40, 0, 0, 200), (0, 0, bar_w, bar_h), border_radius=4)
        surface.blit(bg, (bx, by))

        # HP fill — segments per HP point
        seg_w = (bar_w - 4) / self.hp_max
        for i in range(self.hp):
            frac = (i + 1) / self.hp_max
            c = (
                int(255 * (1 - frac)),
                int(200 * frac),
                0,
                220,
            )
            fg = pygame.Surface((int(seg_w) - 2, bar_h - 4), pygame.SRCALPHA)
            pygame.draw.rect(fg, c, fg.get_rect(), border_radius=3)
            surface.blit(fg, (bx + 2 + int(i * seg_w), by + 2))

        # Border glow
        bd = pygame.Surface((bar_w + 4, bar_h + 4), pygame.SRCALPHA)
        pygame.draw.rect(bd, (255, 80, 0, 120), bd.get_rect(), width=1, border_radius=5)
        surface.blit(bd, (bx - 2, by - 2))


# ─────────────────────────────────────────────────────────────────────────────
# BOSS MANAGER
# ─────────────────────────────────────────────────────────────────────────────
class BossManager:
    """
    Decides when to spawn a boss, tracks the active one,
    and provides draw() / update() / check_slice() methods
    that game_manager calls each frame.
    """

    def __init__(self):
        self.boss:       BossFruit | None = None
        self._cooldown = 600   # min frames between bosses

    def update(self, score: int, time_scale: float = 1.0):
        if self._cooldown > 0:
            self._cooldown -= 1

        if self.boss:
            self.boss.update(time_scale)
            if self.boss.phase == BossFruit.PHASE_DEAD or self.boss.is_off_screen():
                self.boss = None
                self._cooldown = 600

        # Maybe spawn
        if (self.boss is None
                and self._cooldown <= 0
                and score >= BOSS_SCORE_THRESHOLD
                and random.random() < BOSS_CHANCE):
            self.boss = BossFruit(score)

    def draw(self, surface: pygame.Surface):
        if self.boss and self.boss.alive:
            self.boss.draw(surface)

    def check_slice(self, tip_pos) -> tuple[bool, bool, int]:
        """
        Returns (hit, killed, points).
        hit    = blade touched boss this frame
        killed = boss HP hit zero this frame
        points = awarded (0 if not hit, full reward if killed, partial otherwise)
        """
        if not self.boss or not self.boss.alive:
            return False, False, 0
        if not tip_pos:
            return False, False, 0
        if not self.boss.contains_point(*tip_pos):
            return False, False, 0

        killed = self.boss.take_hit()
        pts    = self.boss.points if killed else self.boss.points // self.boss.hp_max
        return True, killed, pts

    @property
    def has_boss(self):
        return self.boss is not None and self.boss.alive