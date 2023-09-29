from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine.state.enum_mode import GAMEMODES
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getButtonFromPath, getStaticButtonFromAnim

from .const import *

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController
    from widebrim.engine.anim.button import StaticButton
    from widebrim.engine.anim.image_anim import AnimatedImageObject

class SecretMenuPlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController):
        ScreenLayerNonBlocking.__init__(self)

        self.__laytonState = laytonState
        self.__screenController = screenController
        self.__buttons = []

        def addButtonIfNotNone(button : Optional[StaticButton]):
            if button != None:
                self.__buttons.append(button)

        self.__animBtn = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_SECRET_BUTTON)
        addButtonIfNotNone(getStaticButtonFromAnim(self.__animBtn, NAME_ANIM_BTN_0, pos=POS_BTN_0, callback=self.__callbackOnWiFiSecretMenu, clickOffset=BTN_CLICK_OFFSET))

        if self.__laytonState.getCountEncounteredStoryPuzzle() > 0:
            addButtonIfNotNone(getStaticButtonFromAnim(self.__animBtn, NAME_ANIM_BTN_1, pos=POS_BTN_1, callback=self.__callbackOnJitenSecret, clickOffset=BTN_CLICK_OFFSET))
        
        if self.__laytonState.isHamsterCompleted() and self.__laytonState.isTeaCompleted() and self.__laytonState.isCameraComplete() and self.__laytonState.saveSlot.isComplete:
            addButtonIfNotNone(getStaticButtonFromAnim(self.__animBtn, NAME_ANIM_BTN_2, pos=POS_BTN_2, callback=self.__callbackOnChallenge, clickOffset=BTN_CLICK_OFFSET))
        
        addButtonIfNotNone(getStaticButtonFromAnim(self.__animBtn, NAME_ANIM_BTN_3, pos=POS_BTN_3, callback=self.__callbackOnTopSecret, clickOffset=BTN_CLICK_OFFSET))

        self.__btnCancel = getButtonFromPath(laytonState, PATH_ANIM_BTN_CANCEL, callback=self.__callbackOnCancel)
        addButtonIfNotNone(self.__btnCancel)

        screenController.setBgMain(PATH_BG_MAIN % self.__laytonState.language.value)
        screenController.setBgSub(PATH_BG_SUB % self.__laytonState.language.value)

        # TODO - Sound index here (haha)

        screenController.fadeIn()
    
    def __callbackOnWiFiSecretMenu(self):
        self.__laytonState.setGameMode(GAMEMODES.WiFiSecretMenu)
        self.__screenController.fadeOut(callback=self.doOnKill)
    
    def __callbackOnJitenSecret(self):
        self.__laytonState.setGameMode(GAMEMODES.JitenSecret)
        self.__laytonState.setGameModeNext(GAMEMODES.SecretMenu)
        self.__screenController.fadeOut(callback=self.doOnKill)
    
    def __callbackOnChallenge(self):
        self.__laytonState.setGameMode(GAMEMODES.Challenge)
        self.__laytonState.setGameModeNext(GAMEMODES.SecretMenu)
        self.__screenController.fadeOut(callback=self.doOnKill)
    
    def __callbackOnTopSecret(self):
        self.__laytonState.setGameMode(GAMEMODES.TopSecretMenu)
        self.__laytonState.setGameModeNext(GAMEMODES.SecretMenu)
        self.__screenController.fadeOut(callback=self.doOnKill)

    def __callbackOnCancel(self):
        # TODO - for some reason game stores an extra variable about whether in secret mode or not
        self.__laytonState.setGameMode(GAMEMODES.Title)
        self.__screenController.fadeOut(callback=self.doOnKill)

    def draw(self, gameDisplay):
        for button in self.__buttons:
            button.draw(gameDisplay)
    
    def update(self, gameClockDelta):
        if self.__btnCancel != None:
            self.__btnCancel.update(gameClockDelta)
    
    def handleTouchEvent(self, event):
        if not(self.__screenController.getFadingStatus()):
            for button in self.__buttons:
                if button.handleTouchEvent(event):
                    return True
        return super().handleTouchEvent(event)
