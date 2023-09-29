from __future__ import annotations

from typing import TYPE_CHECKING, Callable, List, Optional

from widebrim.engine.anim.button import AnimatedButton
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
from widebrim.engine.anim.image_anim.image import AnimatedImageObject

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController

from widebrim.engine_ext.utils import getButtonFromPath, offsetVectorToSecondScreen
from widebrim.gamemodes.core_popup.utils import MainScreenPopup
from widebrim.gamemodes.nazo_popup.mode.base.const import NAME_ANIM_VAR_POS_QUIT, PATH_ANIM_BTN_UNLOCK_NO, PATH_ANIM_BTN_UNLOCK_YES, PATH_BG_QUIT

# TODO - Not accurate, consier Jiten limitations

class BottomScreenOverlayQuit(MainScreenPopup):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController, callbackOnReturn : Optional[Callable], callbackOnQuit : Optional[Callable], animNazoText : Optional[AnimatedImageObject]):
        super().__init__(callbackOnReturn)
        self.__laytonState = laytonState
        self.__screenController = screenController

        self.__callbackOnReturn = callbackOnReturn
        self.__callbackOnTerminate = callbackOnQuit

        # TODO - Many assets are stored in base to reduce reused... yes/no is one of them :)
        self.__btnYesNo : List[Optional[AnimatedButton]] = []
        for pathButton in [PATH_ANIM_BTN_UNLOCK_YES, PATH_ANIM_BTN_UNLOCK_NO]:
            self.__btnYesNo.append(getButtonFromPath(laytonState, pathButton % laytonState.language.value, self.__callbackOnYesNo, namePosVariable=NAME_ANIM_VAR_POS_QUIT))
        self.__isActiveButtonYes = False

        self.__textRendererPuzzleQuestion = StaticTextHelper(laytonState.fontEvent)
        if (nzData := self.__laytonState.getNazoData()) != None:
            self.__textRendererPuzzleQuestion.setText(nzData.getTextName())
            if animNazoText != None and (varPos := animNazoText.getVariable(NAME_ANIM_VAR_POS_QUIT)) != None:
                self.__textRendererPuzzleQuestion.setPos(offsetVectorToSecondScreen((0, varPos[1] + 4)))
        self.__screenController.setBgMain(PATH_BG_QUIT % self.__laytonState.language.value)
    
    def __callbackOnYesNo(self):
        if self.__isActiveButtonYes:
            if self.__callbackOnTerminate != None:
                self.__callbackOnTerminate()
        elif self.__callbackOnReturn != None:
            self.__callbackOnReturn()

    def update(self, gameClockDelta):
        for button in self.__btnYesNo:
            if button != None:
                button.update(gameClockDelta)
        return super().update(gameClockDelta)

    def draw(self, gameDisplay):
        self.__textRendererPuzzleQuestion.drawXCentered(gameDisplay)
        for button in self.__btnYesNo:
            if button != None:
                button.draw(gameDisplay)
    
    def handleTouchEvent(self, event):
        self.__isActiveButtonYes = True
        for button in self.__btnYesNo:
            if button != None and button.handleTouchEvent(event):
                return True
            self.__isActiveButtonYes = False
        return super().handleTouchEvent(event)