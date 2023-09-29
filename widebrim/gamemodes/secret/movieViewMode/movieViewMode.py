from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine.state.enum_mode import GAMEMODES
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getButtonFromPath, getStaticButtonFromAnim

from .const import *

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController
    from widebrim.engine.anim.button import StaticButton

class MovieViewModePlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController):
        ScreenLayerNonBlocking.__init__(self)

        self.__laytonState = laytonState
        self.__screenController = screenController
        self.__buttons = []

        def addButtonIfNotNone(button : Optional[StaticButton]):
            if button != None:
                self.__buttons.append(button)

        self.__animBtn = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_BTN_MOVIE)
        self.__indexBtnActive : int = 0

        x,y = POS_BTN_CORNER
        for indexMovie in range(COUNT_MOVIES):
            addButtonIfNotNone(getStaticButtonFromAnim(self.__animBtn, str(indexMovie + 1), self.__callbackOnMovieClick, pos=(x,y), clickOffset=BTN_CLICK_OFFSET))
            if indexMovie == 17:
                x,y = POS_BTN_FINAL_ROW
            elif indexMovie % LEN_ROW == 5:
                x = POS_BTN_CORNER[0]
                y += STRIDE_BUTTON[1]
            else:
                x += STRIDE_BUTTON[0]

        self.__btnCancel = getButtonFromPath(laytonState, PATH_ANIM_BTN_CANCEL, callback=self.__callbackOnCancel)
        addButtonIfNotNone(self.__btnCancel)

        screenController.setBgMain(PATH_BG_MAIN % self.__laytonState.language.value)
        screenController.setBgSub(PATH_BG_SUB % self.__laytonState.language.value)

        # TODO - Sound index here (haha)

        screenController.fadeIn()

    def __callbackOnCancel(self):
        self.__laytonState.isInMovieMode = False
        self.__laytonState.setGameMode(GAMEMODES.TopSecretMenu)
        self.__screenController.fadeOut(callback=self.doOnKill)
    
    def __callbackOnMovieClick(self):
        if self.__indexBtnActive < len(ID_EVENT_MOVIE):
            self.__laytonState.isInMovieMode = True
            self.__laytonState.setGameMode(GAMEMODES.DramaEvent)
            self.__laytonState.setGameModeNext(GAMEMODES.MovieViewMode)
            self.__laytonState.setEventId(ID_EVENT_MOVIE[self.__indexBtnActive])
            self.__screenController.fadeOut(callback=self.doOnKill)

    def draw(self, gameDisplay):
        for button in self.__buttons:
            button.draw(gameDisplay)
    
    def update(self, gameClockDelta):
        if self.__btnCancel != None:
            self.__btnCancel.update(gameClockDelta)
    
    def handleTouchEvent(self, event):
        if not(self.__screenController.getFadingStatus()):
            for indexButton, button in enumerate(self.__buttons):
                self.__indexBtnActive = indexButton
                if button.handleTouchEvent(event):
                    return True
        return super().handleTouchEvent(event)