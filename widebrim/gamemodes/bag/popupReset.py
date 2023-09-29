from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from widebrim.engine.const import PATH_TEXT_GENERIC, RESOLUTION_NINTENDO_DS
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
from widebrim.gamemodes.bag.const import PATH_ANI_RESET_WINDOW, POS_TEXT_RESET_CENTER, VARIABLE_BTN_RESET_POS, PATH_BTN_RESET_YES, PATH_BTN_RESET_NO
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getButtonFromPath, getTxt2String

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController

from widebrim.gamemodes.dramaevent.popup.utils import FadingPopupAnimBackground
from .const import ID_TEXT2_RESET, PATH_ANI_RESET_FONT

class ResetPopup(FadingPopupAnimBackground):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController, callbackOnYes : Optional[callable], callbackOnNo : Optional[callable]):
        super().__init__(laytonState, screenController, callbackOnNo, getBottomScreenAnimFromPath(laytonState, PATH_ANI_RESET_WINDOW))

        def callbackNo():
            self.startTerminateBehaviour()

        self.__btnYes   = getButtonFromPath(laytonState, PATH_BTN_RESET_YES, callbackOnYes, namePosVariable=VARIABLE_BTN_RESET_POS)
        self.__btnNo    = getButtonFromPath(laytonState, PATH_BTN_RESET_NO, callbackNo, namePosVariable=VARIABLE_BTN_RESET_POS)
        self.__animReset = getBottomScreenAnimFromPath(laytonState, PATH_ANI_RESET_FONT)

        self.__textRenderer = StaticTextHelper(laytonState.fontEvent)
        self.__textRenderer.setText(getTxt2String(laytonState, PATH_TEXT_GENERIC % ID_TEXT2_RESET))
        self.__textRenderer.setPos((POS_TEXT_RESET_CENTER[0], POS_TEXT_RESET_CENTER[1] + RESOLUTION_NINTENDO_DS[1]))
    
    def updateForegroundElements(self, gameClockDelta):
        if self.__btnNo != None:
            self.__btnNo.update(gameClockDelta)
        if self.__btnYes != None:
            self.__btnYes.update(gameClockDelta)
        if self.__animReset != None:
            self.__animReset.update(gameClockDelta)
    
    def drawForegroundElements(self, gameDisplay):
        if self.__animReset != None:
            self.__animReset.draw(gameDisplay)
        if self.__btnNo != None:
            self.__btnNo.draw(gameDisplay)
        if self.__btnYes != None:
            self.__btnYes.draw(gameDisplay)
        self.__textRenderer.drawXCentered(gameDisplay)
    
    def handleTouchEventForegroundElements(self, event):
        if self.__btnNo != None:
            self.__btnNo.handleTouchEvent(event)
        if self.__btnYes != None:
            self.__btnYes.handleTouchEvent(event)
        return True