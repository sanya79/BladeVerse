"""
sound_manager.py  (UPGRADED)
==============================
Sab sounds numpy se PROPERLY synthesize hote hain.
Har sound unique feel deta hai:
  slice     - whoosh + crack
  bomb      - deep rumble + explosion
  combo     - ascending musical chord
  power     - magical sparkle arpeggio
  miss      - sad descending tone
  shield    - metallic clank
  double    - triumphant fanfare
  game_over - dramatic ending phrase
  menu_tick - satisfying click
  excellent - voice-like exclamation tone
"""

import os, math
import numpy as np
import pygame
from settings import SOUNDS_DIR, SFX_VOLUME, MUSIC_VOLUME

SR = 44100   # sample rate

def _buf(duration, func, vol=0.5):
    """Build a mono float array, convert to int16 stereo pygame Sound."""
    n    = int(SR * duration)
    t    = np.linspace(0, duration, n, endpoint=False)
    data = func(t) * vol
    data = np.clip(data, -1, 1)
    data = (data * 32767).astype(np.int16)
    st   = np.column_stack([data, data])
    return pygame.sndarray.make_sound(st)

def _envelope(t, attack=0.01, decay=0.05, sustain=0.6, release=0.3):
    """ADSR envelope — returns array of multipliers same shape as t."""
    dur = t[-1] + 1e-9
    env = np.zeros_like(t)
    a_end = attack;  d_end = attack+decay;  s_end = dur-release
    env = np.where(t < a_end,   t/attack,                           env)
    env = np.where((t>=a_end) & (t<d_end), 1-(1-sustain)*(t-a_end)/decay, env)
    env = np.where((t>=d_end) & (t<s_end), sustain,                 env)
    env = np.where(t >= s_end,  sustain*(1-(t-s_end)/release),      env)
    return np.clip(env, 0, 1)

def _make_slice():
    """Swoosh + high-frequency crack — like a blade cutting air."""
    def f(t):
        dur = t[-1] + 1e-9
        # Swoosh: broadband noise with falling frequency emphasis
        noise  = np.random.uniform(-1, 1, len(t))
        sweep  = np.sin(2*np.pi * np.linspace(800, 200, len(t)) * t)
        env    = np.exp(-t * 18) * (1 - t/dur)
        # Crack: short transient at start
        crack  = np.random.uniform(-1, 1, len(t)) * np.exp(-t * 80)
        return (noise * 0.5 + sweep * 0.3 + crack * 0.8) * env
    return _buf(0.18, f, vol=0.6)

def _make_bomb():
    """Deep thud + rumble + high crackle."""
    def f(t):
        # Sub bass thud
        freq_sweep = np.linspace(90, 30, len(t))
        bass  = np.sin(2*np.pi * np.cumsum(freq_sweep) / SR)
        env_b = np.exp(-t * 5)
        # Mid crackle
        crack = np.random.uniform(-1, 1, len(t)) * np.exp(-t * 12) * 0.5
        # High snap at start
        snap  = np.random.uniform(-1, 1, len(t)) * np.exp(-t * 50) * 0.7
        return (bass * env_b * 0.7 + crack + snap)
    return _buf(0.6, f, vol=0.55)

def _make_combo():
    """Rising major chord arpeggio — C4 E4 G4 C5."""
    freqs  = [262, 330, 392, 523]
    delays = [0.0, 0.08, 0.16, 0.24]
    def f(t):
        out = np.zeros_like(t)
        for freq, delay in zip(freqs, delays):
            mask = t >= delay
            local_t = np.where(mask, t - delay, 0)
            tone = np.sin(2*np.pi*freq*local_t) + 0.3*np.sin(4*np.pi*freq*local_t)
            env  = np.exp(-local_t * 6) * mask
            out += tone * env * 0.35
        return out
    return _buf(0.55, f, vol=0.5)

def _make_power():
    """Magical sparkle: fast ascending arpeggio with shimmer."""
    freqs  = [440, 554, 659, 880, 1109, 1318]
    delays = [i * 0.055 for i in range(6)]
    def f(t):
        out = np.zeros_like(t)
        for freq, delay in zip(freqs, delays):
            mask    = t >= delay
            local_t = np.where(mask, t - delay, 0)
            # Main tone + shimmer overtone
            tone = (np.sin(2*np.pi*freq*local_t) +
                    0.4*np.sin(2*np.pi*freq*1.5*local_t) +
                    0.2*np.sin(2*np.pi*freq*2*local_t))
            env  = np.exp(-local_t * 8) * mask
            out += tone * env * 0.28
        return out
    return _buf(0.65, f, vol=0.5)

def _make_miss():
    """Sad descending minor tone."""
    def f(t):
        freq = np.linspace(440, 220, len(t))
        wave = np.sin(2*np.pi * np.cumsum(freq) / SR)
        env  = _envelope(t, attack=0.02, decay=0.1, sustain=0.4, release=0.25)
        # Add slight wobble
        wobble = 1 + 0.04 * np.sin(2*np.pi*6*t)
        return wave * env * wobble
    return _buf(0.5, f, vol=0.45)

def _make_tick():
    """Short satisfying click."""
    def f(t):
        click = np.random.uniform(-1,1,len(t)) * np.exp(-t * 120)
        tone  = np.sin(2*np.pi*1400*t) * np.exp(-t * 60)
        return click * 0.4 + tone * 0.6
    return _buf(0.06, f, vol=0.4)

def _make_game_over():
    """Dramatic descending chord — minor triad falling."""
    chord_sets = [(330,277,220), (277,233,185), (220,185,147)]
    delays     = [0.0, 0.35, 0.70]
    def f(t):
        out = np.zeros_like(t)
        for (f1,f2,f3), delay in zip(chord_sets, delays):
            mask    = t >= delay
            local_t = np.where(mask, t-delay, 0)
            wave = (np.sin(2*np.pi*f1*local_t) +
                    np.sin(2*np.pi*f2*local_t) +
                    np.sin(2*np.pi*f3*local_t)) / 3
            env  = _envelope(local_t, attack=0.02, decay=0.15, sustain=0.5, release=0.25) * mask
            out += wave * env * 0.45
        return out
    return _buf(1.4, f, vol=0.5)

def _make_shield():
    """Metallic CLANK — high ring + sub thud."""
    def f(t):
        # Metallic ring: inharmonic partials
        ring = (np.sin(2*np.pi*800*t)*np.exp(-t*8) +
                np.sin(2*np.pi*1250*t)*np.exp(-t*12) +
                np.sin(2*np.pi*2000*t)*np.exp(-t*20))
        # Sub thud
        thud = np.sin(2*np.pi*80*t) * np.exp(-t*15)
        return ring * 0.5 + thud * 0.5
    return _buf(0.35, f, vol=0.55)

def _make_double():
    """Triumphant fanfare — 4 stacked power chords."""
    def f(t):
        freqs = [262, 330, 392, 523, 659]
        out   = np.zeros_like(t)
        for i, freq in enumerate(freqs):
            delay   = i * 0.04
            mask    = t >= delay
            local_t = np.where(mask, t - delay, 0)
            wave = (np.sin(2*np.pi*freq*local_t) +
                    0.5*np.sin(2*np.pi*freq*2*local_t)) * mask
            env  = np.exp(-local_t * 4)
            out += wave * env * 0.22
        return out
    return _buf(0.6, f, vol=0.5)

def _make_excellent():
    """Voice-like exclamation: formant synthesis — ascending vowel."""
    def f(t):
        f0  = np.linspace(200, 350, len(t))           # pitch glide up
        src = np.sin(2*np.pi * np.cumsum(f0) / SR)    # source
        # Two formants to sound vowel-like
        f1_freq, f2_freq = 800, 1200
        filt1 = np.sin(2*np.pi*f1_freq*t) * np.exp(-t*5)
        filt2 = np.sin(2*np.pi*f2_freq*t) * np.exp(-t*8)
        env   = _envelope(t, attack=0.05, decay=0.1, sustain=0.6, release=0.15)
        return (src * 0.4 + filt1 * 0.35 + filt2 * 0.25) * env
    return _buf(0.45, f, vol=0.55)


class SoundManager:
    def __init__(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=SR, size=-16, channels=2, buffer=256)

        self._sfx_on   = True
        self._music_on = True
        os.makedirs(SOUNDS_DIR, exist_ok=True)

        # Map: name → (filename, generator)
        generators = {
            "slice"    : ("slice.ogg",     _make_slice),
            "bomb"     : ("bomb.ogg",      _make_bomb),
            "combo"    : ("combo.ogg",     _make_combo),
            "power"    : ("power.ogg",     _make_power),
            "miss"     : ("miss.ogg",      _make_miss),
            "menu_tick": ("menu_tick.ogg", _make_tick),
            "game_over": ("game_over.ogg", _make_game_over),
            "shield"   : ("shield.ogg",    _make_shield),
            "double"   : ("double.ogg",    _make_double),
            "excellent": ("excellent.ogg", _make_excellent),
        }

        self._sounds: dict[str, pygame.mixer.Sound] = {}
        for name, (fname, gen) in generators.items():
            path = os.path.join(SOUNDS_DIR, fname)
            try:
                if os.path.isfile(path):
                    s = pygame.mixer.Sound(path)
                else:
                    s = gen()
                s.set_volume(SFX_VOLUME)
                self._sounds[name] = s
            except Exception as e:
                print(f"[Sound] {name}: {e}")

    def play(self, name: str):
        if self._sfx_on:
            s = self._sounds.get(name)
            if s:
                s.play()

    def play_music(self, filename="bgm.ogg"):
        path = os.path.join(SOUNDS_DIR, filename)
        if os.path.isfile(path):
            try:
                pygame.mixer.music.load(path)
                pygame.mixer.music.set_volume(MUSIC_VOLUME)
                pygame.mixer.music.play(-1)
            except Exception as e:
                print(f"[Music] {e}")

    def stop_music(self):
        pygame.mixer.music.stop()

    def toggle_sfx(self):
        self._sfx_on = not self._sfx_on

    def toggle_music(self):
        self._music_on = not self._music_on
        if self._music_on: self.play_music()
        else: self.stop_music()

    @property
    def sfx_on(self):   return self._sfx_on
    @property
    def music_on(self): return self._music_on