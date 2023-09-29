from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine.state.enum_mode import GAMEMODES
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getButtonFromPath, getStaticButtonFromAnim, offsetVectorToSecondScreen
from widebrim.engine.anim.image_anim.imageAsNumber import StaticImageAsNumericalFont

from .const import *

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController
    from widebrim.engine.anim.button import StaticButton

class TopSecretMenuPlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController):
        ScreenLayerNonBlocking.__init__(self)

        self.__laytonState = laytonState
        self.__screenController = screenController
        self.__buttons = []
        self.__numRenderer : Optional[StaticImageAsNumericalFont] = None

        def addButtonIfNotNone(button : Optional[StaticButton]):
            if button != None:
                self.__buttons.append(button)

        self.__animBtn = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_SECRET_BUTTON)

        positions = [POS_BTN_0, POS_BTN_1, POS_BTN_2, POS_BTN_3, POS_BTN_4]
        names = [NAME_ANIM_BTN_0, NAME_ANIM_BTN_1, NAME_ANIM_BTN_2, NAME_ANIM_BTN_3, NAME_ANIM_BTN_4]
        callbacks = [self.__callbackOnBtnProfile, self.__callbackOnBtnArt, self.__callbackOnBtnMusic, self.__callbackOnBtnVoice, self.__callbackOnBtnMovie]

        if self.__laytonState.saveSlot.isComplete:
            for pos, name, decay, callback in zip(positions, names, PICARAT_LIMIT, callbacks):
                if self.__laytonState.saveSlot.picarats >= decay:
                    addButtonIfNotNone(getStaticButtonFromAnim(self.__animBtn, name, pos=pos, callback=callback, clickOffset=BTN_CLICK_OFFSET))
        addButtonIfNotNone(getStaticButtonFromAnim(self.__animBtn, NAME_ANIM_BTN_5, pos=POS_BTN_5, callback=self.__callbackOnBtnPasscode ,clickOffset=BTN_CLICK_OFFSET))

        if (animFont := getBottomScreenAnimFromPath(laytonState, PATH_ANIM_PICARAT_NUM)) != None:
            self.__numRenderer = StaticImageAsNumericalFont(animFont, stride=STRIDE_PICARAT, text=self.__laytonState.saveSlot.picarats, maxNum=9999, usePadding=True)
            self.__numRenderer.setPos(offsetVectorToSecondScreen(POS_PICARAT_DISPLAY))

        self.__btnCancel = getButtonFromPath(laytonState, PATH_ANIM_BTN_CANCEL, callback=self.__callbackOnCancel)
        addButtonIfNotNone(self.__btnCancel)

        screenController.setBgMain(PATH_BG_MAIN % self.__laytonState.language.value)
        screenController.setBgSub(PATH_BG_SUB % self.__laytonState.language.value)

        # TODO - Sound index here (haha)

        screenController.fadeIn()
    
    def __callbackShared(self, gamemode):
        self.__laytonState.setGameMode(gamemode)
        self.__laytonState.setGameModeNext(GAMEMODES.TopSecretMenu)
        self.__screenController.fadeOut(callback=self.doOnKill)

    def __callbackOnBtnProfile(self):
        self.__callbackShared(GAMEMODES.ChrViewMode)

    def __callbackOnBtnArt(self):
        self.__callbackShared(GAMEMODES.ArtMode)
    
    def __callbackOnBtnMusic(self):
        self.__callbackShared(GAMEMODES.MusicMode)

    def __callbackOnBtnVoice(self):
        self.__callbackShared(GAMEMODES.VoiceMode)
    
    def __callbackOnBtnMovie(self):
        self.__callbackShared(GAMEMODES.MovieViewMode)
    
    def __callbackOnBtnPasscode(self):
        self.__callbackShared(GAMEMODES.Passcode)    

    def __callbackOnCancel(self):
        self.__laytonState.setGameMode(GAMEMODES.SecretMenu)
        self.__screenController.fadeOut(callback=self.doOnKill)

    def draw(self, gameDisplay):
        for button in self.__buttons:
            button.draw(gameDisplay)
        if self.__numRenderer != None:
            self.__numRenderer.drawBiased(gameDisplay)
    
    def update(self, gameClockDelta):
        if self.__btnCancel != None:
            self.__btnCancel.update(gameClockDelta)
    
    def handleTouchEvent(self, event):
        if not(self.__screenController.getFadingStatus()):
            for button in self.__buttons:
                if button.handleTouchEvent(event):
                    return True
        return super().handleTouchEvent(event)
