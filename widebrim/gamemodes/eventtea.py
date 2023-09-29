from ..engine.state.layer import ScreenLayerNonBlocking
from ..engine.state.enum_mode import GAMEMODES

# TODO - Set tea as completed to prevent room allowing spawning it again

class EventTeaPlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState, screenController):
        ScreenLayerNonBlocking.__init__(self)
        laytonState.setGameMode(laytonState.getGameModeNext())

        baseEventId = laytonState.entryEvInfo
        if baseEventId != None:
            # 0 - Base tea event
            # 1 - Tea solved event
            # 2 - Tea failed event
            # 3 - Tea quit event
            # 4 - Tea retry event (event viewed flag)

            # Bypass tea event by setting ID to solved event, then spawning event handler (which game does in overlay 2)
            baseEventId = baseEventId.idEvent + 1
            laytonState.setEventId(baseEventId)

        self._canBeKilled = True