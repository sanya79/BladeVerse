"""
xp.py
-----
XP manager: awards XP, computes level thresholds, emits level-up events.
"""
from typing import Callable

class XPManager:
    def __init__(self, player_manager, on_level_up: Callable[[int,int], None] = None):
        self.pm = player_manager
        self.on_level_up = on_level_up
        # Precompute XP table for 50 levels
        self.level_table = [0]
        xp = 50
        for i in range(1, 51):
            self.level_table.append(int(xp))
            xp = xp * 1.6

    def xp_for_level(self, level: int) -> int:
        if level < len(self.level_table):
            return self.level_table[level]
        # fallback growth
        return int(self.level_table[-1] * (1.6 ** (level - len(self.level_table) + 1)))

    def add_xp(self, amount: int) -> dict:
        """Add XP to player; returns dict with keys: leveled (bool), old_level, new_level, xp, xp_next"""
        if not self.pm or not self.pm.player:
            return {"leveled": False}
        old_level = self.pm.player.level
        self.pm.player.xp += int(amount)
        # check level up
        leveled = False
        while self.pm.player.xp >= self.xp_for_level(self.pm.player.level + 1):
            self.pm.player.level += 1
            leveled = True
        self.pm.save()
        if leveled and self.on_level_up:
            self.on_level_up(old_level, self.pm.player.level)
        return {
            "leveled": leveled,
            "old_level": old_level,
            "new_level": self.pm.player.level,
            "xp": self.pm.player.xp,
            "xp_next": self.xp_for_level(self.pm.player.level + 1)
        }
 