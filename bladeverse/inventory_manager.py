"""
inventory_manager.py
--------------------
Stores owned items and equipped selections in a local JSON file.
"""
import json
import os
from typing import Dict, Any

PATH = os.path.join(os.path.dirname(__file__), '..', 'saves', 'inventory.json')
os.makedirs(os.path.dirname(PATH), exist_ok=True)

DEFAULT = {
    'owned': {
        'blades': ['default'],
        'trails': ['default'],
        'backgrounds': ['default']
    },
    'equipped': {
        'blade': 'default',
        'trail': 'default',
        'background': 'default'
    }
}

class InventoryManager:
    def __init__(self, path: str = PATH):
        self.path = path
        self.data = DEFAULT.copy()
        self._load()

    def _load(self):
        try:
            if os.path.exists(self.path):
                with open(self.path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            else:
                self._save()
        except Exception:
            self.data = DEFAULT.copy(); self._save()

    def _save(self):
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2)

    def is_owned(self, category: str, key: str) -> bool:
        return key in self.data['owned'].get(category, [])

    def add_item(self, category: str, key: str) -> None:
        owned = self.data['owned'].setdefault(category, [])
        if key not in owned:
            owned.append(key); self._save()

    def equip(self, slot: str, key: str) -> bool:
        # slot: blade/trail/background
        cat = 'blades' if slot=='blade' else ('trails' if slot=='trail' else 'backgrounds')
        if not self.is_owned(cat, key):
            return False
        self.data['equipped'][slot] = key; self._save(); return True

    def get_equipped(self) -> Dict[str, str]:
        return self.data.get('equipped', {}).copy()

    def get_owned(self) -> Dict[str, list]:
        return {k:list(v) for k,v in self.data.get('owned',{}).items()}
