from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine.state.enum_mode import GAMEMODES
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getButtonFromPath, getImageFromPath, getStaticButtonFromAnim, getTxtString
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper

from pygame import Surface
from .const import *

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController
    from widebrim.engine.anim.button import StaticButton, AnimatedButton

class ChrViewModePlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController):
        ScreenLayerNonBlocking.__init__(self)

        self.__laytonState = laytonState
        self.__screenController = screenController
        self.__buttons : List[AnimatedButton] = []
        self.__btnCharacters : List[List[Optional[StaticButton]]] = []
        self.__indexPageActive  = 0
        self.__indexBtnClicked  = 0
        self.__indexActive      =  -1

        self.__bgChar : Optional[Surface] = None
        self.__textCharName : StaticTextHelper = StaticTextHelper(laytonState.fontEvent)
        self.__textCharDesc : StaticTextHelper = StaticTextHelper(laytonState.fontQ, yBias=2)

        self.__textCharName.setPos(POS_TEXT_NAME)
        self.__textCharDesc.setPos(POS_TEXT_DESC) 

        def addButtonIfNotNone(button : Optional[AnimatedButton]):
            if button != None:
                self.__buttons.append(button)

        if self.__laytonState.hasAllPuzzlesBeenSolved():
            self.__countPages = COUNT_PAGES_PUZZLES_SOLVED
        else:
            self.__countPages = COUNT_PAGES_PUZZLES_REMAINING

        countBtnRemaining = COUNT_CHAR_BUTTONS
        for indexPage in range(self.__countPages):
            self.__btnCharacters.append([])
            countBtnPerPageRemaining = min(countBtnRemaining, COUNT_CHAR_PER_PAGE)
            animBtn = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_CHAR_BTN_PAGE % (indexPage + 1))

            x,y = POS_CHAR_CORNER
            for indexBtn in range(max(0, countBtnPerPageRemaining)):
                self.__btnCharacters[indexPage].append(getStaticButtonFromAnim(animBtn, str(indexBtn + 1), self.__loadActiveEntry, pos=(x,y), clickOffset=BTN_CLICK_OFFSET))
                if indexBtn % COUNT_CHAR_PER_ROW == COUNT_CHAR_PER_ROW - 1:
                    x = POS_CHAR_CORNER[0]
                    y += STRIDE_Y
                else:
                    x += STRIDE_X
            
            countBtnRemaining -= countBtnPerPageRemaining

        addButtonIfNotNone(getButtonFromPath(laytonState, PATH_ANIM_BTN_CANCEL, callback=self.__callbackOnCancel))
        addButtonIfNotNone(getButtonFromPath(laytonState, PATH_ANIM_BTN, self.__callbackOnPrevious, animOff=NAME_ANIM_BTN_BACK_OFF, animOn=NAME_ANIM_BTN_BACK_ON, namePosVariable=VAR_POS_BACK))
        addButtonIfNotNone(getButtonFromPath(laytonState, PATH_ANIM_BTN, self.__callbackOnNext, animOff=NAME_ANIM_BTN_NEXT_OFF, animOn=NAME_ANIM_BTN_NEXT_ON, namePosVariable=VAR_POS_NEXT))

        screenController.setBgMain(PATH_BG_MAIN % self.__laytonState.language.value)
        screenController.setBgSub(PATH_BG_SUB)

        # TODO - Sound index here (haha)

        self.__loadActiveEntry()
        screenController.fadeIn()

    def __loadActiveEntry(self):
        charId = (self.__indexPageActive * COUNT_CHAR_PER_PAGE) + self.__indexBtnClicked + 1
        if self.__indexActive != charId:
            self.__indexActive = charId
            self.__bgChar = getImageFromPath(self.__laytonState, PATH_ANIM_CHAR % charId)
            
            # HACK - Loads txt.plz twice. No biggie probably...
            strName = getTxtString(self.__laytonState, PATH_TXT_CHAR_NAME % (charId - 1))
            strDesc = getTxtString(self.__laytonState, PATH_TXT_CHAR_DESC % (charId - 1))

            # TODO - Make string shortening universal at binary level, because this could add characters if multi-byte set is used
            self.__textCharName.setText(strName[0:min(len(strName), MAX_LEN_NAME)])
            self.__textCharDesc.setText(strDesc[0:min(len(strDesc), MAX_LEN_DESC)])

    def __callbackOnCancel(self):
        self.__laytonState.setGameMode(GAMEMODES.TopSecretMenu)
        self.__screenController.fadeOut(callback=self.doOnKill)
    
    def __callbackOnNext(self):
        self.__indexPageActive = (self.__indexPageActive + 1) % self.__countPages

    def __callbackOnPrevious(self):
        self.__indexPageActive = (self.__indexPageActive - 1) % self.__countPages

    def draw(self, gameDisplay):
        if self.__bgChar != None:
            gameDisplay.blit(self.__bgChar, (0,0))

        # TODO - Screen separation to prevent non-replicable text overflow bug
        self.__textCharName.draw(gameDisplay)
        self.__textCharDesc.draw(gameDisplay)

        for button in self.__btnCharacters[self.__indexPageActive]:
            if button != None:
                button.draw(gameDisplay)
        for button in self.__buttons:
            button.draw(gameDisplay)
        return super().draw(gameDisplay)
    
    def update(self, gameClockDelta):
        for button in self.__buttons:
            button.update(gameClockDelta)
        return super().update(gameClockDelta)
    
    def handleTouchEvent(self, event):
        if not(self.__screenController.getFadingStatus()):
            for indexButton, button in enumerate(self.__btnCharacters[self.__indexPageActive]):
                self.__indexBtnClicked = indexButton
                if button != None and button.handleTouchEvent(event):
                    return True
            for button in self.__buttons:
                if button.handleTouchEvent(event):
                    return True
        return super().handleTouchEvent(event)