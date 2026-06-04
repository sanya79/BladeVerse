"""
main.py  (FULL UPGRADE)
=======================
Full cinematic game loop with:
  • DynamicBackground (score-reactive, 5 themes)
  • ZoomController   (smooth zoom in/out)
  • MotionBlurOverlay(slow-mo blur)
  • CinematicBars    (letterbox)
  • BossManager      (boss fruits)
  • BladeModeManager (fire / ice)
  • ShockwaveBlast / SlashArc / SpeedLines / ImpactFlash
  • VoiceReactor     (optional TTS)
  • ComboAnimator    (big combo text)
  • HandCursor       (glowing fingertip + gesture badge)
"""

import sys, os, cv2, pygame
import numpy as np

from settings import (SAVES_DIR, SCREEN_W, SCREEN_H, TARGET_FPS, FULLSCREEN)
os.makedirs(SAVES_DIR, exist_ok=True)

import settings as S
from hand_tracking  import HandTracker
from effects        import (BladeTrail, ParticleSystem, ComboPopup,
                             ScreenShake, HitFlash, BackgroundRenderer, HandCursor)
from sound_manager  import SoundManager
from game_manager   import (GameManager,
                             STATE_MENU, STATE_MODE_SEL, STATE_PLAYING,
                             STATE_PAUSED, STATE_GAME_OVER,
                             STATE_LEADERBOARD, STATE_SETTINGS)
from ui import (FontCache, HUD, MainMenu, ModeSelectScreen, PauseOverlay,
                GameOverScreen, LeaderboardScreen, SettingsScreen, ProfileScreen, ShopScreen)
from bladeverse.player import PlayerManager
from bladeverse.inventory_manager import InventoryManager
from bladeverse.shop_manager import ShopManager
from bladeverse.chest_manager import ChestManager


def init_pygame(fullscreen=FULLSCREEN):
    pygame.init()
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    flags = (pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
             if fullscreen else pygame.HWSURFACE | pygame.DOUBLEBUF)
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), flags)
    pygame.display.set_caption(S.WINDOW_TITLE)
    FontCache.init()
    return screen


def blit_webcam(surface, frame_bgr, alpha=40, scale=0.25):
    if frame_bgr is None: return
    h, w = frame_bgr.shape[:2]
    nw, nh = int(w*scale), int(h*scale)
    small  = cv2.resize(frame_bgr, (nw, nh))
    rgb    = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
    pg_s   = pygame.surfarray.make_surface(np.rot90(rgb))
    pg_s.set_alpha(alpha)
    # Rounded-corner mask
    surface.blit(pg_s, (SCREEN_W - nw - 10, SCREEN_H - nh - 10))
    # Border glow
    pygame.draw.rect(surface, (0, 180, 255),
                     (SCREEN_W-nw-11, SCREEN_H-nh-11, nw+2, nh+2), 1)


def main():
    screen = init_pygame()
    clock  = pygame.time.Clock()

    # ── Subsystems ───────────────────────────────────────────────────────
    tracker   = HandTracker()
    sound     = SoundManager()
    sound.play_music()

    # Player profile manager (local persistence)
    pm = PlayerManager()


    particles = ParticleSystem()
    trail     = BladeTrail()
    shake     = ScreenShake()
    flash     = HitFlash()
    bg        = BackgroundRenderer(S.DEFAULT_THEME)
    hud_ui    = HUD()
    hand_cur  = HandCursor()

    # ── Screens ──────────────────────────────────────────────────────────
    main_menu   = MainMenu()
    mode_sel    = ModeSelectScreen()
    pause_ov    = PauseOverlay()
    gameover_sc = GameOverScreen()
    lb_scr      = LeaderboardScreen()
    settings_sc = SettingsScreen()
    profile_sc  = ProfileScreen()
    profile_sc.load_player(pm.player)
    # Shop + inventory
    inv_mgr = InventoryManager()
    shop_mgr = ShopManager(pm, inv_mgr)
    chest_mgr = ChestManager(pm, inv_mgr)
    shop_sc = ShopScreen(shop_mgr, inv_mgr, pm, chest_mgr, sound)

    # ── Game manager (now owns all new systems) ──────────────────────────
    gm = GameManager(sound, particles, trail, shake, flash, bg, hud_ui)

    popups: list[ComboPopup] = []

    # Two surfaces: game_surf (pre-shake), screen
    game_surf = pygame.Surface((SCREEN_W, SCREEN_H))

    running = True
    show_profile = False
    show_shop = False
    while running:
        clock.tick(TARGET_FPS)
        fps   = clock.get_fps()
        mouse = pygame.mouse.get_pos()

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if gm.state == STATE_PLAYING:
                        gm.goto(STATE_PAUSED)
                    elif gm.state == STATE_PAUSED:
                        gm.goto(STATE_PLAYING)
                    elif gm.state == STATE_MENU:
                        running = False
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                if event.key == pygame.K_F3:
                    gm.cfg["show_fps"] = not gm.cfg.get("show_fps", True)
                if event.key == pygame.K_F4:
                    S.DEBUG_MODE = not S.DEBUG_MODE; gm.cfg["debug"] = S.DEBUG_MODE
                # Quick blade mode test keys (for demos)
                if event.key == pygame.K_1 and gm.state == STATE_PLAYING:
                    gm.blade_mode.activate_fire()
                if event.key == pygame.K_2 and gm.state == STATE_PLAYING:
                    gm.blade_mode.activate_ice()
                if event.key == pygame.K_3 and gm.state == STATE_PLAYING:
                    gm.blade_mode.deactivate()

        # ── Webcam / hand tracking ────────────────────────────────────────
        tracker.update()
        tip_pos     = tracker.tip_pos
        gesture     = tracker.gesture
        swipe_speed = tracker.swipe_speed

        # ── Clear render surface ─────────────────────────────────────────
        game_surf.fill(S.BLACK)

        # ── Dynamic Background (playing) or static BG (menus) ───────────
        if gm.state == STATE_PLAYING:
            gm.dyn_bg.draw(game_surf)
        else:
            bg.draw(game_surf)

        # ── Motion blur capture (before drawing objects) ─────────────────
        if gm.state == STATE_PLAYING and gm.slow_mo_ctrl.active:
            gm.blur.set_active(True)
            gm.blur.apply(game_surf)
        else:
            gm.blur.set_active(False)

        # ═══════════════════════════════════════════════════════════════
        # STATE ROUTING
        # ═══════════════════════════════════════════════════════════════

        if gm.state == STATE_MENU:
            action = main_menu.update(events, mouse)
            main_menu.draw(game_surf)
            if action == "play":
                # require profile
                if not pm.player or pm.player.username in (None, "", "Player"):
                    show_profile = True
                    profile_sc.load_player(pm.player)
                else:
                    gm.goto(STATE_MODE_SEL);    sound.play("menu_tick")
            elif action == "profile":
                show_profile = True
                profile_sc.load_player(pm.player)
            elif action == "shop":
                show_shop = True
                shop_sc.selected = None
            elif action == "leaderboard":
                gm.goto(STATE_LEADERBOARD); sound.play("menu_tick")
            elif action == "settings":
                gm._prev_state=STATE_MENU; gm.goto(STATE_SETTINGS); sound.play("menu_tick")
            elif action == "quit":
                running = False

            # Profile overlay handling
            if show_profile:
                prof_action = profile_sc.update(events, mouse, pm)
                profile_sc.draw(game_surf, pm.player)
                if prof_action == "saved":
                    show_profile = False
                    profile_sc.message = "Saved"
                    sound.play("menu_tick")
                    # after saving, proceed to mode select
                    gm.goto(STATE_MODE_SEL)
                elif prof_action == "back":
                    show_profile = False
            # Shop overlay handling
            if show_shop:
                shop_action = shop_sc.update(events, mouse)
                shop_sc.draw(game_surf)
                # if chest opened, create popups for rewards
                if getattr(shop_sc, 'last_chest_rewards', None):
                    rews = shop_sc.last_chest_rewards
                    for r in rews:
                        popups.append(ComboPopup(str(r), SCREEN_W//2, 180, color=(200,200,60)))
                    shop_sc.last_chest_rewards = None
                # if purchase/equip happened, show result
                if getattr(shop_sc, 'last_purchase_result', None):
                    res = shop_sc.last_purchase_result
                    txt = 'Purchased' if res.get('ok') else 'Failed'
                    popups.append(ComboPopup(f"{txt}: {res.get('item')}", SCREEN_W//2, 200, color=(200,220,100)))
                    shop_sc.last_purchase_result = None
                if shop_action == 'back':
                    show_shop = False

        elif gm.state == STATE_MODE_SEL:
            action = mode_sel.update(events, mouse)
            mode_sel.draw(game_surf)
            if action and action != "back":
                gm.start_game(mode=action); sound.play("menu_tick")
            elif action == "back":
                gm.goto(STATE_MENU)

        elif gm.state == STATE_PLAYING:
            # Update logic
            gm.update_playing(tip_pos, gesture, swipe_speed, popups, fps)

            # Draw fruits / bombs
            for obj in gm.objects:
                obj.draw(game_surf)

            # Particles
            particles.draw(game_surf)

            # Blade trail
            trail.add_point(tip_pos)
            trail.draw(game_surf)

            # All new cinematic effects
            gm.draw_effects(game_surf)

            # Hand cursor
            hand_cur.draw(game_surf, tip_pos, gesture, swipe_speed)
            # Blade mode particles at tip
            if tip_pos:
                gm.blade_mode.draw(game_surf, tip_pos)

            # Webcam preview
            blit_webcam(game_surf, tracker.raw_frame)

            # HUD
            hud_ui.draw(game_surf, gm.hud_state(fps, gesture))

            # Popups
            popups = [p for p in popups if p.alive]
            for p in popups:
                p.update(); p.draw(game_surf)

            # Flash
            flash.draw(game_surf)

            # Capture for next-frame blur
            gm.blur.capture(game_surf)

        elif gm.state == STATE_PAUSED:
            for obj in gm.objects: obj.draw(game_surf)
            particles.draw(game_surf)
            action = pause_ov.update(events, mouse)
            pause_ov.draw(game_surf)
            if action == "resume":    gm.goto(STATE_PLAYING);  sound.play("menu_tick")
            elif action == "settings":gm._prev_state=STATE_PAUSED; gm.goto(STATE_SETTINGS)
            elif action == "menu":    gm.goto(STATE_MENU)

        elif gm.state == STATE_GAME_OVER:
            action = gameover_sc.update(events, mouse)
            gameover_sc.draw(game_surf, gm.score, gm.high_score,
                             gm._is_new_record, gm.game_mode)
            if action == "replay":
                gm.start_game(gm.game_mode); popups.clear(); sound.play("menu_tick")
            elif action == "menu":
                gm.goto(STATE_MENU); popups.clear()

        elif gm.state == STATE_LEADERBOARD:
            action = lb_scr.update(events, mouse)
            lb_scr.draw(game_surf, gm.leaderboard)
            if action == "back": gm.goto(STATE_MENU)

        elif gm.state == STATE_SETTINGS:
            action = settings_sc.update(events, mouse)
            settings_sc.draw(game_surf, gm.cfg)
            if action:
                _handle_settings(action, gm, sound, bg, screen)
                if action in ("toggle_back", "back"):
                    gm.goto(gm._prev_state or STATE_MENU)

        # ── Zoom + shake composite ───────────────────────────────────────
        gm.zoom.update()
        scaled, zoom_off = gm.zoom.apply(game_surf)
        ox, oy = shake.offset
        screen.fill(S.BLACK)
        screen.blit(scaled, (zoom_off[0]+ox, zoom_off[1]+oy))

        # ── Boss incoming HUD alert ──────────────────────────────────────
        if gm.state == STATE_PLAYING and gm.boss_mgr.has_boss:
            _draw_boss_alert(screen)

        pygame.display.flip()

    tracker.release()
    pygame.quit()
    sys.exit(0)


def _draw_boss_alert(surface):
    import math
    tick = pygame.time.get_ticks() // 16
    a    = int(150 + 100*abs(math.sin(tick*0.1)))
    try:
        font = pygame.font.SysFont("Consolas", 18, bold=True)
        t    = font.render("⚠ BOSS INCOMING ⚠", True, (255, 40, 80))
        t.set_alpha(a)
        surface.blit(t, (SCREEN_W//2 - t.get_width()//2, 14))
    except Exception:
        pass


def _handle_settings(action, gm, sound, bg, screen):
    cfg = gm.cfg
    if action == "toggle_sfx":     cfg["sfx_on"]    = not cfg.get("sfx_on",True);    sound.toggle_sfx()
    elif action=="toggle_music":   cfg["music_on"]  = not cfg.get("music_on",True);  sound.toggle_music()
    elif action=="toggle_debug":   cfg["debug"]     = not cfg.get("debug",False);    S.DEBUG_MODE=cfg["debug"]
    elif action=="toggle_fps":     cfg["show_fps"]  = not cfg.get("show_fps",True)
    elif action=="toggle_theme_c": cfg["theme"]=S.THEME_CYBERPUNK; bg.set_theme(S.THEME_CYBERPUNK)
    elif action=="toggle_theme_d": cfg["theme"]=S.THEME_DOJO;      bg.set_theme(S.THEME_DOJO)
    elif action=="toggle_theme_s": cfg["theme"]=S.THEME_SPACE;     bg.set_theme(S.THEME_SPACE)
    elif action=="toggle_fs":      cfg["fullscreen"]=not cfg.get("fullscreen",False); pygame.display.toggle_fullscreen()


if __name__ == "__main__":
    main()