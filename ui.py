"""
ui.py
=====
All user-interface components:
  • FontCache          – lazy-loads fonts (falls back to SysFont)
  • GlowButton         – animated neon button
  • HUD                – in-game score / lives / mode overlay
  • MainMenu           – title screen
  • PauseOverlay       – pause screen
  • GameOverScreen     – end-game results
  • LeaderboardScreen  – top-10 scores
  • SettingsScreen     – audio, theme, camera, debug toggles
  • ModeSelectScreen   – choose Arcade / Survival / Time Attack
"""

import os
import math
import pygame
from settings import (
    SCREEN_W, SCREEN_H,
    FONTS_DIR,
    FONT_LARGE, FONT_MEDIUM, FONT_SMALL, FONT_TINY,
    HUD_PADDING,
    BLACK, WHITE, NEON_CYAN, NEON_PINK, NEON_GREEN,
    NEON_YELLOW, NEON_ORANGE, NEON_PURPLE, GOLD,
    DARK_PANEL, RED, DEEP_BLUE,
    MODE_ARCADE, MODE_SURVIVAL, MODE_TIME_ATTACK,
    THEME_CYBERPUNK, THEME_DOJO, THEME_SPACE,
    TARGET_FPS,
)


# ────────────────────────────────────────────────────────────────────────────
# FONT CACHE
# ────────────────────────────────────────────────────────────────────────────
class FontCache:
    """
    Loads fonts once and caches them.
    Tries to load a custom font from assets/fonts/; falls back to system font.
    """
    _cache: dict[tuple, pygame.font.Font] = {}
    _custom_font_path: str | None = None

    @classmethod
    def init(cls):
        # Look for any .ttf file in fonts dir
        if os.path.isdir(FONTS_DIR):
            for f in os.listdir(FONTS_DIR):
                if f.lower().endswith(".ttf"):
                    cls._custom_font_path = os.path.join(FONTS_DIR, f)
                    break

    @classmethod
    def get(cls, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in cls._cache:
            if cls._custom_font_path:
                try:
                    cls._cache[key] = pygame.font.Font(cls._custom_font_path, size)
                    return cls._cache[key]
                except Exception:
                    pass
            cls._cache[key] = pygame.font.SysFont("Consolas", size, bold=bold)
        return cls._cache[key]


def _render_glow_text(surface, text, font, color, cx, cy, glow_color=None, glow_passes=3):
    """Render text with a coloured neon glow."""
    gc = glow_color or color
    for r in range(glow_passes, 0, -1):
        a   = max(20, 80 // r)
        gs  = font.render(text, True, (*gc, a))
        gs.set_alpha(a)
        for dx, dy in [(-r, 0), (r, 0), (0, -r), (0, r)]:
            rect = gs.get_rect(center=(cx + dx, cy + dy))
            surface.blit(gs, rect)
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(cx, cy))
    surface.blit(surf, rect)


def _panel(surface: pygame.Surface, rect: pygame.Rect, color=DARK_PANEL, radius=18):
    """Draw a semi-transparent rounded panel."""
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, color, s.get_rect(), border_radius=radius)
    surface.blit(s, rect.topleft)


# ────────────────────────────────────────────────────────────────────────────
# GLOW BUTTON
# ────────────────────────────────────────────────────────────────────────────
class GlowButton:
    """
    Clickable / hoverable button with neon glow animation.
    Supports both mouse and a selected-via-keyboard highlight.
    """

    def __init__(self, text: str, cx: int, cy: int,
                 width: int = 260, height: int = 60,
                 color: tuple = NEON_CYAN, font_size: int = FONT_SMALL):
        self.text    = text
        self.rect    = pygame.Rect(0, 0, width, height)
        self.rect.center = (cx, cy)
        self.color   = color
        self.font    = FontCache.get(font_size, bold=True)
        self._tick   = 0
        self.hovered = False
        self.selected= False   # keyboard navigation

    def update(self, mouse_pos: tuple[int, int]):
        self.hovered = self.rect.collidepoint(mouse_pos)
        self._tick  += 1

    def is_clicked(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface: pygame.Surface):
        active = self.hovered or self.selected
        pulse  = 0.7 + 0.3 * math.sin(self._tick * 0.1)
        alpha  = int(200 * pulse) if active else 120

        # Background fill
        bg = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        border_color = (*self.color, alpha)
        fill_color   = (*[c // 5 for c in self.color], 140 if active else 80)
        pygame.draw.rect(bg, fill_color,   bg.get_rect(), border_radius=12)
        pygame.draw.rect(bg, border_color, bg.get_rect(), width=2, border_radius=12)
        surface.blit(bg, self.rect.topleft)

        # Glow
        if active:
            for r in range(1, 4):
                gs = pygame.Surface((self.rect.width + r*4, self.rect.height + r*4), pygame.SRCALPHA)
                gc = (*self.color, max(0, 60 - r*15))
                pygame.draw.rect(gs, gc, gs.get_rect(), width=2, border_radius=14 + r)
                surface.blit(gs, (self.rect.x - r*2, self.rect.y - r*2))

        # Text
        tc = WHITE if active else tuple(min(255, c + 40) for c in self.color)
        _render_glow_text(surface, self.text, self.font, tc,
                          self.rect.centerx, self.rect.centery,
                          glow_color=self.color, glow_passes=2 if active else 1)


# ────────────────────────────────────────────────────────────────────────────
# HUD
# ────────────────────────────────────────────────────────────────────────────
class HUD:
    """Draws in-game heads-up display: score, lives, combo, active powers, FPS."""

    def __init__(self):
        self.f_large  = FontCache.get(FONT_LARGE,  bold=True)
        self.f_medium = FontCache.get(FONT_MEDIUM, bold=True)
        self.f_small  = FontCache.get(FONT_SMALL,  bold=True)
        self.f_tiny   = FontCache.get(FONT_TINY)

    def draw(self, surface: pygame.Surface, state: dict):
        """
        state keys:
          score, high_score, lives, combo, mode, time_left,
          active_powers: list[str], fps, double_score_active,
          shield_active, slow_mo_active, game_mode
        """
        # ── Score ───────────────────────────────────────────────────────
        sc = state.get("score", 0)
        hs = state.get("high_score", 0)
        color = NEON_YELLOW if state.get("double_score_active") else NEON_CYAN
        _render_glow_text(surface, f"{sc:06d}", self.f_large, color,
                          SCREEN_W // 2, HUD_PADDING + 36, glow_color=color)
        hi_surf = self.f_tiny.render(f"BEST {hs:06d}", True, (150, 150, 200))
        surface.blit(hi_surf, (SCREEN_W // 2 - hi_surf.get_width() // 2, HUD_PADDING + 82))

        # ── Lives (heart icons) ─────────────────────────────────────────
        lives = state.get("lives", 0)
        for i in range(3):
            c = NEON_PINK if i < lives else (50, 20, 40)
            x = HUD_PADDING + i * 38
            y = HUD_PADDING
            pygame.draw.polygon(surface, c, _heart_points(x + 14, y + 14, 12))

        # ── Combo ────────────────────────────────────────────────────────
        combo = state.get("combo", 0)
        if combo > 1:
            cc = GOLD if combo >= 5 else NEON_ORANGE
            _render_glow_text(surface, f"×{combo} COMBO", self.f_medium, cc,
                              SCREEN_W // 2, HUD_PADDING + 120, glow_color=cc)

        # ── Mode label ───────────────────────────────────────────────────
        mode = state.get("game_mode", MODE_ARCADE)
        ms = self.f_tiny.render(mode.upper(), True, NEON_PURPLE)
        surface.blit(ms, (SCREEN_W - ms.get_width() - HUD_PADDING, HUD_PADDING))

        # ── Time left (Time Attack) ──────────────────────────────────────
        tl = state.get("time_left")
        if tl is not None:
            secs = max(0, tl // TARGET_FPS)
            tc   = NEON_GREEN if secs > 20 else (RED if secs < 10 else NEON_YELLOW)
            _render_glow_text(surface, f"{secs:02d}s", self.f_medium, tc,
                              SCREEN_W - 80, HUD_PADDING + 40, glow_color=tc)

        # ── Active power icons ───────────────────────────────────────────
        powers = state.get("active_powers", [])
        px = HUD_PADDING
        py = SCREEN_H - 60
        power_colors = {
            "shield": NEON_GREEN,  "double_score": NEON_YELLOW,
            "slow_mo": NEON_PURPLE, "freeze": NEON_CYAN,
        }
        for pwr in powers:
            pc = power_colors.get(pwr, WHITE)
            _render_glow_text(surface, f"[{pwr.upper()}]", self.f_tiny, pc,
                              px + 60, py, glow_color=pc)
            px += 130

        # ── Shield overlay ───────────────────────────────────────────────
        if state.get("shield_active"):
            s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.rect(s, (*NEON_GREEN, 20), s.get_rect())
            pygame.draw.rect(s, (*NEON_GREEN, 80), s.get_rect(), width=6)
            surface.blit(s, (0, 0))

        # ── FPS ──────────────────────────────────────────────────────────
        if state.get("show_fps"):
            fps_surf = self.f_tiny.render(f"FPS {state.get('fps', 0):.0f}", True, (100, 255, 100))
            surface.blit(fps_surf, (SCREEN_W - fps_surf.get_width() - HUD_PADDING,
                                    SCREEN_H - fps_surf.get_height() - HUD_PADDING))

        # ── Gesture indicator ────────────────────────────────────────────
        gesture = state.get("gesture", "")
        if gesture not in ("NONE", "", "POINTING"):
            gs_surf = self.f_tiny.render(f"✋ {gesture}", True, NEON_ORANGE)
            surface.blit(gs_surf, (HUD_PADDING, SCREEN_H - 90))


def _heart_points(cx, cy, r):
    """Approximate heart shape as a polygon."""
    pts = []
    for angle in range(0, 360, 5):
        a = math.radians(angle)
        x = cx + r * (16 * math.sin(a)**3) / 16
        y = cy - r * (13*math.cos(a) - 5*math.cos(2*a) - 2*math.cos(3*a) - math.cos(4*a)) / 16
        pts.append((int(x), int(y)))
    return pts


# ────────────────────────────────────────────────────────────────────────────
# MAIN MENU
# ────────────────────────────────────────────────────────────────────────────
class MainMenu:
    def __init__(self):
        self.f_title = FontCache.get(FONT_LARGE + 20, bold=True)
        self.f_sub   = FontCache.get(FONT_SMALL)
        self._tick   = 0
        self.buttons = [
            GlowButton("▶  PLAY",         SCREEN_W//2, SCREEN_H//2 - 50,  color=NEON_CYAN),
            GlowButton("👤  PROFILE",      SCREEN_W//2 - 120, SCREEN_H//2 + 10,  color=NEON_GREEN),
            GlowButton("🛒  SHOP",         SCREEN_W//2 + 120, SCREEN_H//2 + 10,  color=NEON_ORANGE),
            GlowButton("🏆  LEADERBOARD",  SCREEN_W//2, SCREEN_H//2 + 70,  color=NEON_YELLOW),
            GlowButton("⚙  SETTINGS",     SCREEN_W//2, SCREEN_H//2 + 130, color=NEON_PURPLE),
            GlowButton("✕  QUIT",         SCREEN_W//2, SCREEN_H//2 + 190, color=NEON_PINK),
        ]

    def update(self, events, mouse_pos):
        self._tick += 1
        for btn in self.buttons:
            btn.update(mouse_pos)
        for event in events:
            for i, btn in enumerate(self.buttons):
                if btn.is_clicked(event):
                    return ["play", "profile", "shop", "leaderboard", "settings", "quit"][i]
        return None

    def draw(self, surface: pygame.Surface):
        # Animated title
        wave = 6 * math.sin(self._tick * 0.05)
        _render_glow_text(surface, "BLADE HAND", self.f_title, NEON_CYAN,
                          SCREEN_W // 2, 130 + int(wave), glow_color=NEON_PINK, glow_passes=4)
        _render_glow_text(surface, "GESTURE FRUIT NINJA", self.f_sub, NEON_PURPLE,
                          SCREEN_W // 2, 210)
        # Instruction
        ins = FontCache.get(FONT_TINY).render("Point your index finger at the camera to slice!", True, (150, 150, 200))
        surface.blit(ins, (SCREEN_W//2 - ins.get_width()//2, SCREEN_H - 60))
        for btn in self.buttons:
            btn.draw(surface)


# ────────────────────────────────────────────────────────────────────────────
# MODE SELECT
# ────────────────────────────────────────────────────────────────────────────
class ModeSelectScreen:
    MODES = [MODE_ARCADE, MODE_SURVIVAL, MODE_TIME_ATTACK]
    DESCS = [
        "Classic endless play — beat your high score!",
        "One life only — how long can you survive?",
        "60 seconds — slice as many as you can!",
    ]
    COLORS = [NEON_CYAN, NEON_PINK, NEON_GREEN]

    def __init__(self):
        self.f_title = FontCache.get(FONT_MEDIUM, bold=True)
        self.f_desc  = FontCache.get(FONT_TINY)
        self.buttons = [
            GlowButton(m, SCREEN_W//2, 260 + i*110, color=self.COLORS[i])
            for i, m in enumerate(self.MODES)
        ]
        self.back_btn = GlowButton("← BACK", SCREEN_W//2, SCREEN_H - 70, color=NEON_PURPLE)

    def update(self, events, mouse_pos):
        for btn in self.buttons + [self.back_btn]:
            btn.update(mouse_pos)
        for event in events:
            for i, btn in enumerate(self.buttons):
                if btn.is_clicked(event):
                    return self.MODES[i]
            if self.back_btn.is_clicked(event):
                return "back"
        return None

    def draw(self, surface: pygame.Surface):
        _render_glow_text(surface, "SELECT MODE", self.f_title, NEON_CYAN,
                          SCREEN_W//2, 160, glow_color=NEON_CYAN)
        for i, (btn, desc) in enumerate(zip(self.buttons, self.DESCS)):
            btn.draw(surface)
            ds = self.f_desc.render(desc, True, (140, 140, 180))
            surface.blit(ds, (SCREEN_W//2 - ds.get_width()//2, 298 + i*110))
        self.back_btn.draw(surface)


# ────────────────────────────────────────────────────────────────────────────
# PAUSE OVERLAY
# ────────────────────────────────────────────────────────────────────────────
class PauseOverlay:
    def __init__(self):
        self.f_title = FontCache.get(FONT_LARGE, bold=True)
        self.buttons = [
            GlowButton("▶ RESUME",   SCREEN_W//2, SCREEN_H//2 + 20,  color=NEON_GREEN),
            GlowButton("⚙ SETTINGS", SCREEN_W//2, SCREEN_H//2 + 100, color=NEON_PURPLE),
            GlowButton("⏏ MAIN MENU",SCREEN_W//2, SCREEN_H//2 + 180, color=NEON_PINK),
        ]

    def update(self, events, mouse_pos):
        for btn in self.buttons:
            btn.update(mouse_pos)
        for event in events:
            for i, btn in enumerate(self.buttons):
                if btn.is_clicked(event):
                    return ["resume", "settings", "menu"][i]
        return None

    def draw(self, surface: pygame.Surface):
        # Dim overlay
        dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dim.fill((0, 0, 10, 160))
        surface.blit(dim, (0, 0))
        _render_glow_text(surface, "PAUSED", self.f_title, NEON_CYAN,
                          SCREEN_W//2, SCREEN_H//2 - 80, glow_color=NEON_CYAN, glow_passes=4)
        for btn in self.buttons:
            btn.draw(surface)


# ────────────────────────────────────────────────────────────────────────────
# GAME OVER SCREEN
# ────────────────────────────────────────────────────────────────────────────
class GameOverScreen:
    def __init__(self):
        self.f_title  = FontCache.get(FONT_LARGE, bold=True)
        self.f_score  = FontCache.get(FONT_MEDIUM, bold=True)
        self.f_small  = FontCache.get(FONT_SMALL)
        self.f_tiny   = FontCache.get(FONT_TINY)
        self.buttons  = [
            GlowButton("▶ PLAY AGAIN",  SCREEN_W//2, SCREEN_H//2 + 130, color=NEON_GREEN),
            GlowButton("⏏ MAIN MENU",   SCREEN_W//2, SCREEN_H//2 + 210, color=NEON_PINK),
        ]
        self._tick    = 0

    def update(self, events, mouse_pos):
        self._tick += 1
        for btn in self.buttons:
            btn.update(mouse_pos)
        for event in events:
            for i, btn in enumerate(self.buttons):
                if btn.is_clicked(event):
                    return ["replay", "menu"][i]
        return None

    def draw(self, surface: pygame.Surface, score: int, high_score: int,
             is_new_record: bool, mode: str):
        dim = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        dim.fill((0, 0, 10, 180))
        surface.blit(dim, (0, 0))

        _render_glow_text(surface, "GAME OVER", self.f_title, NEON_PINK,
                          SCREEN_W//2, SCREEN_H//2 - 160, glow_color=NEON_PINK, glow_passes=4)
        _render_glow_text(surface, f"SCORE  {score:06d}", self.f_score, NEON_YELLOW,
                          SCREEN_W//2, SCREEN_H//2 - 60, glow_color=NEON_YELLOW)
        _render_glow_text(surface, f"BEST   {high_score:06d}", self.f_small,
                          (180, 180, 255), SCREEN_W//2, SCREEN_H//2)

        if is_new_record:
            wave = int(8 * math.sin(self._tick * 0.2))
            _render_glow_text(surface, "✦ NEW HIGH SCORE! ✦", self.f_small, GOLD,
                              SCREEN_W//2, SCREEN_H//2 + 55 + wave, glow_color=GOLD)

        mode_s = self.f_tiny.render(mode.upper(), True, NEON_PURPLE)
        surface.blit(mode_s, (SCREEN_W//2 - mode_s.get_width()//2, SCREEN_H//2 + 95))

        for btn in self.buttons:
            btn.draw(surface)


# ────────────────────────────────────────────────────────────────────────────
# LEADERBOARD SCREEN
# ────────────────────────────────────────────────────────────────────────────
class LeaderboardScreen:
    def __init__(self):
        self.f_title  = FontCache.get(FONT_MEDIUM, bold=True)
        self.f_entry  = FontCache.get(FONT_SMALL,  bold=True)
        self.f_tiny   = FontCache.get(FONT_TINY)
        self.back_btn = GlowButton("← BACK", SCREEN_W//2, SCREEN_H - 60, color=NEON_PURPLE)

    def update(self, events, mouse_pos):
        self.back_btn.update(mouse_pos)
        for event in events:
            if self.back_btn.is_clicked(event):
                return "back"
        return None

    def draw(self, surface: pygame.Surface, entries: list[dict]):
        _panel(surface, pygame.Rect(SCREEN_W//2 - 340, 80, 680, SCREEN_H - 160))
        _render_glow_text(surface, "LEADERBOARD", self.f_title, GOLD,
                          SCREEN_W//2, 130, glow_color=GOLD)

        row_colors = [GOLD, (200, 200, 200), (180, 120, 60)]

        for i, entry in enumerate(entries[:10]):
            y   = 200 + i * 52
            rc  = row_colors[i] if i < 3 else (160, 160, 200)
            rank = f"#{i+1}"
            name = entry.get("name", "Player")[:12]
            sc   = entry.get("score", 0)
            mode = entry.get("mode", "")

            rk_s  = self.f_entry.render(rank,        True, rc)
            nm_s  = self.f_entry.render(name,        True, WHITE)
            sc_s  = self.f_entry.render(f"{sc:06d}", True, NEON_YELLOW)
            md_s  = self.f_tiny.render(mode,         True, NEON_PURPLE)

            surface.blit(rk_s,  (SCREEN_W//2 - 280, y))
            surface.blit(nm_s,  (SCREEN_W//2 - 180, y))
            surface.blit(sc_s,  (SCREEN_W//2 + 60,  y))
            surface.blit(md_s,  (SCREEN_W//2 + 200, y + 8))

        self.back_btn.draw(surface)


# ────────────────────────────────────────────────────────────────────────────
# SETTINGS SCREEN
# ────────────────────────────────────────────────────────────────────────────
class SettingsScreen:
    def __init__(self):
        self.f_title  = FontCache.get(FONT_MEDIUM, bold=True)
        self.f_label  = FontCache.get(FONT_SMALL)
        self.f_val    = FontCache.get(FONT_SMALL,  bold=True)
        self.f_tiny   = FontCache.get(FONT_TINY)
        # Options represented as toggle buttons
        self.btns = {
            "sfx"    : GlowButton("SFX",    SCREEN_W//2 - 220, 280, width=180, color=NEON_GREEN),
            "music"  : GlowButton("MUSIC",  SCREEN_W//2 + 40,  280, width=180, color=NEON_GREEN),
            "theme_c": GlowButton(THEME_CYBERPUNK, SCREEN_W//2 - 300, 380, width=200, color=NEON_CYAN),
            "theme_d": GlowButton(THEME_DOJO,      SCREEN_W//2,       380, width=200, color=NEON_ORANGE),
            "theme_s": GlowButton(THEME_SPACE,     SCREEN_W//2 + 300, 380, width=200, color=NEON_PURPLE),
            "debug"  : GlowButton("DEBUG",  SCREEN_W//2 - 200, 470, width=180, color=NEON_PINK),
            "fps"    : GlowButton("SHOW FPS",SCREEN_W//2 + 40, 470, width=180, color=NEON_PINK),
            "fs"     : GlowButton("FULLSCREEN", SCREEN_W//2 - 80, 560, width=240, color=NEON_YELLOW),
        }
        self.back_btn = GlowButton("← BACK", SCREEN_W//2, SCREEN_H - 60, color=NEON_PURPLE)

    def update(self, events, mouse_pos):
        for btn in list(self.btns.values()) + [self.back_btn]:
            btn.update(mouse_pos)
        for event in events:
            if self.back_btn.is_clicked(event):
                return "back"
            for key, btn in self.btns.items():
                if btn.is_clicked(event):
                    return f"toggle_{key}"
        return None

    def draw(self, surface: pygame.Surface, cfg: dict):
        _panel(surface, pygame.Rect(SCREEN_W//2 - 380, 120, 760, SCREEN_H - 200))
        _render_glow_text(surface, "SETTINGS", self.f_title, NEON_CYAN,
                          SCREEN_W//2, 170, glow_color=NEON_CYAN)
        # Section labels
        def sec(text, y):
            s = self.f_tiny.render(text, True, (150, 150, 200))
            surface.blit(s, (SCREEN_W//2 - s.get_width()//2, y))

        sec("─── AUDIO ───", 248)
        sec("─── THEME ───", 348)
        sec("─── DISPLAY ───", 440)

        for key, btn in self.btns.items():
            # Highlight if active
            active_keys = {
                "sfx":    cfg.get("sfx_on"),
                "music":  cfg.get("music_on"),
                "debug":  cfg.get("debug"),
                "fps":    cfg.get("show_fps"),
                "fs":     cfg.get("fullscreen"),
                "theme_c":cfg.get("theme") == THEME_CYBERPUNK,
                "theme_d":cfg.get("theme") == THEME_DOJO,
                "theme_s":cfg.get("theme") == THEME_SPACE,
            }
            btn.selected = active_keys.get(key, False)
            btn.draw(surface)

        self.back_btn.draw(surface)


# ────────────────────────────────────────────────────────────────────────────
# PROFILE / CREATE / EDIT SCREEN
# ────────────────────────────────────────────────────────────────────────────
class ProfileScreen:
    """Create or edit a player profile: username (required), avatar, country."""

    AVATARS = ["neon", "fire", "ice", "shadow", "galaxy"]
    COUNTRIES = ["USA", "Japan", "India", "UK", "Canada", "Germany", "China", "Australia", "Brazil"]

    def __init__(self):
        self.f_title = FontCache.get(FONT_MEDIUM, bold=True)
        self.f_label = FontCache.get(FONT_SMALL)
        self.f_input = FontCache.get(FONT_SMALL, bold=True)
        self._tick   = 0
        self.username = ""
        self.avatar = self.AVATARS[0]
        self.country = self.COUNTRIES[0]
        self.active_input = False
        self.message = ""
        self.save_btn = GlowButton("💾 SAVE PROFILE", SCREEN_W//2 + 160, SCREEN_H - 80, width=260, color=NEON_GREEN)
        self.back_btn = GlowButton("← BACK", SCREEN_W//2 - 160, SCREEN_H - 80, width=220, color=NEON_PURPLE)
        # shop integration helpers
        self.shop_open = False

        # animation state
        self.slide = 1.0

    def load_player(self, player):
        if not player:
            return
        self.username = getattr(player, 'username', '') or ''
        self.avatar = getattr(player, 'avatar', self.AVATARS[0])
        self.country = getattr(player, 'country', self.COUNTRIES[0])

    def update(self, events, mouse_pos, player_manager=None):
        # update animation
        self._tick += 1
        self.slide = max(0.0, self.slide - 0.06)

        self.save_btn.update(mouse_pos)
        self.back_btn.update(mouse_pos)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # avatar click
                ax = SCREEN_W//2 - 220
                ay = 240
                for i, a in enumerate(self.AVATARS):
                    r = pygame.Rect(ax + i*100, ay, 72, 72)
                    if r.collidepoint(event.pos):
                        self.avatar = a
                # country click
                cx = SCREEN_W//2 - 200
                cy = 340
                for i, c in enumerate(self.COUNTRIES):
                    r = pygame.Rect(cx + (i%5)*140, cy + (i//5)*48, 130, 40)
                    if r.collidepoint(event.pos):
                        self.country = c

            if event.type == pygame.KEYDOWN:
                if self.active_input:
                    if event.key == pygame.K_BACKSPACE:
                        self.username = self.username[:-1]
                    elif event.key == pygame.K_RETURN:
                        self.active_input = False
                    else:
                        if len(self.username) < 20 and event.unicode.isprintable():
                            self.username += event.unicode

            # button clicks
            if self.save_btn.is_clicked(event):
                if not self.username.strip():
                    self.message = "Username is required"
                else:
                    # persist via player_manager
                    if player_manager:
                        pm = player_manager
                        if getattr(pm, 'player', None) and pm.player.username not in (None, "Player", ""):
                            pm.edit_profile(username=self.username.strip(), avatar=self.avatar, country=self.country)
                        else:
                            pm.create_profile(self.username.strip(), self.avatar, self.country)
                    self.message = "Profile saved"
                    return "saved"

            if self.back_btn.is_clicked(event):
                return "back"

            # detect click on username box to activate text input
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                ux = SCREEN_W//2 - 260
                uy = 180
                ub = pygame.Rect(ux, uy, 520, 48)
                self.active_input = ub.collidepoint(event.pos)

        return None

    def draw(self, surface, player=None):
        # slide-in animation offset
        oy = int(80 * self.slide)
        _panel(surface, pygame.Rect(SCREEN_W//2 - 420, 120 - oy, 840, SCREEN_H - 240))
        _render_glow_text(surface, "PROFILE", self.f_title, NEON_CYAN,
                          SCREEN_W//2, 160 - oy, glow_color=NEON_CYAN)

        # Username input
        ux = SCREEN_W//2 - 260
        uy = 180 - oy
        pygame.draw.rect(surface, (20,20,30), (ux, uy, 520, 48), border_radius=8)
        txt = self.username if self.username else "Enter username..."
        color = WHITE if self.username else (140,140,160)
        txt_s = self.f_input.render(txt, True, color)
        surface.blit(txt_s, (ux + 12, uy + 10))
        # Username label
        lbl = self.f_label.render("USERNAME (required)", True, (180,180,200))
        surface.blit(lbl, (ux, uy - 26))

        # Avatars
        ax = SCREEN_W//2 - 220
        ay = 240 - oy
        a_label = self.f_label.render("AVATAR", True, (180,180,200))
        surface.blit(a_label, (ax, ay - 34))
        for i, a in enumerate(self.AVATARS):
            x = ax + i*100
            col = NEON_PINK if a == self.avatar else (80,80,100)
            pygame.draw.rect(surface, col, (x, ay, 72, 72), border_radius=12)
            nm = self.f_label.render(a.upper(), True, WHITE if a==self.avatar else (160,160,160))
            surface.blit(nm, (x + 8, ay + 76))

        # Countries
        cx = SCREEN_W//2 - 200
        cy = 340 - oy
        c_label = self.f_label.render("COUNTRY", True, (180,180,200))
        surface.blit(c_label, (cx, cy - 34))
        for i, c in enumerate(self.COUNTRIES):
            rx = cx + (i%5)*140
            ry = cy + (i//5)*48
            selected = c == self.country
            col = NEON_CYAN if selected else (30,30,40)
            pygame.draw.rect(surface, col, (rx, ry, 130, 40), border_radius=8)
            cs = self.f_label.render(c, True, WHITE if selected else (160,160,160))
            surface.blit(cs, (rx + 10, ry + 8))

        # Message
        if self.message:
            m_s = self.f_label.render(self.message, True, NEON_YELLOW)
            surface.blit(m_s, (SCREEN_W//2 - m_s.get_width()//2, SCREEN_H - 120))

        # Buttons
        self.save_btn.draw(surface)
        self.back_btn.draw(surface)

        # small hint
        hint = self.f_label.render("You can edit this profile later from the Main Menu.", True, (150,150,180))
        surface.blit(hint, (SCREEN_W//2 - hint.get_width()//2, SCREEN_H - 40))


# ────────────────────────────────────────────────────────────────────────────
# SHOP SCREEN
# ────────────────────────────────────────────────────────────────────────────
class ShopScreen:
    """Simple shop UI: categories, item cards, purchase/equip and chest opening."""

    CATS = ['blades','trails','backgrounds']

    def __init__(self, shop_manager, inventory_manager, player_manager, chest_manager, sound=None):
        self.shop = shop_manager
        self.inv = inventory_manager
        self.pm  = player_manager
        self.chest = chest_manager
        self.sound = sound
        self.f_title = FontCache.get(FONT_MEDIUM, bold=True)
        self.f_label = FontCache.get(FONT_SMALL)
        self._tick = 0
        self.cat_idx = 0
        self.selected = None
        self.confirm_mode = False
        self.confirm_item = None
        self.confirm_category = None
        self.last_purchase_result = None
        self.opening = None
        self.open_anim = 0

    def update(self, events, mouse_pos):
        self._tick += 1
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                # category clicks
                cx = SCREEN_W//2 - 320
                for i, c in enumerate(self.CATS):
                    r = pygame.Rect(cx + i*220, 160, 200, 40)
                    if r.collidepoint(event.pos):
                        self.cat_idx = i; self.selected = None
                # item click
                ix = SCREEN_W//2 - 360
                iy = 240
                items = self.shop.get_catalog(self.CATS[self.cat_idx])
                for i, it in enumerate(items):
                    r = pygame.Rect(ix + (i%3)*240, iy + (i//3)*140, 220, 120)
                    if r.collidepoint(event.pos):
                        self.selected = it['key']
                        self.selected_item = it
                # chest areas
                chest_x = SCREEN_W - 220
                chest_y = SCREEN_H - 220
                if pygame.Rect(chest_x, chest_y, 180, 160).collidepoint(event.pos):
                    # open a common chest for testing
                    self.opening = 'common'; self.open_anim = 30
                    if self.sound: self.sound.play('chest_open')

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return 'back'

            # handle purchase confirm clicks
            if event.type == pygame.MOUSEBUTTONDOWN and event.button==1 and self.selected:
                # purchase / equip button area
                bx = SCREEN_W//2 + 260
                by = SCREEN_H//2 + 140
                b_rect = pygame.Rect(bx-60, by-24, 120, 48)
                if b_rect.collidepoint(event.pos):
                    # if owned -> equip, else confirm purchase
                    cat = self.CATS[self.cat_idx]
                    owned = self.inv.is_owned(cat, self.selected)
                    if owned:
                        ok = self.shop.equip('blade' if cat=='blades' else ('trail' if cat=='trails' else 'background'), self.selected)
                        self.last_purchase_result = {'type':'equip','item':self.selected,'ok':ok}
                        if self.sound and ok: self.sound.play('equip')
                    else:
                        self.confirm_mode = True
                        self.confirm_item = self.selected
                        self.confirm_category = cat
                    
            # confirmation modal handling
            if self.confirm_mode and event.type == pygame.MOUSEBUTTONDOWN and event.button==1:
                # yes/no buttons
                yx = SCREEN_W//2 - 120
                yy = SCREEN_H//2 + 40
                yes_rect = pygame.Rect(yx, yy, 100, 44)
                no_rect = pygame.Rect(yx + 140, yy, 100, 44)
                if yes_rect.collidepoint(event.pos):
                    # perform purchase
                    ok = self.shop.purchase(self.confirm_category, self.confirm_item)
                    self.last_purchase_result = {'type':'purchase','item':self.confirm_item,'ok':ok}
                    if self.sound and ok: self.sound.play('purchase')
                    self.confirm_mode = False
                    self.confirm_item = None
                    self.confirm_category = None
                if no_rect.collidepoint(event.pos):
                    self.confirm_mode = False
                    self.confirm_item = None
                    self.confirm_category = None

        # animate chest opening
        if self.opening:
            self.open_anim -= 1
            if self.open_anim <= 0:
                rewards = self.chest.open_chest(self.opening)
                # create simple textual popups via notifier if available
                # we'll return rewards to main loop via a property
                self.last_chest_rewards = rewards
                self.opening = None
        return None

    def draw(self, surface):
        _panel(surface, pygame.Rect(SCREEN_W//2 - 460, 120, 920, SCREEN_H - 240))
        _render_glow_text(surface, 'SHOP', self.f_title, NEON_CYAN, SCREEN_W//2, 140, glow_color=NEON_CYAN)

        # categories
        cx = SCREEN_W//2 - 320
        for i, c in enumerate(self.CATS):
            r = pygame.Rect(cx + i*220, 160, 200, 40)
            col = NEON_ORANGE if i==self.cat_idx else (40,40,50)
            pygame.draw.rect(surface, col, r, border_radius=10)
            t = self.f_label.render(c.upper(), True, WHITE if i==self.cat_idx else (160,160,160))
            surface.blit(t, (r.x + 12, r.y + 8))

        # items
        items = self.shop.get_catalog(self.CATS[self.cat_idx])
        ix = SCREEN_W//2 - 360
        iy = 240
        for i, it in enumerate(items):
            r = pygame.Rect(ix + (i%3)*240, iy + (i//3)*140, 220, 120)
            active = (self.selected == it['key'])
            pygame.draw.rect(surface, (30,30,40), r, border_radius=12)
            if active:
                for s in range(1,4):
                    pygame.draw.rect(surface, (*NEON_CYAN, 20), r.inflate(s*6,s*6), border_radius=14, width=2)
            nm = self.f_label.render(it['name'], True, WHITE)
            price = f"{it['coins']}c" + (f" / {it['gems']}g" if it['gems'] else '')
            pr = self.f_label.render(price, True, NEON_YELLOW)
            surface.blit(nm, (r.x + 12, r.y + 12))
            surface.blit(pr, (r.x + 12, r.y + 44))
            # owned/equipped badge
            owned = self.inv.is_owned(self.CATS[self.cat_idx], it['key'])
            if owned:
                b = self.f_label.render('OWNED', True, NEON_GREEN)
                surface.blit(b, (r.x + 120, r.y + 12))

        # purchase / equip button
        if self.selected:
            bx = SCREEN_W//2 + 260
            by = SCREEN_H//2 + 140
            btn_rect = pygame.Rect(bx-60, by-24, 120, 48)
            pygame.draw.rect(surface, NEON_CYAN, btn_rect, border_radius=10)
            cat = self.CATS[self.cat_idx]
            owned = self.inv.is_owned(cat, self.selected)
            label = 'EQUIP' if owned else 'BUY'
            l_s = self.f_label.render(label, True, (10,10,20))
            surface.blit(l_s, (btn_rect.x + 28, btn_rect.y + 12))

        # confirmation modal
        if self.confirm_mode:
            mrect = pygame.Rect(SCREEN_W//2 - 220, SCREEN_H//2 - 100, 440, 220)
            _panel(surface, mrect, color=(20,20,30), radius=12)
            q = self.f_label.render(f"Buy {self.confirm_item}?", True, NEON_YELLOW)
            surface.blit(q, (SCREEN_W//2 - q.get_width()//2, SCREEN_H//2 - 40))
            # yes/no
            yx = SCREEN_W//2 - 120
            yy = SCREEN_H//2 + 40
            pygame.draw.rect(surface, NEON_GREEN, (yx, yy, 100, 44), border_radius=8)
            pygame.draw.rect(surface, NEON_PINK, (yx + 140, yy, 100, 44), border_radius=8)
            yes = self.f_label.render('YES', True, (10,10,10))
            no  = self.f_label.render('NO', True, (10,10,10))
            surface.blit(yes, (yx + 34, yy + 12))
            surface.blit(no, (yx + 174, yy + 12))

        # chest area
        chest_x = SCREEN_W - 220
        chest_y = SCREEN_H - 220
        chest_rect = pygame.Rect(chest_x, chest_y, 180, 160)
        pygame.draw.rect(surface, (40,20,30), chest_rect, border_radius=12)
        ch = self.f_label.render('OPEN CHEST', True, NEON_YELLOW)
        surface.blit(ch, (chest_x + 18, chest_y + 66))

        # player currency
        if self.pm and getattr(self.pm,'player',None):
            money = f"Coins: {self.pm.player.coins}   Gems: {self.pm.player.gems}"
            m_s = self.f_label.render(money, True, NEON_YELLOW)
            surface.blit(m_s, (SCREEN_W//2 - m_s.get_width()//2, SCREEN_H - 60))