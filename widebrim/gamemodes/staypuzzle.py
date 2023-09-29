from . import EventPlayer
from ..engine.state.enum_mode import GAMEMODES

# Overlay_StayPuzzle
class StayPuzzlePlayer(EventPlayer):
    def __init__(self, laytonState, screenController):
        EventPlayer.__init__(self, laytonState, screenController)