"""
firebase_stub.py
-----------------
Lightweight placeholder for Firebase integration. Replace with actual
`firebase_admin` or client SDK usage when a Firebase project is available.

This stub exposes the minimal interface used by the upgrade plan:
- init(config)
- sign_in_anonymously()
- save_player(player_dict)
- get_leaderboard(category="global", limit=50)

The functions currently operate against local JSON files for offline testing.
"""
import os
import json
from typing import Dict, List

LOCAL_DB = os.path.join(os.path.dirname(__file__), '..', 'saves', 'firebase_local.json')
os.makedirs(os.path.dirname(LOCAL_DB), exist_ok=True)

class FirebaseClient:
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self._db = {}
        self._load_local()

    def _load_local(self):
        if os.path.exists(LOCAL_DB):
            try:
                with open(LOCAL_DB, 'r', encoding='utf-8') as f:
                    self._db = json.load(f)
            except Exception:
                self._db = {}
        else:
            self._db = {"players": [], "leaderboard": []}

    def _save_local(self):
        with open(LOCAL_DB, 'w', encoding='utf-8') as f:
            json.dump(self._db, f, indent=2)

    def init(self, config: Dict):
        self.config = config
        self._load_local()

    def sign_in_anonymously(self) -> str:
        # Return a fake UID
        return "anon_" + os.urandom(4).hex()

    def save_player(self, player: Dict) -> None:
        # Upsert by username
        players = self._db.setdefault('players', [])
        for i, p in enumerate(players):
            if p.get('username') == player.get('username'):
                players[i] = player
                self._save_local()
                return
        players.append(player)
        self._save_local()

    def get_leaderboard(self, category: str = 'global', limit: int = 50) -> List[Dict]:
        lb = self._db.get('leaderboard', [])
        # For offline stub, sort by score if present
        lb_sorted = sorted(lb, key=lambda x: x.get('score', 0), reverse=True)
        return lb_sorted[:limit]

    def push_score(self, username: str, score: int, metadata: Dict = None):
        lb = self._db.setdefault('leaderboard', [])
        lb.append({"username": username, "score": int(score), "meta": metadata or {}})
        self._save_local()


if __name__ == '__main__':
    fb = FirebaseClient()
    fb.save_player({'username':'Test','highestScore':123})
    fb.push_score('Test', 123)
    print('Players:', fb._db.get('players'))
    print('Leaderboard:', fb.get_leaderboard())
