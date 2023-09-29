from . import EventPlayer
from ..engine.state.enum_mode import GAMEMODES

# Overlay_EndPuzzle
class EndPuzzlePlayer(EventPlayer):
    def __init__(self, laytonState, screenController):

        self.laytonState = laytonState
        self.laytonState.setGameModeNext(GAMEMODES.Room)

        baseEventId = laytonState.entryEvInfo
        if baseEventId != None:
            wasSkipped = self.laytonState.wasPuzzleSkipped
            if self.laytonState.getCurrentNazoListEntry() != None:
                puzzleState = self.laytonState.saveSlot.puzzleData.getPuzzleData((self.laytonState.getCurrentNazoListEntry().idExternal - 1))
                if not(puzzleState.wasSolved):
                    wasSkipped = True

            # TODO - Had to remove special behaviour for puzzle 135 (sword puzzle), swaps 4 and 3. Causes last event to miss, dunno why
            if wasSkipped:
                baseEventId = baseEventId.idEvent + 4
            else:
                baseEventId = baseEventId.idEvent + 3
            
            # Override feature used because unified branching behaviour deviates event flow
            EventPlayer.__init__(self, laytonState, screenController, overrideId=baseEventId)
        else:
            EventPlayer.__init__(self, laytonState, screenController)
            self._makeInactive()
            self.doOnKill()
    
    def doOnKill(self):
        self.laytonState.setGameMode(self.laytonState.getGameModeNext())
        return super().doOnKill()