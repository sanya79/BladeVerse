"""
achievements.py
---------------
Manage achievement definitions and evaluation.
"""
from typing import List, Dict

ACHIEVEMENTS = {
    "first_slice": {"title":"First Slice", "desc":"Slice your first fruit"},
    "score_100": {"title":"Score 100", "desc":"Reach 100 points"},
    "score_500": {"title":"Score 500", "desc":"Reach 500 points"},
    "score_1000": {"title":"Score 1000", "desc":"Reach 1000 points"},
    "combo_master": {"title":"Combo Master", "desc":"Achieve a 10x combo"},
    "boss_slayer": {"title":"Boss Slayer", "desc":"Defeat a boss"},
    "fruit_destroyer": {"title":"Fruit Destroyer", "desc":"Slice 500 fruits"},
    "speed_demon": {"title":"Speed Demon", "desc":"Perform a fast swipe"},
    "legendary_ninja": {"title":"Legendary Ninja", "desc":"Reach level 50"},
}

class AchievementsManager:
    def __init__(self, player_manager, notifier=None):
        self.pm = player_manager
        self.notifier = notifier  # function(title, message)

    def _unlock(self, key: str) -> bool:
        if not self.pm: return False
        unlocked = self.pm.unlock_achievement(key)
        if unlocked and self.notifier:
            info = ACHIEVEMENTS.get(key, {})
            self.notifier(info.get('title', 'Achievement'), info.get('desc', 'Unlocked'))
        return unlocked

    def evaluate_on_slice(self, total_slices: int, score: int, combo: int, fast_swipe: bool):
        unlocked = []
        if total_slices >= 1:
            if self._unlock('first_slice'): unlocked.append('first_slice')
        if score >= 100:
            if self._unlock('score_100'): unlocked.append('score_100')
        if score >= 500:
            if self._unlock('score_500'): unlocked.append('score_500')
        if score >= 1000:
            if self._unlock('score_1000'): unlocked.append('score_1000')
        if combo >= 10:
            if self._unlock('combo_master'): unlocked.append('combo_master')
        if fast_swipe:
            if self._unlock('speed_demon'): unlocked.append('speed_demon')
        if total_slices >= 500:
            if self._unlock('fruit_destroyer'): unlocked.append('fruit_destroyer')
        return unlocked

    def evaluate_on_boss_defeat(self):
        if self._unlock('boss_slayer'):
            return ['boss_slayer']
        return []

    def evaluate_on_level(self, level: int):
        if level >= 50:
            if self._unlock('legendary_ninja'):
                return ['legendary_ninja']
        return []
 