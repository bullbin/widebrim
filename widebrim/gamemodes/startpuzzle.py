from . import EventPlayer
from ..engine.state.enum_mode import GAMEMODES

# Overlay_StartPuzzle
class StartPuzzlePlayer(EventPlayer):
    def __init__(self, laytonState, screenController):
        laytonState.setGameModeNext(GAMEMODES.Room)
        EventPlayer.__init__(self, laytonState, screenController)
    
    def doOnKill(self):
        super().doOnKill()
        self.laytonState.setGameMode(GAMEMODES.Puzzle)