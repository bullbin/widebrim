from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine.state.enum_mode import GAMEMODES

# WFC support for widebrim is not planned so download mode is not required

class WiFiDownloadPuzzleBypassPlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState, screenController):
        ScreenLayerNonBlocking.__init__(self)
        laytonState.setGameMode(GAMEMODES.WiFiSecretMenu)
        self._canBeKilled = True