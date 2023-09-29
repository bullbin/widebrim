from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from widebrim.engine.anim.image_anim.image import AnimatedImageObject
from widebrim.engine.state.enum_mode import GAMEMODES
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getButtonFromPath, getClickableButtonFromPath, getTxtString
from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine.anim.button import AnimatedButton, NullButton
from .const import *

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController

# TODO - Research positions from binary
# TODO - Fix text line (bottom screen) positions and add page number to draw

class MemoPlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController):
        super().__init__()
        self.laytonState        = laytonState
        self.screenController   = screenController
        self.__interactable : bool    = False
        
        self.__countEntries : int = 0
        self.__pageNumber : int = self.laytonState.saveSlot.lastMemoPage
        if self.__pageNumber == 0:
            self.__pageNumber = 1

        self.__loadCountEntries()

        self.__buttonEntries : List[NullButton] = []
        self.__surfacesTitle : List[StaticTextHelper] = []
        x = BUTTON_OFFSET[0]
        y = BUTTON_OFFSET[1] + RESOLUTION_NINTENDO_DS[1]
        for indexButton in range(COUNT_BUTTON_ENTRIES):
            self.__buttonEntries.append(NullButton((x,y), (x+BUTTON_DIMENSIONS[0], y+BUTTON_DIMENSIONS[1]), callback=self.__callbackOnEntryPress))
            self.__surfacesTitle.append(StaticTextHelper(self.laytonState.fontEvent))
            # TODO - position was from visual, no basis in binary
            self.__surfacesTitle[indexButton].setPos((x + 28,y + 3))
            y += BUTTON_STRIDE_Y + 1 # TODO - What's going on with spacing here? Missing padding?

        # TODO - Button collection class, faster
        self.__buttons : List[AnimatedButton] = []
        def addButtonIfNotNone(button : Optional[AnimatedButton]):
            if button != None:
                self.__buttons.append(button)
        
        addButtonIfNotNone(getButtonFromPath(self.laytonState, PATH_ANIM_MEMO_BUTTONS, animOff=NAME_ANIM_BACK_OFF, animOn=NAME_ANIM_BACK_ON, namePosVariable=POS_ANIM_BACK, callback=self.__callbackOnPrevPage))
        addButtonIfNotNone(getButtonFromPath(self.laytonState, PATH_ANIM_MEMO_BUTTONS, animOff=NAME_ANIM_NEXT_OFF, animOn=NAME_ANIM_NEXT_ON, namePosVariable=POS_ANIM_NEXT, callback=self.__callbackOnNextPage))
        addButtonIfNotNone(getClickableButtonFromPath(self.laytonState, PATH_ANIM_MEMO_CLOSE, animOff=NAME_ANIM_CLOSE_OFF, animOn=NAME_ANIM_CLOSE_ON, animClick=NAME_ANIM_CLOSE_CLICK, namePosVariable=POS_ANIM_CLICK, callback=self.__callbackOnClose, unclickOnCallback=False))

        self.screenController.setBgMain(PATH_BG_MAIN)
        self.screenController.setBgSub(PATH_BG_SUB % laytonState.language.value)
        self.screenController.fadeIn(callback=self.__makeActive)

        self.__textContents = StaticTextHelper(self.laytonState.fontEvent, yBias=3)
        self.__textContents.setPos((18,11))

        self.__indexButton : int = 0
        self.__indexActiveEntry : int = -1
        self.__animMemoGfx : Optional[AnimatedImageObject] = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_MEMO_GFX)
        self.__doOnReloadPage()
    
    def __makeActive(self):
        self.__interactable = True

    def __makeInactive(self):
        self.__interactable = False

    def draw(self, gameDisplay):
        self.__drawHatNew(gameDisplay)
        for button in self.__buttons + self.__surfacesTitle:
            button.draw(gameDisplay)
        self.__textContents.draw(gameDisplay)
        return super().draw(gameDisplay)

    def doOnKill(self):
        self.laytonState.saveSlot.menuNewFlag.setSlot(False,0)
        # TODO - 0x39?
        for indexEntry in range(0x3a):
            if self.laytonState.saveSlot.memoFlag.flagNew.getSlot(indexEntry):
                self.laytonState.saveSlot.menuNewFlag.setSlot(True, 0)
                break
        return super().doOnKill()
    
    def handleTouchEvent(self, event):
        if self.__interactable:
            for button in self.__buttons:
                if button.handleTouchEvent(event):
                    return True

            for indexButton, button in enumerate(self.__buttonEntries):
                self.__indexButton = indexButton
                if button.handleTouchEvent(event):
                    return True
        return super().handleTouchEvent(event)

    def __callbackOnEntryPress(self):
        targetEntry = ((self.__pageNumber - 1) * COUNT_BUTTON_ENTRIES) + self.__indexButton
        if self.laytonState.saveSlot.memoFlag.flagEnabled.getSlot(targetEntry):
            if self.__indexActiveEntry != targetEntry:
                
                if self.__indexActiveEntry == -1:
                    self.screenController.setBgSub(PATH_BG_SUB_ENTRY)

                self.__indexActiveEntry = targetEntry
                self.__redrawEntryContents()
    
    def __callbackOnNextPage(self):
        self.__pageNumber += 1
        if self.__pageNumber > 10:
            self.__pageNumber = 1
        self.__doOnReloadPage()

    def __callbackOnPrevPage(self):
        self.__pageNumber -= 1
        if self.__pageNumber < 1:
            self.__pageNumber = 10
        self.__doOnReloadPage()

    def __callbackOnClose(self):
        self.__makeInactive()
        self.laytonState.saveSlot.lastMemoPage = self.__pageNumber
        self.laytonState.setGameMode(GAMEMODES.Bag)
        self.screenController.fadeOut(callback=self.doOnKill)

    def __doOnReloadPage(self):
        for indexEntry in range(COUNT_BUTTON_ENTRIES):
            targetEntry = ((self.__pageNumber - 1) * COUNT_BUTTON_ENTRIES) + indexEntry
            if self.laytonState.saveSlot.memoFlag.flagEnabled.getSlot(targetEntry):
                if targetEntry == self.__indexActiveEntry:
                    self.__surfacesTitle[indexEntry].setColor((255,0,0))
                else:
                    self.__surfacesTitle[indexEntry].setColor((0,0,0))
                self.__surfacesTitle[indexEntry].setText(getTxtString(self.laytonState, PATH_TEXT_TITLE % (targetEntry + 1)))
            else:
                self.__surfacesTitle[indexEntry].setText("")

    def __loadCountEntries(self):
        self.__countEntries = 0
        # TODO - This might be 57 instead
        for indexFlag in range(0x40):
            if self.laytonState.saveSlot.memoFlag.flagEnabled.getSlot(indexFlag):
                self.__countEntries += 1
    
    def __redrawEntryContents(self):
        self.laytonState.saveSlot.memoFlag.flagNew.setSlot(False, self.__indexActiveEntry)
        text = getTxtString(self.laytonState, PATH_TEXT_CONTENT % (self.__indexActiveEntry + 1))
        if text == "":
            text = TEXT_FILE_NOT_FOUND % (self.__indexActiveEntry + 1)
        self.__textContents.setText(text)
        self.__doOnReloadPage()
    
    def __drawHatNew(self, gameDisplay):
        if self.__animMemoGfx != None:
            x = 0xf
            y = 0x20 + RESOLUTION_NINTENDO_DS[1]
            for indexEntry in range(COUNT_BUTTON_ENTRIES):
                self.__animMemoGfx.setPos((x,y))
                targetEntry = ((self.__pageNumber - 1) * COUNT_BUTTON_ENTRIES) + indexEntry
                if self.laytonState.saveSlot.memoFlag.flagEnabled.getSlot(targetEntry):
                    self.__animMemoGfx.setAnimationFromName(NAME_ANIM_HAT)
                    if self.laytonState.saveSlot.memoFlag.flagNew.getSlot(targetEntry):
                        self.__animMemoGfx.setAnimationFromName(NAME_ANIM_NEW)
                    self.__animMemoGfx.draw(gameDisplay)
                y += 0x16