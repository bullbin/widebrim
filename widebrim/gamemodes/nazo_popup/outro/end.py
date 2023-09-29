from __future__ import annotations
from typing import TYPE_CHECKING

from pygame.constants import MOUSEBUTTONUP
if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController

from widebrim.engine_ext.utils import getButtonFromPath
from widebrim.gamemodes.core_popup.utils import FullScreenPopup
from ....engine.anim.font.scrolling import ScrollingFontHelper
from widebrim.engine.const import RESOLUTION_NINTENDO_DS, TIME_FRAMECOUNT_TO_MILLISECONDS
from .const import *
from widebrim.gamemodes.nazo_popup.mode.base import BaseQuestionObject

class QuestionEndPopup(FullScreenPopup):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController, callbackOnTerminate):
        super().__init__(callbackOnTerminate)

        self.laytonState = laytonState
        self.screenController = screenController

        self.__isInteractive = False
        self.__buttons = []
        self.__isOnButtonScreen = False
        self._callbackOnTerminate = callbackOnTerminate
        
        def addIfNotNone(button):
            if button != None:
                self.__buttons.append(button)

        self._textScroller = ScrollingFontHelper(laytonState.fontQ, yBias=2, durationPerCharacter=TIME_FRAMECOUNT_TO_MILLISECONDS * 2)
        self._textScroller.setPos((BaseQuestionObject.POS_QUESTION_TEXT[0],
                                   BaseQuestionObject.POS_QUESTION_TEXT[1] + RESOLUTION_NINTENDO_DS[1]))

        if (entryPuzzle := laytonState.saveSlot.puzzleData.getPuzzleData(laytonState.getCurrentNazoListEntry().idExternal - 1)) != None:
            if laytonState.wasPuzzleSolved:
                # TODO - When is encountered flag set?
                # TODO - Set reward flag
                # TODO - Why are we loading two backgrounds??
                entryPuzzle.wasSolved = True
                screenController.setBgMain(PATH_BG_PASS % laytonState.getNazoData().getBgSubIndex())
                self._textScroller.setText(laytonState.getNazoData().getTextCorrect())
                if laytonState.getNazoData().hasAnswerBg():
                    if laytonState.getNazoData().isBgAnswerLanguageDependent():
                        screenController.setBgSub(PATH_BG_ANSWER_LANG % laytonState.getNazoData().getBgMainIndex())
                    else:
                        screenController.setBgSub(PATH_BG_ANSWER % laytonState.getNazoData().getBgMainIndex())
                    screenController.fadeIn(callback=self.__makeActive)
                else:
                    screenController.fadeInMain(callback=self.__makeActive)
            else:
                if not(entryPuzzle.wasSolved):
                    entryPuzzle.incrementDecayStage()

                screenController.setBgMain(PATH_BG_FAIL % laytonState.getNazoData().getBgSubIndex())
                self._textScroller.setText(laytonState.getNazoData().getTextIncorrect())
                screenController.fadeInMain(callback=self.__makeActive)

                addIfNotNone(getButtonFromPath(laytonState, PATH_ANI_TRY_AGAIN, callback=self.__callbackOnTryAgain))
                addIfNotNone(getButtonFromPath(laytonState, PATH_ANI_VIEW_HINT))
                addIfNotNone(getButtonFromPath(laytonState, PATH_ANI_QUIT, callback=self.__callbackOnQuit))
    
    # TODO - These methods are getting frequent - base drawable needs rewrite anyways
    def __makeActive(self):
        self.__isInteractive = True

    def __makeInactive(self):
        self.__isInteractive = False

    def __isActive(self):
        return self.__isInteractive

    def update(self, gameClockDelta):
        if self.__isActive():
            self._textScroller.update(gameClockDelta)
    
    def draw(self, gameDisplay):
        if self.__isOnButtonScreen:
            for button in self.__buttons:
                button.draw(gameDisplay)
        else:
            self._textScroller.draw(gameDisplay)

    def __callbackOnQuit(self):
        self.laytonState.wasPuzzleSkipped = True
        self.__makeInactive()
        self.screenController.fadeOut(callback=self._callbackOnTerminate)
    
    def __callbackOnTryAgain(self):
        self.laytonState.wasPuzzleRestarted = True
        self.__makeInactive()
        self.screenController.fadeOut(callback=self._callbackOnTerminate)

    def __switchToButtonMode(self):
        self.__isOnButtonScreen = True
        self.screenController.setBgMain(PATH_BG_RETRY)
        self.screenController.fadeInMain(callback=self.__makeActive())
    
    def handleTouchEvent(self, event):
        # TODO - Hint popup
        if self.__isActive():
            # TODO - Unify hiding fading status
            if self.__isOnButtonScreen:
                for button in self.__buttons:
                    button.handleTouchEvent(event)
            else:
                if not(self._textScroller.getActiveState()):
                    # Update buttons
                    # TODO - Touch overlay - hide it
                    if event.type == MOUSEBUTTONUP:
                        self.__makeInactive()
                        if self.laytonState.wasPuzzleSolved:
                            self.screenController.fadeOut(callback=self._callbackOnTerminate)
                        else:
                            self.screenController.fadeOutMain(callback=self.__switchToButtonMode)
                else:
                    if event.type == MOUSEBUTTONUP:
                        self._textScroller.skip()

        return super().handleTouchEvent(event)