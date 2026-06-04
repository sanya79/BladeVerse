"""
shop_manager.py
----------------
Handles shop catalog, prices, purchases and persistent ownership via InventoryManager.
"""
from typing import Dict, List
from .inventory_manager import InventoryManager

CATALOG = {
    'blades': [
        {'key':'fire_blade','name':'Fire Blade','coins':500,'gems':0},
        {'key':'ice_blade','name':'Ice Blade','coins':700,'gems':0},
        {'key':'thunder_blade','name':'Thunder Blade','coins':1200,'gems':1},
        {'key':'shadow_blade','name':'Shadow Blade','coins':2000,'gems':3},
        {'key':'galaxy_blade','name':'Galaxy Blade','coins':5000,'gems':10},
    ],
    'trails': [
        {'key':'neon_trail','name':'Neon Trail','coins':200,'gems':0},
        {'key':'flame_trail','name':'Flame Trail','coins':400,'gems':0},
        {'key':'lightning_trail','name':'Lightning Trail','coins':800,'gems':1},
        {'key':'galaxy_trail','name':'Galaxy Trail','coins':1500,'gems':2},
    ],
    'backgrounds': [
        {'key':'cyber_city','name':'Cyber City','coins':800,'gems':0},
        {'key':'neon_tokyo','name':'Neon Tokyo','coins':900,'gems':0},
        {'key':'space_arena','name':'Space Arena','coins':1500,'gems':2},
        {'key':'volcano_realm','name':'Volcano Realm','coins':2000,'gems':3},
        {'key':'frozen_kingdom','name':'Frozen Kingdom','coins':1800,'gems':2},
        {'key':'digital_matrix','name':'Digital Matrix','coins':2500,'gems':5},
    ]
}

class ShopManager:
    def __init__(self, player_manager, inventory: InventoryManager = None):
        self.pm = player_manager
        self.inv = inventory or InventoryManager()

    def get_catalog(self, category: str) -> List[Dict]:
        return CATALOG.get(category, [])

    def can_afford(self, coins:int, gems:int) -> bool:
        if not self.pm or not self.pm.player: return False
        return (self.pm.player.coins >= coins) and (self.pm.player.gems >= gems)

    def purchase(self, category: str, item_key: str) -> bool:
        items = self.get_catalog(category)
        item = next((i for i in items if i['key']==item_key), None)
        if not item: return False
        if not self.can_afford(item['coins'], item['gems']):
            return False
        # deduct
        self.pm.add_coins(-abs(item['coins']))
        if item['gems']:
            self.pm.add_gems(-abs(item['gems']))
        # grant ownership
        self.inv.add_item(category, item_key)
        return True

    def equip(self, slot: str, item_key: str) -> bool:
        return self.inv.equip(slot, item_key)

    def get_owned(self):
        return self.inv.get_owned()

    def get_equipped(self):
        return self.inv.get_equipped()
 