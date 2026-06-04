"""
player.py
---------
Player data model and local persistence manager.

This is an incremental Python implementation to provide profile create/edit/load/save
functionality using a local JSON file. Later this will be extended to sync with
Firebase via `firebase_stub.py`.
"""
from dataclasses import dataclass, asdict, field
import json
import os
from typing import List, Dict

SAVES_DIR = os.path.join(os.path.dirname(__file__), '..', 'saves')
PLAYER_FILE = os.path.join(SAVES_DIR, 'player_profile.json')

os.makedirs(SAVES_DIR, exist_ok=True)

@dataclass
class Player:
    username: str = "Player"
    avatar: str = "default"
    country: str = "Unknown"
    highestScore: int = 0
    totalFruitsSliced: int = 0
    gamesPlayed: int = 0
    level: int = 1
    xp: int = 0
    achievements: List[str] = field(default_factory=list)
    unlockedRewards: List[str] = field(default_factory=list)
    coins: int = 0
    gems: int = 0
    rank: str = "Rookie"

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict):
        return cls(**{k: d.get(k) for k in cls.__annotations__.keys()})


class PlayerManager:
    """Manages loading/saving player profile locally and simple CRUD operations."""

    def __init__(self, path: str = PLAYER_FILE):
        self.path = os.path.abspath(path)
        self.player: Player | None = None
        self.load()

    def load(self) -> Player:
        if os.path.exists(self.path):
            try:
                with open(self.path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.player = Player.from_dict(data)
                return self.player
            except Exception:
                pass
        # Return default player if no save
        self.player = Player()
        return self.player

    def save(self) -> None:
        if self.player is None:
            return
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, 'w', encoding='utf-8') as f:
            json.dump(self.player.to_dict(), f, indent=2)

    def create_profile(self, username: str, avatar: str, country: str) -> Player:
        self.player = Player(username=username, avatar=avatar, country=country)
        self.save()
        return self.player

    def edit_profile(self, **kwargs) -> Player:
        if self.player is None:
            self.player = Player()
        for k, v in kwargs.items():
            if hasattr(self.player, k):
                setattr(self.player, k, v)
        self.save()
        return self.player

    def add_xp(self, amount: int) -> None:
        if self.player is None:
            return
        self.player.xp += int(amount)
        # Example level up threshold: simple curve; real table later
        while self.player.xp >= self._xp_for_level(self.player.level + 1):
            self.player.level += 1
        self.save()

    def _xp_for_level(self, lvl: int) -> int:
        # Simple exponential-ish curve; replace with 50,120,250,... table later
        return int(50 * (1.6 ** (lvl - 1)))

    # Additional helper methods for game integration
    def record_slices(self, count: int) -> None:
        if self.player is None: return
        self.player.totalFruitsSliced += int(count)
        self.save()

    def record_game(self, score: int, highest_combo: int) -> None:
        if self.player is None: return
        self.player.gamesPlayed += 1
        if score > self.player.highestScore:
            self.player.highestScore = int(score)
        # track highest combo in achievements via achievements manager
        self.save()

    def unlock_achievement(self, name: str) -> bool:
        if self.player is None: return False
        if name in self.player.achievements: return False
        self.player.achievements.append(name)
        self.save()
        return True

    def add_coins(self, amount: int) -> None:
        if self.player is None: return
        self.player.coins += int(amount)
        self.save()

    def add_gems(self, amount: int) -> None:
        if self.player is None: return
        self.player.gems += int(amount)
        self.save()


# Quick test runner when executed directly
if __name__ == '__main__':
    pm = PlayerManager()
    print('Loaded player:', pm.player)
    if pm.player.username == 'Player':
        pm.create_profile('Ninja', 'neon', 'Japan')
        print('Created profile:', pm.player)
