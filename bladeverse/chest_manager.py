"""
chest_manager.py
-----------------
Chest opening logic and reward drop tables.
"""
import random
from typing import Dict, List

CHESTS = {
    'common': {
        'weight': 60,
        'drops': [
            ('coins', (50,150)), ('xp', (10,40)), ('gems', (0,0)),
            ('blade', None), ('trail', None), ('background', None)
        ]
    },
    'rare': {
        'weight': 25,
        'drops': [
            ('coins', (200,400)), ('xp', (50,120)), ('gems', (1,2)),
            ('blade', None), ('trail', None)
        ]
    },
    'epic': {
        'weight': 10,
        'drops': [
            ('coins', (500,900)), ('xp', (200,400)), ('gems', (3,6)), ('blade', None), ('trail', None)
        ]
    },
    'legendary': {
        'weight': 5,
        'drops': [
            ('coins', (1200,3000)), ('xp', (800,2000)), ('gems', (10,30)), ('blade', None), ('background', None)
        ]
    }
}

# simple sample item pools (should align with shop catalog keys)
BLADE_POOL = ['fire_blade','ice_blade','thunder_blade','shadow_blade','galaxy_blade']
TRAIL_POOL = ['neon_trail','flame_trail','lightning_trail','galaxy_trail']
BG_POOL = ['cyber_city','neon_tokyo','space_arena','volcano_realm','frozen_kingdom','digital_matrix']

class ChestManager:
    def __init__(self, player_manager, inventory_manager=None):
        self.pm = player_manager
        self.inv = inventory_manager

    def open_chest(self, chest_type: str) -> List[Dict]:
        """Opens a chest and returns list of rewards applied (and applied to player/inventory)."""
        ct = CHESTS.get(chest_type, CHESTS['common'])
        rewards = []
        # pick number of drops based on chest type
        drops_n = 2 if chest_type=='common' else (3 if chest_type=='rare' else (4 if chest_type=='epic' else 5))
        for _ in range(drops_n):
            kind = random.choice([d[0] for d in ct['drops']])
            if kind == 'coins':
                amount = random.randint(*ct['drops'][0][1])
                if self.pm: self.pm.add_coins(amount)
                rewards.append({'type':'coins','amount':amount})
            elif kind == 'xp':
                amount = random.randint(*[d[1] for d in ct['drops'] if d[0]=='xp'][0])
                if self.pm: self.pm.add_xp(amount)
                rewards.append({'type':'xp','amount':amount})
            elif kind == 'gems':
                rng = [d for d in ct['drops'] if d[0]=='gems'][0][1]
                amount = random.randint(rng[0], rng[1])
                if amount>0 and self.pm: self.pm.add_gems(amount)
                rewards.append({'type':'gems','amount':amount})
            elif kind == 'blade':
                item = random.choice(BLADE_POOL)
                if self.inv: self.inv.add_item('blades', item)
                rewards.append({'type':'blade','key':item})
            elif kind == 'trail':
                item = random.choice(TRAIL_POOL)
                if self.inv: self.inv.add_item('trails', item)
                rewards.append({'type':'trail','key':item})
            elif kind == 'background':
                item = random.choice(BG_POOL)
                if self.inv: self.inv.add_item('backgrounds', item)
                rewards.append({'type':'background','key':item})
        return rewards
 