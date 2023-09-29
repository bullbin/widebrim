from __future__ import annotations
from typing import TYPE_CHECKING
from widebrim.engine.config import DEBUG_BYPASS_PUZZLE_INTRO
from widebrim.madhatter.common import logVerbose
if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController

from ..engine.state.layer import ScreenLayerNonBlocking
from ..engine.state.enum_mode import GAMEMODES
from .nazo_popup.intro import IntroLayer
from .nazo_popup.outro import OutroLayer
from .nazo_popup.mode import *

ID_TO_NAZO_HANDLER = {2:HandlerFreeButton,

                      3:HandlerOnOff,
                      14:HandlerOnOff,

                      5:HandlerTraceButton,

                      6:HandlerTrace,
                      34:HandlerTraceOnly,

                      9:HandlerDivide,
                      15:HandlerDivide,

                      10:HandlerTouch,
                      11:"Tile",
                      13:HandlerPancake,

                      16:HandlerDrawInput,
                      20:HandlerDrawInput,
                      21:HandlerDrawInput,
                      22:HandlerDrawInput,
                      28:HandlerDrawInput,
                      32:HandlerDrawInput,
                      35:HandlerDrawInput,

                      18:HandlerTile2,
                      26:HandlerTile2,
                      
                      17:HandlerKnight,
                      23:HandlerOnOff2,
                      24:HandlerRose,
                      25:HandlerSlide2,
                      27:HandlerSkate,
                      29:HandlerPegSolitaire,
                      30:HandlerCouple,
                      31:HandlerLamp,
                      33:HandlerBridge}

def getPuzzleHandler(laytonState, screenController, callbackOnTerminate):
    if laytonState.getNazoData() != None:
        try:
            logVerbose("Handler", laytonState.getNazoData().idHandler, name="NazoDispatch")
            handler = ID_TO_NAZO_HANDLER[laytonState.getNazoData().idHandler]
            if type(handler) != str:
                return handler(laytonState, screenController, callbackOnTerminate)
        except KeyError:
            pass
    return BaseQuestionObject(laytonState, screenController, callbackOnTerminate)

class PuzzlePlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController):
        ScreenLayerNonBlocking.__init__(self)
        self.laytonState = laytonState
        self.screenController = screenController
        self._popup = None

        # Use of bypass callbacks eventually causes stack depth error, so delay potential loops to next frame to allow stack to unroll.
        # This is mimicing a very long while loop in game which could potentially go on forever
        self._waitingToUnrollAndRestart = False

        # TODO - Triggers some sound to stop here
        # This check was rewritten, some puzzles seem to not want to be stored, eg ID 203 (secret) intentionally uses external ID 0 which is invalid
        if (activeNazoEntry := self.laytonState.getCurrentNazoListEntry()) != None:
            if (puzzleData := self.laytonState.saveSlot.puzzleData.getPuzzleData(activeNazoEntry.idExternal - 1)) != None:
                # TODO - This actually checks that the puzzle has nothing attached to it - no flags at all
                puzzleData.wasEncountered = True

        if self.laytonState.loadCurrentNazoData():
            # Do intro screen and start loading chain
            if DEBUG_BYPASS_PUZZLE_INTRO:
                self.__callbackSpawnPuzzleObject()
            else:
                self.__callbackSpawnPuzzleIntro()
        else:
            # I think this will cause a softlock. Bypass potentially required (switch to next gamemode?)
            # TODO - Check the nazo data grabbing function for what it does under failure condition
            #        Checked, initial loading never checks for nazo script. Only grabbed in base object.
            self.doOnKill()
    
    def update(self, gameClockDelta):
        if self._waitingToUnrollAndRestart:
            self._waitingToUnrollAndRestart = False
            if DEBUG_BYPASS_PUZZLE_INTRO:
                self.__callbackSpawnPuzzleObject()
            else:
                self.__callbackSpawnPuzzleIntro()
        if self._popup != None:
            self._popup.update(gameClockDelta)
    
    def draw(self, gameDisplay):
        if self._popup != None:
            self._popup.draw(gameDisplay)
    
    def handleTouchEvent(self, event):
        if self._popup != None:
            return self._popup.handleTouchEvent(event)
        return super().handleTouchEvent(event)

    def __callbackSpawnPuzzleIntro(self):
        self.laytonState.wasPuzzleSkipped   = False
        self.laytonState.wasPuzzleSolved    = False
        self.laytonState.wasPuzzleRestarted = False
        self._popup = IntroLayer(self.laytonState, self.screenController, self.__callbackSpawnPuzzleObject)

    def __callbackSpawnPuzzleObject(self):
        self._popup = getPuzzleHandler(self.laytonState, self.screenController, self.__callbackOnPuzzleEnd)

    def __callbackOnPuzzleEnd(self):
        # If user tried to solved puzzle, display outro layer.
        if not(self.laytonState.wasPuzzleSkipped):
            self._popup = OutroLayer(self.laytonState, self.screenController, self.__callbackOnTerminateMode)
            # Callbacks can't be called during init, or very bad things happen
            # self.__callbackOnTerminateMode()
        else:
            self.__callbackOnTerminateMode()

    def __callbackOnTerminateMode(self):
        self._popup = None
        if self.laytonState.wasPuzzleSkipped or not(self.laytonState.wasPuzzleRestarted):
            self.laytonState.setGameMode(self.laytonState.getGameModeNext()) # Usually EndPuzzle
            self.laytonState.unloadCurrentNazoData()
            
            if self.laytonState.getGameMode() == GAMEMODES.Nazoba:
                # TODO - Again only checks flag for value of 2... how does nazoba flag work here?
                if self.laytonState.saveSlot.puzzleData.getPuzzleData(self.laytonState.getCurrentNazoListEntry().idExternal - 1).wasSolved:

                    # TODO - Make const, actually play the event. Nazoba mode is already set but this triggers the reward popups if they were required.
                    self.laytonState.setGameMode(GAMEMODES.DramaEvent)
                    self.laytonState.setEventId(18000)
                    # More checks here... integrates a script player into itself to play script and continue.
                    # TODO - There's one more check about the game being complete so another event can be played

            self.doOnKill()
        else:
            self._waitingToUnrollAndRestart = True