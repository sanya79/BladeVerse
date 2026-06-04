"""
rewards.py
----------
Grant coin/gem/xp rewards for events.
"""
from typing import Callable, Dict

class RewardManager:
    def __init__(self, player_manager, notifier: Callable[[str,str],None]=None):
        self.pm = player_manager
        self.notifier = notifier

    def grant_for_achievement(self, ach_key: str) -> Dict:
        # simple reward map
        rewards = {
            'first_slice': {'coins':10, 'gems':0, 'xp':5},
            'score_100':   {'coins':20, 'gems':0, 'xp':10},
            'score_500':   {'coins':50, 'gems':1, 'xp':40},
            'score_1000':  {'coins':150,'gems':2, 'xp':120},
            'combo_master':{'coins':80, 'gems':1, 'xp':60},
            'boss_slayer': {'coins':300,'gems':5, 'xp':350},
            'fruit_destroyer':{'coins':500,'gems':5,'xp':500},
            'speed_demon': {'coins':30, 'gems':0, 'xp':20},
            'legendary_ninja':{'coins':2000,'gems':50,'xp':5000},
        }
        r = rewards.get(ach_key, {'coins':0,'gems':0,'xp':0})
        # apply to player
        if self.pm:
            if r.get('coins',0): self.pm.add_coins(r['coins'])
            if r.get('gems',0): self.pm.add_gems(r['gems'])
            if r.get('xp',0): self.pm.add_xp(r['xp'])
        if self.notifier:
            self.notifier('Reward Earned', f"+{r.get('coins',0)} coins, +{r.get('gems',0)} gems, +{r.get('xp',0)} XP")
        return r

    def grant_levelup(self, old_level:int, new_level:int) -> Dict:
        # simple levelup reward: coins scaled
        coins = 50 * (new_level - old_level)
        xp = 0
        gems = 0
        if self.pm:
            self.pm.add_coins(coins)
        if self.notifier:
            self.notifier('Level Up!', f'Level {new_level} — +{coins} coins')
        return {'coins':coins,'gems':gems,'xp':xp}

    def grant_for_boss(self) -> Dict:
        r = {'coins':200,'gems':3,'xp':200}
        if self.pm:
            self.pm.add_coins(r['coins']); self.pm.add_gems(r['gems']); self.pm.add_xp(r['xp'])
        if self.notifier:
            self.notifier('Boss Reward', f"+{r['coins']} coins, +{r['gems']} gems, +{r['xp']} XP")
        return r

    def daily_login(self) -> Dict:
        r = {'coins':10,'gems':0,'xp':5}
        if self.pm:
            self.pm.add_coins(r['coins']); self.pm.add_xp(r['xp'])
        if self.notifier:
            self.notifier('Daily Login', f"+{r['coins']} coins, +{r['xp']} XP")
        return r
 