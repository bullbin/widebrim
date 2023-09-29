# TODO - Gamemode class, this is out of hand lmao

from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine.state.enum_mode import GAMEMODES
from widebrim.madhatter.common import logSevere

# widebrim has no intention of supporting Nintendo WiFi Connection emulation
# Packets could potentially be repeated in future as a cheaper alternative,
# but since the service has ended, puzzles unlocked by the service will never change
# This mode is therefore skipped altogether

class NintendoWfcBypassPlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState, screenController):
        ScreenLayerNonBlocking.__init__(self)
        logSevere("WFC service not implemented!", name="WfcMissing")
        laytonState.setGameMode(GAMEMODES.WiFiSecretMenu)
        self._canBeKilled = True