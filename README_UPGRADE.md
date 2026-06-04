BladeVerse Upgrade Notes
========================

What I added
- `bladeverse/` package with:
  - `player.py` — Player model + local JSON persistence and XP handling
  - `firebase_stub.py` — Local stub for Firebase (players + leaderboard)
  - `__init__.py` — exports

Why
- We're doing an incremental upgrade keeping the existing Pygame app.
- These modules let us add the required player/profile and leaderboard
  features and iterate without a full web rewrite.

Next steps (I'll implement next)
1. Integrate `bladeverse.PlayerManager` into the main menu flow so a profile
   is created/edited before starting a game.
2. Add UI screens for profile create/edit using the existing `ui.py` system.
3. Hook `GameManager` to award XP/coins and call `PlayerManager.add_xp()`.
4. Implement achievements and rewards stubs, and connect to `firebase_stub`
   for optional online sync.
5. Profile/avatar picker and country selector UI.

Firebase
- `bladeverse/firebase_stub.py` emulates minimal Firestore behavior for offline
  development. When you have a Firebase project, we'll replace the stub with
  real SDK calls and add secure auth.

To run quick local test:

```powershell
python -c "from bladeverse.player import PlayerManager; pm=PlayerManager(); print(pm.player)"
```
