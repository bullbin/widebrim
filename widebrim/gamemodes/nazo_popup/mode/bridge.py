from __future__ import annotations
from typing import Callable, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController

from widebrim.engine.anim.image_anim.image import AnimatedImageObject
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath
from .onOff import HandlerOnOff
from ....engine.const import RESOLUTION_NINTENDO_DS
from .const import PATH_ANI_BRIDGE

# TODO - Research required. Seems to not care about script?

class HandlerBridge(HandlerOnOff):

    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController, callbackOnTerminate : Optional[Callable]):
        super().__init__(laytonState, screenController, callbackOnTerminate)
        self._setPuzzleTouchBounds(RESOLUTION_NINTENDO_DS[0])

        self.__animFoot : Optional[AnimatedImageObject] = getBottomScreenAnimFromPath(laytonState, PATH_ANI_BRIDGE)

        # 0 - last placed
        # 1 - can place
        # 2 - previous placed
        self.__currentColumn = 0
        self.__currentButton : int = 0
        self.__wasLastFootLeft = None

    def _doReset(self):
        for foot in self._buttons:
            foot.reset()
        self.__currentColumn = 0
        self.__wasLastFootLeft = None
        return super()._doReset()

    def getColumnFromFoot(self, footPos):
            x,y = footPos
            return ((203 - x) // 12) + 1
        
    def isFootLeftFoot(self, footPos):
        left = 129
        x,y = footPos
        return y == left + RESOLUTION_NINTENDO_DS[1]

    def isFootValid(self, footPos) -> bool:
        
        column = self.getColumnFromFoot(footPos)
        isLeft = self.isFootLeftFoot(footPos)

        offsetFromCurrent = column - self.__currentColumn
        if offsetFromCurrent == 1 or offsetFromCurrent == 3:
            if self.__wasLastFootLeft == None:
                return True
            return self.__wasLastFootLeft != isLeft
        return False

    def doOnComplete(self):
        for button in self._buttons:
            button.setCallbackOnPressed(self._onFootPressed)
        return super().doOnComplete()

    def drawPuzzleElements(self, gameDisplay):
        for foot in self._buttons:
            if foot.getEnabledState():
                self.__animFoot.setPos(foot.getPos())
                if self.getColumnFromFoot(foot.getPos()) < self.__currentColumn:
                    if self.isFootLeftFoot(foot.getPos()):
                        self.__animFoot.setAnimationFromName("l2")
                    else:
                        self.__animFoot.setAnimationFromName("r2")
                else:
                    # TODO - Not right for some reason
                    if self.isFootLeftFoot(foot.getPos()):
                        self.__animFoot.setAnimationFromName("l0")
                    else:
                        self.__animFoot.setAnimationFromName("r0")

                self.__animFoot.draw(gameDisplay)

            elif self.isFootValid(foot.getPos()):
                self.__animFoot.setPos(foot.getPos())
                if self.isFootLeftFoot(foot.getPos()):
                    self.__animFoot.setAnimationFromName("l1")
                else:
                    self.__animFoot.setAnimationFromName("r1")
                self.__animFoot.draw(gameDisplay)

        return super().drawPuzzleElements(gameDisplay)

    def _onFootPressed(self):
        self.__currentColumn = self.getColumnFromFoot(self._buttons[self.__currentButton].getPos())
        self.__wasLastFootLeft = self.isFootLeftFoot(self._buttons[self.__currentButton].getPos())

    def updatePuzzleElements(self, gameClockDelta):
        if self._wasAnswerSolution():
            # TODO - Last step can't be pressed
            self._startJudgement()
        return super().updatePuzzleElements(gameClockDelta)

    def handleTouchEventPuzzleElements(self, event):
        for indexButton, button in enumerate(self._buttons):
            self.__currentButton = indexButton
            if self.isFootValid(button.getPos()) and button.handleTouchEvent(event):
                return True
        return False

    def hasRestartButton(self):
        return True
    
    def hasSubmitButton(self):
        return False