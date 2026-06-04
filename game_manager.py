"""
game_manager.py  (FULL UPGRADE)
================================
Wires in:
  • BossManager        — rare giant boss fruits
  • BladeModeManager   — fire / ice blade switching
  • ShockwaveBlast     — fist gesture AoE
  • SlashArc           — anime slash trail
  • SpeedLines         — combo entry burst
  • ImpactFlash        — edge flash on events
  • SlowMoController   — cinematic slow-mo
  • ComboAnimator      — big animated combo text
  • DynamicBackground  — score-reactive background
  • VoiceReactor       — TTS voice lines
  • CinematicBars      — letterbox on slow-mo
"""

import os, json, random, time
import pygame
from settings import (
    SCREEN_W, SCREEN_H, TARGET_FPS,
    STARTING_LIVES, MISS_PENALTY, BOMB_LIVES_PENALTY,
    BASE_SLICE_POINTS, FAST_SWIPE_BONUS,
    INITIAL_SPAWN_INTERVAL, MIN_SPAWN_INTERVAL,
    BOMB_CHANCE, SPECIAL_FRUIT_CHANCE, SPEED_SCALE_FACTOR,
    COMBO_WINDOW, COMBO_2_MULT, COMBO_3_MULT, COMBO_5_MULT, COMBO_10_MULT,
    FREEZE_DURATION, SLOW_MO_DURATION, DOUBLE_SCORE_DURATION,
    FIST_SHIELD_DURATION, TWOFINGER_COMBO_FRAMES, PALM_SLOWMO_FRAMES,
    SCREEN_SHAKE_INTENSITY, SCREEN_SHAKE_FRAMES,
    MODE_ARCADE, MODE_SURVIVAL, MODE_TIME_ATTACK, TIME_ATTACK_DURATION,
    LEADERBOARD_FILE, SAVES_DIR,
    NEON_GREEN, NEON_YELLOW, NEON_CYAN, NEON_PURPLE, RED, GOLD, NEON_ORANGE,
)
from fruit import spawn_object, Bomb, Fruit

# ── New modules ──────────────────────────────────────────────────────────────
from boss       import BossManager
from powers     import (BladeModeManager, ShockwaveBlast, SlashArc,
                         SpeedLines, ImpactFlash, VoiceReactor,
                         BLADE_FIRE, BLADE_ICE, BLADE_NORMAL)
from animations import (DynamicBackground, ComboAnimator,
                         SlowMoController, ZoomController,
                         MotionBlurOverlay, CinematicBars)

# BladeVerse managers (XP, achievements, rewards, leaderboard)
from bladeverse.player import PlayerManager
from bladeverse.firebase_stub import FirebaseClient
from bladeverse.xp import XPManager
from bladeverse.achievements import AchievementsManager
from bladeverse.rewards import RewardManager
from bladeverse.leaderboard import LeaderboardManager

STATE_MENU        = "menu"
STATE_MODE_SEL    = "mode_select"
STATE_PLAYING     = "playing"
STATE_PAUSED      = "paused"
STATE_GAME_OVER   = "game_over"
STATE_LEADERBOARD = "leaderboard"
STATE_SETTINGS    = "settings"


class GameManager:
    def __init__(self, sound_manager, particle_system, blade_trail,
                 screen_shake, hit_flash, bg_renderer, hud):
        # ── Legacy injected systems ──────────────────────────────────────
        self.sound  = sound_manager
        self.parts  = particle_system
        self.trail  = blade_trail
        self.shake  = screen_shake
        self.flash  = hit_flash
        self.bg     = bg_renderer      # BackgroundRenderer (legacy)
        self.hud    = hud

        # ── NEW cinematic / animation systems ────────────────────────────
        self.bars        = CinematicBars()
        self.zoom        = ZoomController()
        self.blur        = MotionBlurOverlay()
        self.dyn_bg      = DynamicBackground()
        self.combo_anim  = ComboAnimator()
        self.slow_mo_ctrl= SlowMoController(self.zoom, self.blur, self.bars)
        self.blade_mode  = BladeModeManager()
        self.boss_mgr    = BossManager()
        self.voice       = VoiceReactor(enabled=False)   # set True to enable TTS

        # Live effect lists
        self._shockwaves:   list[ShockwaveBlast] = []
        self._slash_arcs:   list[SlashArc]       = []
        self._speed_lines:  list[SpeedLines]     = []
        self._impact_flash: list[ImpactFlash]    = []

        # ── State ────────────────────────────────────────────────────────
        self.state       = STATE_MENU
        self._prev_state = None

        # ── Session ──────────────────────────────────────────────────────
        self.score        = 0
        self.high_score   = 0
        self.lives        = STARTING_LIVES
        self.combo        = 0
        self.combo_timer  = 0
        self.game_mode    = MODE_ARCADE
        self.objects:list = []

        # ── Spawn ────────────────────────────────────────────────────────
        self._spawn_timer    = 0
        self._spawn_interval = INITIAL_SPAWN_INTERVAL
        self._prev_tip       = None

        # ── Power timers ─────────────────────────────────────────────────
        self._freeze_timer       = 0
        self._slow_mo_timer      = 0
        self._double_score_timer = 0
        self._shield_timer       = 0
        self._combo_mode_timer   = 0

        # ── Time attack ──────────────────────────────────────────────────
        self._time_left = TIME_ATTACK_DURATION

        # ── Misc ─────────────────────────────────────────────────────────
        self._is_new_record = False
        self.leaderboard    = self._load_leaderboard()
        self.cfg = {
            "sfx_on": True, "music_on": True, "debug": False,
            "show_fps": True, "fullscreen": False,
            "theme": "Cyberpunk", "voice": False,
        }
        os.makedirs(SAVES_DIR, exist_ok=True)

        # ── BladeVerse integrations (optional player + firebase)
        # If main.py created a PlayerManager and passed it in, use it; otherwise create a local one.
        self.pm = None
        try:
            # attempt to use existing saves/player_profile.json via PlayerManager
            self.pm = PlayerManager()
        except Exception:
            self.pm = None

        self.fb = FirebaseClient()
        self.xp_mgr = XPManager(self.pm, on_level_up=self._on_level_up)
        self.notifier_queue = []
        self.ach_mgr = AchievementsManager(self.pm, notifier=self._notify)
        self.rew_mgr = RewardManager(self.pm, notifier=self._notify)
        self.lb_mgr = LeaderboardManager(self.fb, self.pm)

        # session counters
        self._session_slices = 0
        self._session_max_combo = 0
        self._notifications = []

    # ─────────────────────────────────────────────────────────────────────
    # STATE TRANSITIONS
    # ─────────────────────────────────────────────────────────────────────
    def goto(self, state):
        self._prev_state = self.state
        self.state = state

    def start_game(self, mode=MODE_ARCADE):
        self.game_mode = mode
        self.score     = 0
        self.lives     = 1 if mode == MODE_SURVIVAL else STARTING_LIVES
        self.combo     = 0; self.combo_timer = 0
        self.objects.clear(); self.parts.clear()
        self._spawn_timer = 0; self._spawn_interval = INITIAL_SPAWN_INTERVAL
        for attr in ('_freeze_timer','_slow_mo_timer','_double_score_timer',
                     '_shield_timer','_combo_mode_timer'):
            setattr(self, attr, 0)
        self._time_left = TIME_ATTACK_DURATION
        self._is_new_record = False
        self._shockwaves.clear(); self._slash_arcs.clear()
        self._speed_lines.clear(); self._impact_flash.clear()
        self.blade_mode.deactivate()
        self.slow_mo_ctrl._active = False
        self.zoom.zoom_to(1.0, speed=0.1)
        self.bars.hide()
        self.goto(STATE_PLAYING)

    # ─────────────────────────────────────────────────────────────────────
    # MAIN UPDATE
    # ─────────────────────────────────────────────────────────────────────
    def update_playing(self, tip_pos, gesture, swipe_speed, popups, fps):
        # ── Time-attack countdown ────────────────────────────────────────
        if self.game_mode == MODE_TIME_ATTACK:
            self._time_left -= 1
            if self._time_left <= 0:
                self._end_game(); return

        # ── Power timers ─────────────────────────────────────────────────
        self._tick_powers()

        # ── Dynamic BG ───────────────────────────────────────────────────
        self.dyn_bg.update(self.score)

        # ── Blade mode ───────────────────────────────────────────────────
        self.blade_mode.update(tip_pos)
        self.trail.set_mode(self.blade_mode.mode)

        # ── Gesture powers ───────────────────────────────────────────────
        self._handle_gestures(gesture, tip_pos, popups, swipe_speed)

        # ── Cinematic systems ─────────────────────────────────────────────
        self.slow_mo_ctrl.update()
        self.zoom.update()
        self.bars.update()
        self.combo_anim.update()
        self.voice.update()

        # ── Time scale ───────────────────────────────────────────────────
        ts = self.slow_mo_ctrl.time_scale
        if self._slow_mo_timer > 0: ts = min(ts, 0.38)
        if self._freeze_timer  > 0: ts = 0.0

        # ── Physics ──────────────────────────────────────────────────────
        for obj in self.objects:
            obj.update(ts)
        self.boss_mgr.update(self.score, ts)

        # ── Slash arc tracking ────────────────────────────────────────────
        if (tip_pos and self._prev_tip and swipe_speed > 15):
            color = self.blade_mode.get_trail_color()
            self._slash_arcs.append(
                SlashArc(self._prev_tip, tip_pos, color, swipe_speed))
        self._prev_tip = tip_pos

        # ── Collision / slicing ──────────────────────────────────────────
        if tip_pos and swipe_speed > 4:
            self._check_slices(tip_pos, swipe_speed, popups)
            self._check_boss_slice(tip_pos, swipe_speed, popups)
            self._check_shockwave(tip_pos, popups)

        # ── Remove off-screen objects ────────────────────────────────────
        self._remove_offscreen(popups)

        # ── Spawn ────────────────────────────────────────────────────────
        self._maybe_spawn()

        # ── Combo timer ──────────────────────────────────────────────────
        if self.combo_timer > 0:
            self.combo_timer -= 1
            if self.combo_timer == 0:
                self.combo = 0

        # ── Effect lists update ──────────────────────────────────────────
        self._shockwaves   = [s for s in self._shockwaves if s.alive]
        self._slash_arcs   = [a for a in self._slash_arcs  if a.alive]
        self._speed_lines  = [l for l in self._speed_lines if l.alive]
        self._impact_flash = [f for f in self._impact_flash if f.alive]
        for obj in self._shockwaves:  obj.update()
        for obj in self._slash_arcs:  obj.update()
        for obj in self._speed_lines: obj.update()
        for obj in self._impact_flash:obj.update()

        # ── Core systems update ──────────────────────────────────────────
        self.shake.update(); self.flash.update(); self.parts.update()

        # ── Flush notifications into popups
        try:
            from effects import ComboPopup
            for title, msg in list(self._notifications):
                popups.append(ComboPopup(f"{title}", SCREEN_W//2, 140, color=NEON_YELLOW))
            self._notifications.clear()
        except Exception:
            pass

        # ── Game over check ──────────────────────────────────────────────
        if self.lives <= 0:
            self._end_game()

    # ─────────────────────────────────────────────────────────────────────
    # DRAW EFFECTS (called from main.py after objects are drawn)
    # ─────────────────────────────────────────────────────────────────────
    def draw_effects(self, surface: pygame.Surface):
        """Draw all new effect layers onto the game surface."""
        for obj in self._slash_arcs:   obj.draw(surface)
        for obj in self._speed_lines:  obj.draw(surface)
        for obj in self._shockwaves:   obj.draw(surface)
        for obj in self._impact_flash: obj.draw(surface)
        self.blade_mode.draw(surface, None)   # particles only; tip drawn in main
        self.combo_anim.draw(surface)
        self.boss_mgr.draw(surface)
        self.bars.draw(surface)

    # ─────────────────────────────────────────────────────────────────────
    # SLICING
    # ─────────────────────────────────────────────────────────────────────
    def _check_slices(self, tip, speed, popups):
        sliced_any = False; sliced_count = 0
        for obj in self.objects:
            if obj.sliced or not obj.alive: continue
            if obj.contains_point(*tip):
                obj.sliced = True; obj.alive = False
                if isinstance(obj, Bomb):
                    self._on_bomb_hit(obj, popups)
                else:
                    self._on_fruit_slice(obj, speed, popups)
                    sliced_any = True; sliced_count += 1
        if sliced_any:
            self.sound.play("slice")
            # Trigger cinematic slow-mo on 3+ simultaneous slices
            if sliced_count >= 3 and not self.slow_mo_ctrl.active:
                self.slow_mo_ctrl.trigger(80)
                self._speed_lines.append(SpeedLines(color=(255,255,255)))
                self._impact_flash.append(ImpactFlash(color=(255,220,0), duration=10))

    def _check_boss_slice(self, tip, speed, popups):
        hit, killed, pts = self.boss_mgr.check_slice(tip)
        if not hit: return
        self.sound.play("slice")
        self.shake.trigger(intensity=14, duration=18)
        self._impact_flash.append(ImpactFlash(color=(255,60,0), duration=12))
        from effects import ComboPopup
        popups.append(ComboPopup(f"+{pts} BOSS HIT!", SCREEN_W//2, 180,
                                 color=(255,80,0)))
        if killed:
            self.score += pts
            self.parts.emit_boss_explosion(
                self.boss_mgr.boss.x, self.boss_mgr.boss.y)
            self.shake.trigger_heavy()
            self._speed_lines.append(SpeedLines(color=(255,60,0), count=60))
            self.combo_anim.trigger(99)   # special tier
            self.voice.say("ultra")
            self.sound.play("combo")
            popups.append(ComboPopup("BOSS DEFEATED!", SCREEN_W//2, 240,
                                     color=(255,200,0)))
            # BladeVerse: boss rewards, XP and achievements
            try:
                # award XP
                xp_amt = int(pts * 1.5) + 200
                self.xp_mgr.add_xp(xp_amt)
                # rewards
                self.rew_mgr.grant_for_boss()
                # achievements
                unlocked = self.ach_mgr.evaluate_on_boss_defeat()
                for a in unlocked:
                    self.rew_mgr.grant_for_achievement(a)
                    popups.append(ComboPopup("ACHIEVEMENT!", SCREEN_W//2, 180, color=NEON_YELLOW))
            except Exception:
                pass
        else:
            self.score += pts
        self.voice.say("boss")

    def _check_shockwave(self, tip, popups):
        for sw in self._shockwaves:
            for obj in self.objects:
                if obj.sliced or not obj.alive: continue
                if isinstance(obj, Bomb): continue
                dist = ((obj.x-sw.cx)**2 + (obj.y-sw.cy)**2)**0.5
                if dist < sw.get_radius():
                    obj.sliced = True; obj.alive = False
                    pts = getattr(obj,'points',10)
                    self.score += pts
                    self.parts.emit_slice(obj.x, obj.y,
                                          obj.color_outer, obj.color_inner)
                    from effects import ComboPopup
                    popups.append(ComboPopup(f"+{pts}", int(obj.x), int(obj.y),
                                             color=NEON_CYAN))

    def _on_fruit_slice(self, fruit, speed, popups):
        if self.combo_timer > 0: self.combo += 1
        else: self.combo = 1
        self.combo_timer = COMBO_WINDOW

        mult = 1.0
        if self.combo >= 10: mult = COMBO_10_MULT
        elif self.combo >= 5: mult = COMBO_5_MULT
        elif self.combo >= 3: mult = COMBO_3_MULT
        elif self.combo >= 2: mult = COMBO_2_MULT
        if self._double_score_timer > 0: mult *= 2
        if self._combo_mode_timer   > 0: mult *= 1.5
        mult *= self.blade_mode.get_damage_mult()

        pts    = fruit.points + (FAST_SWIPE_BONUS if speed > 25 else 0)
        earned = int(pts * mult)
        self.score += earned

        self.parts.emit_slice(fruit.x, fruit.y, fruit.color_outer, fruit.color_inner)

        from effects import ComboPopup
        col = GOLD if self.combo >= 5 else NEON_YELLOW
        popups.append(ComboPopup(f"+{earned}", int(fruit.x), int(fruit.y), color=col))

        if self.combo in (2, 5, 10, 20):
            self.combo_anim.trigger(self.combo)
            self._speed_lines.append(SpeedLines())
            self.sound.play("combo")
            self.voice.say("combo")
            popups.append(ComboPopup(
                f"×{self.combo} COMBO!", SCREEN_W//2, 290, color=GOLD))

        if self.combo == 10:
            self.voice.say("ultra")
            self.shake.trigger(intensity=10, duration=15)

        if hasattr(fruit, 'power'):
            self._activate_power(fruit.power, fruit.x, fruit.y, popups)

        # ── BladeVerse: grant XP and check achievements/rewards
        try:
            # increment session slices and update player stats
            self._session_slices += 1
            if self.pm:
                self.pm.record_slices(1)

            # compute XP: proportional to earned points
            xp_amt = max(1, int(earned * 0.25))
            # combo bonus XP
            xp_amt += int(self.combo * 2)
            res = self.xp_mgr.add_xp(xp_amt)
            if res.get('leveled'):
                # level up handled in callback
                pass

            # achievements: evaluate slice-related ones
            unlocked = self.ach_mgr.evaluate_on_slice(self._session_slices, self.score, self.combo, speed > 25)
            for a in unlocked:
                # grant rewards for achievement
                self.rew_mgr.grant_for_achievement(a)
                # enqueue popup
                from effects import ComboPopup
                popups.append(ComboPopup("ACHIEVEMENT!", SCREEN_W//2, 160, color=NEON_YELLOW))
        except Exception:
            pass

        # update session max combo
        if self.combo > self._session_max_combo:
            self._session_max_combo = self.combo

    def _on_bomb_hit(self, bomb, popups):
        from effects import ComboPopup
        if self._shield_timer > 0:
            popups.append(ComboPopup("SHIELD!", SCREEN_W//2, 250, color=NEON_GREEN))
            self.sound.play("shield"); return
        self.lives = max(0, self.lives - BOMB_LIVES_PENALTY)
        self.combo = 0; self.combo_timer = 0
        self.shake.trigger(); self.flash.trigger((220,40,40), duration=14)
        self.sound.play("bomb")
        self.parts.emit_bomb(bomb.x, bomb.y)
        self._impact_flash.append(ImpactFlash(color=(255,30,0), duration=18))
        popups.append(ComboPopup("BOMB!", SCREEN_W//2, 200, color=RED))

    # ─────────────────────────────────────────────────────────────────────
    # POWERS & GESTURES
    # ─────────────────────────────────────────────────────────────────────
    def _activate_power(self, power, x, y, popups):
        from effects import ComboPopup
        cfg = {
            "freeze":       (FREEZE_DURATION,       "FREEZE!",       NEON_CYAN,    (0,200,220)),
            "double_score": (DOUBLE_SCORE_DURATION,  "DOUBLE SCORE!", NEON_YELLOW,  (200,200,0)),
            "slow_mo":      (SLOW_MO_DURATION,       "SLOW MO!",      NEON_PURPLE,  (120,0,200)),
            "bomb_diffuse": (0,                      "BOMBS CLEARED!",NEON_GREEN,   (0,180,80)),
        }
        if power not in cfg: return
        dur, label, color, pc = cfg[power]
        if power == "freeze":
            self._freeze_timer = dur
        elif power == "double_score":
            self._double_score_timer = dur
        elif power == "slow_mo":
            self._slow_mo_timer = dur
            self.slow_mo_ctrl.trigger(dur)
        elif power == "bomb_diffuse":
            for obj in self.objects:
                if isinstance(obj, Bomb): obj.alive = False
        self.sound.play("power"); self.parts.emit_power(x, y, pc)
        popups.append(ComboPopup(label, SCREEN_W//2, 260, color=color))
        self._impact_flash.append(ImpactFlash(color=pc, duration=10))

    def _handle_gestures(self, gesture, tip_pos, popups, swipe_speed):
        from effects import ComboPopup
        if gesture == "FIST" and self._shield_timer <= 0:
            self._shield_timer = FIST_SHIELD_DURATION
            self.sound.play("shield")
            popups.append(ComboPopup("SHIELD ACTIVE!", SCREEN_W//2, 240, color=NEON_GREEN))
            # Shockwave blast
            if tip_pos:
                self._shockwaves.append(
                    ShockwaveBlast(tip_pos[0], tip_pos[1], color=NEON_GREEN))
            self.voice.say("shield")

        elif gesture == "TWO_FINGER" and self._combo_mode_timer <= 0:
            self._combo_mode_timer = TWOFINGER_COMBO_FRAMES
            popups.append(ComboPopup("COMBO MODE!", SCREEN_W//2, 240, color=NEON_YELLOW))
            # Activate fire blade for style
            self.blade_mode.activate_fire()
            self.voice.say("fire_blade")

        elif gesture == "OPEN_PALM" and self._slow_mo_timer <= 0:
            self._slow_mo_timer = PALM_SLOWMO_FRAMES
            self.slow_mo_ctrl.trigger(PALM_SLOWMO_FRAMES)
            popups.append(ComboPopup("SLOW-MO!", SCREEN_W//2, 240, color=NEON_PURPLE))
            # Activate ice blade
            self.blade_mode.activate_ice()
            self.voice.say("ice_blade")

    def _tick_powers(self):
        for attr in ('_freeze_timer','_slow_mo_timer','_double_score_timer',
                     '_shield_timer','_combo_mode_timer'):
            v = getattr(self, attr)
            if v > 0: setattr(self, attr, v-1)

    # ─────────────────────────────────────────────────────────────────
    # Notifications / callbacks
    # ─────────────────────────────────────────────────────────────────
    def _notify(self, title: str, message: str):
        # queue a notification to be shown as popup in the next frame
        self._notifications.append((title, message))

    def _on_level_up(self, old_level: int, new_level: int):
        # called by XPManager when a level up occurs
        try:
            self.rew_mgr.grant_levelup(old_level, new_level)
            self._notify('Level Up!', f'Level {new_level} reached')
            # achievements for reaching high levels
            unlocked = self.ach_mgr.evaluate_on_level(new_level)
            for a in unlocked:
                self.rew_mgr.grant_for_achievement(a)
        except Exception:
            pass

    # ─────────────────────────────────────────────────────────────────────
    # SPAWN
    # ─────────────────────────────────────────────────────────────────────
    def _maybe_spawn(self):
        self._spawn_timer += 1
        target = max(MIN_SPAWN_INTERVAL,
                     INITIAL_SPAWN_INTERVAL - int(self.score * SPEED_SCALE_FACTOR * 10))
        if self._spawn_interval > target: self._spawn_interval -= 1
        if self._spawn_timer >= self._spawn_interval:
            self._spawn_timer = 0
            extra = self.score * SPEED_SCALE_FACTOR
            obj = spawn_object(BOMB_CHANCE, SPECIAL_FRUIT_CHANCE)
            obj.vy *= (1 + extra)
            self.objects.append(obj)
            if random.random() < 0.25:
                obj2 = spawn_object(0, SPECIAL_FRUIT_CHANCE * 0.5)
                obj2.vy *= (1 + extra)
                self.objects.append(obj2)

    # ─────────────────────────────────────────────────────────────────────
    # OFF-SCREEN CLEANUP
    # ─────────────────────────────────────────────────────────────────────
    def _remove_offscreen(self, popups):
        from effects import ComboPopup
        remaining = []
        for obj in self.objects:
            if not obj.alive: continue
            if obj.is_off_screen():
                if not isinstance(obj, Bomb) and not obj.sliced:
                    self.lives = max(0, self.lives - MISS_PENALTY)
                    self.combo = 0; self.combo_timer = 0
                    self.sound.play("miss")
                    self.flash.trigger((150,30,30), duration=8)
                    popups.append(ComboPopup("-LIFE", int(obj.x), SCREEN_H-60, color=RED))
            else:
                remaining.append(obj)
        self.objects = remaining

    # ─────────────────────────────────────────────────────────────────────
    # GAME OVER
    # ─────────────────────────────────────────────────────────────────────
    def _end_game(self):
        self._is_new_record = self.score > self.high_score
        if self._is_new_record: self.high_score = self.score
        self.sound.play("game_over")
        self.voice.say("victory")
        # BladeVerse: record player stats and push leaderboard
        try:
            if self.pm:
                self.pm.record_game(self.score, self._session_max_combo)
            # push to leaderboard
            self.lb_mgr.push_score(self.score, mode=self.game_mode)
            # sync player state to stub
            self.lb_mgr.sync_player()
        except Exception:
            pass
        self._save_score()
        self.goto(STATE_GAME_OVER)

    def _save_score(self):
        entry = {"name":"Player","score":self.score,
                 "mode":self.game_mode,"date":time.strftime("%Y-%m-%d")}
        self.leaderboard.append(entry)
        self.leaderboard.sort(key=lambda e:e["score"], reverse=True)
        self.leaderboard = self.leaderboard[:20]
        try:
            with open(LEADERBOARD_FILE,"w") as f: json.dump(self.leaderboard,f,indent=2)
        except Exception: pass

    def _load_leaderboard(self):
        if not os.path.isfile(LEADERBOARD_FILE): return []
        try:
            with open(LEADERBOARD_FILE) as f: return json.load(f)
        except Exception: return []

    # ─────────────────────────────────────────────────────────────────────
    # HUD STATE
    # ─────────────────────────────────────────────────────────────────────
    def hud_state(self, fps, gesture):
        powers = []
        if self._shield_timer       > 0: powers.append("shield")
        if self._double_score_timer > 0: powers.append("double_score")
        if self._slow_mo_timer      > 0: powers.append("slow_mo")
        if self._freeze_timer       > 0: powers.append("freeze")
        if self.blade_mode.mode == BLADE_FIRE: powers.append("fire_blade")
        if self.blade_mode.mode == BLADE_ICE:  powers.append("ice_blade")
        return {
            "score":               self.score,
            "high_score":          self.high_score,
            "lives":               self.lives,
            "combo":               self.combo,
            "game_mode":           self.game_mode,
            "time_left":           self._time_left if self.game_mode==MODE_TIME_ATTACK else None,
            "active_powers":       powers,
            "fps":                 fps,
            "double_score_active": self._double_score_timer > 0,
            "shield_active":       self._shield_timer > 0,
            "slow_mo_active":      self._slow_mo_timer > 0,
            "show_fps":            self.cfg.get("show_fps", True),
            "gesture":             gesture,
            "blade_mode":          self.blade_mode.mode,
            "boss_active":         self.boss_mgr.has_boss,
        }