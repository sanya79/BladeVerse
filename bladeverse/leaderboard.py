"""
leaderboard.py
--------------
Simple leaderboard integration using the local Firebase stub.
"""
from bladeverse.firebase_stub import FirebaseClient

class LeaderboardManager:
    def __init__(self, firebase_client: FirebaseClient = None, player_manager=None):
        self.fb = firebase_client or FirebaseClient()
        self.pm = player_manager

    def push_score(self, score:int, mode:str=None):
        if self.pm and self.pm.player:
            username = self.pm.player.username
        else:
            username = 'Player'
        self.fb.push_score(username, int(score), {'mode':mode})

    def sync_player(self):
        if not self.pm or not self.pm.player: return
        self.fb.save_player(self.pm.player.to_dict())

    def get_top(self, category='global', limit=50):
        return self.fb.get_leaderboard(category, limit)
 