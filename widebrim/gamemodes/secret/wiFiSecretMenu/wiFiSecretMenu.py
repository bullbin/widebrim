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
    from widebrim.engine.anim.image_anim import AnimatedImageObject

# See other WiFi modes for more information - widebrim has no plans to support WiFi puzzles
# It will import downloaded WiFi puzzles fine. The format is defined in madhatter
# However communication emulation to WFC servers is not planned

class WiFiSecretMenuPlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController):
        ScreenLayerNonBlocking.__init__(self)

        self.__laytonState = laytonState
        self.__screenController = screenController
        self.__buttons = []

        def addButtonIfNotNone(button : Optional[StaticButton]):
            if button != None:
                self.__buttons.append(button)

        self.__animNew : Optional[AnimatedImageObject] = None
        self.__animBtn = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_SECRET_BUTTONS)
        self.__btnSolve : Optional[StaticButton] = None

        if laytonState.wiFiData.getCountEntries() > 0:
            self.__btnSolve = getStaticButtonFromAnim(self.__animBtn, NAME_ANIM_BTN_0, pos=POS_BTN_0, callback=self.__callbackOnStartJiten, clickOffset=BTN_CLICK_OFFSET)

        addButtonIfNotNone(self.__btnSolve)
        addButtonIfNotNone(getStaticButtonFromAnim(self.__animBtn, NAME_ANIM_BTN_1, pos=POS_BTN_1, callback=self.__callbackOnStartDownload, clickOffset=BTN_CLICK_OFFSET))
        addButtonIfNotNone(getStaticButtonFromAnim(self.__animBtn, NAME_ANIM_BTN_2, pos=POS_BTN_2, callback=self.__callbackOnStartWfc, clickOffset=BTN_CLICK_OFFSET))
        
        self.__btnCancel = getButtonFromPath(laytonState, PATH_ANIM_BTN_CANCEL, callback=self.__callbackOnCancel)
    
        drawNew = False
        for indexEntry in range(laytonState.wiFiData.getCountEntries()):
            idInternal = laytonState.wiFiData.getEntry(indexEntry).idInternal
            if (entry := laytonState.getNazoListEntry(idInternal)) != None:
                if (puzzleData := laytonState.saveSlot.puzzleData.getPuzzleData(entry.idExternal - 1)) != None:
                    if not(puzzleData.wasSolved or puzzleData.wasEncountered):
                        drawNew = True
                        break
        
        if drawNew:
            self.__animNew = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_NEW, pos=POS_ANIM_NEW)

        screenController.setBgMain(PATH_BG_MAIN)
        screenController.setBgSub(PATH_BG_SUB)

        # TODO - Sound index here (haha)

        screenController.fadeIn()
    
    def __callbackOnStartJiten(self):
        self.__laytonState.setGameMode(GAMEMODES.JitenWiFi)
        self.__laytonState.setGameModeNext(GAMEMODES.WiFiSecretMenu)
        self.__laytonState.setLastJitenWiFiExternal(0)
        self.__screenController.fadeOut(callback=self.doOnKill)
    
    def __callbackOnStartDownload(self):
        self.__laytonState.setGameMode(GAMEMODES.WiFiDownloadPuzzle)
        self.__screenController.fadeOut(callback=self.doOnKill)

    def __callbackOnStartWfc(self):
        self.__laytonState.setGameMode(GAMEMODES.NintendoWfcSetup)
        self.__screenController.fadeOut(callback=self.doOnKill)
    
    def __callbackOnCancel(self):
        self.__laytonState.setGameMode(GAMEMODES.SecretMenu)
        self.__screenController.fadeOut(callback=self.doOnKill)

    def draw(self, gameDisplay):
        for button in self.__buttons:
            button.draw(gameDisplay)
        if self.__btnCancel != None:
            self.__btnCancel.draw(gameDisplay)
        if self.__animNew != None:
            self.__animNew.draw(gameDisplay)
    
    def update(self, gameClockDelta):
        if self.__btnCancel != None:
            self.__btnCancel.update(gameClockDelta)
        if self.__animNew != None:
            self.__animNew.update(gameClockDelta)
    
    def handleTouchEvent(self, event):
        if not(self.__screenController.getFadingStatus()):
            for button in self.__buttons:
                if button.handleTouchEvent(event):
                    return True
            if self.__btnCancel != None and self.__btnCancel.handleTouchEvent(event):
                return True
        return super().handleTouchEvent(event)
