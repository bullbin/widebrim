from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from widebrim.engine.anim.button import AnimatedClickableButton

from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine.state.enum_mode import GAMEMODES
from widebrim.engine_ext.utils import getClickableButtonFromPath, getTxtString
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper

from .const import *

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController
    from widebrim.engine.anim.button import AnimatedButton

class DiaryPlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController):
        ScreenLayerNonBlocking.__init__(self)

        self.__laytonState = laytonState
        self.__screenController = screenController
        self.__buttons : List[AnimatedButton] = []
        self.__diaryButtons : List[Optional[AnimatedClickableButton]] = []
        self.__diaryButtonEntries : List[int] = []
        self.__indexDiaryActive = -1
        self.__indexLoadedDiary = -1

        self.__textRenderer = StaticTextHelper(laytonState.fontEvent, yBias=3)
        self.__textRenderer.setPos((0x11,10))

        def addButtonIfNotNone(button : Optional[AnimatedButton]):
            if button != None:
                self.__buttons.append(button)

        addButtonIfNotNone(getClickableButtonFromPath(laytonState, PATH_ANIM_BTN_CANCEL, namePosVariable=VAR_POS_CANCEL, animOff=NAME_ANIM_CANCEL_OFF, animOn=NAME_ANIM_CANCEL_ON, callback=self.__callbackOnCancel, unclickOnCallback=False))
        screenController.setBgMain(PATH_BG_MAIN % self.__laytonState.language.value)
        screenController.setBgSub(PATH_BG_SUB_INIT % self.__laytonState.language.value)

        # TODO - Sound index here (haha)
        self.__setupDiaryButtons()
        screenController.fadeIn()

    def __setupDiaryButtons(self):
        countAvailableEntries = 0
        x,y = POS_ENTRY_CORNER

        for indexEntry in range(COUNT_DIARY_ENTRIES):
            self.__diaryButtonEntries.append(-1)
            self.__diaryButtons.append(getClickableButtonFromPath(self.__laytonState, PATH_ANIM_BTN_ENTRY, None, pos=(x,y)))
            if self.__laytonState.saveSlot.anthonyDiaryState.flagEnabled.getSlot(indexEntry):
                self.__diaryButtonEntries[countAvailableEntries] = indexEntry
                countAvailableEntries += 1
            
            if (indexEntry % COUNT_ENTRIES_PER_ROW) == (COUNT_ENTRIES_PER_ROW - 1):
                x = POS_ENTRY_CORNER[0]
                y += STRIDE_Y
            else:
                x += STRIDE_X
        
        for indexActiveEntry in range(countAvailableEntries):
            indexEntrySlot = self.__diaryButtonEntries[indexActiveEntry]
            if self.__diaryButtons[indexActiveEntry] != None:
                if self.__laytonState.saveSlot.anthonyDiaryState.flagNew.getSlot(indexEntrySlot):
                    self.__diaryButtons[indexActiveEntry].setAnimNameUnpressed(NAME_ANIM_BTN_NEW_OFF)
                    self.__diaryButtons[indexActiveEntry].setAnimNamePressed(NAME_ANIM_BTN_NEW_ON)
                    self.__diaryButtons[indexActiveEntry].setAnimNameClicked(NAME_ANIM_BTN_NEW_CLICK)
                    self.__diaryButtons[indexActiveEntry].setCallbackOnPressed(self.__callbackOnUnlockNewEntry)
                else:
                    self.__diaryButtons[indexActiveEntry].setAnimNameUnpressed(NAME_ANIM_BTN_OLD_OFF)
                    self.__diaryButtons[indexActiveEntry].setAnimNamePressed(NAME_ANIM_BTN_OLD_ON)
                    self.__diaryButtons[indexActiveEntry].setAnimNameClicked(NAME_ANIM_BTN_OLD_CLICK)
                    self.__diaryButtons[indexActiveEntry].setCallbackOnPressed(self.__callbackOnLoadCurrentEntry)

        for indexDisabledEntry in range(countAvailableEntries, COUNT_DIARY_ENTRIES):
            if self.__diaryButtons != None:
                self.__diaryButtons[indexDisabledEntry].setAnimNameUnpressed(NAME_ANIM_BTN_DISABLE_OFF)
                self.__diaryButtons[indexDisabledEntry].setAnimNamePressed(NAME_ANIM_BTN_DISABLE_ON)
                self.__diaryButtons[indexDisabledEntry].setAnimNameClicked(NAME_ANIM_BTN_DISABLE_CLICK)

    def __callbackOnUnlockNewEntry(self):
        if self.__diaryButtons[self.__indexDiaryActive] != None:
            self.__laytonState.saveSlot.anthonyDiaryState.flagNew.setSlot(False, self.__diaryButtonEntries[self.__indexDiaryActive])
        self.__callbackOnLoadCurrentEntry()

    def __callbackOnLoadCurrentEntry(self):
        if self.__diaryButtons[self.__indexDiaryActive] == None or self.__indexDiaryActive == self.__indexLoadedDiary:
            return

        self.__diaryButtons[self.__indexDiaryActive].setAnimNameUnpressed(NAME_ANIM_BTN_SELECTED_OFF)
        self.__diaryButtons[self.__indexDiaryActive].setAnimNamePressed(NAME_ANIM_BTN_SELECTED_ON)
        self.__diaryButtons[self.__indexDiaryActive].setAnimNameClicked(NAME_ANIM_BTN_SELECTED_CLICK)

        if self.__indexLoadedDiary != -1:
            self.__diaryButtons[self.__indexLoadedDiary].setAnimNameUnpressed(NAME_ANIM_BTN_DESELECTED_OFF)
            self.__diaryButtons[self.__indexLoadedDiary].setAnimNamePressed(NAME_ANIM_BTN_DESELECTED_ON)
            self.__diaryButtons[self.__indexLoadedDiary].setAnimNameClicked(NAME_ANIM_BTN_DESELECTED_CLICK)
        else:
            self.__screenController.setBgSub(PATH_BG_SUB)
        
        self.__indexLoadedDiary = self.__indexDiaryActive
        self.__textRenderer.setText(getTxtString(self.__laytonState, PATH_TXT_DIARY % (self.__indexLoadedDiary + 1)))       

    def doOnKill(self):
        self.__laytonState.saveSlot.menuNewFlag.setSlot(False, 6)
        for indexEntry in range(COUNT_DIARY_ENTRIES):
            if self.__laytonState.saveSlot.anthonyDiaryState.flagNew.getSlot(indexEntry):
                self.__laytonState.saveSlot.menuNewFlag.setSlot(True, 6)
                break
        return super().doOnKill()

    def __callbackOnCancel(self):
        self.__laytonState.setGameMode(GAMEMODES.Bag)
        self.__screenController.fadeOut(callback=self.doOnKill)

    def draw(self, gameDisplay):
        self.__textRenderer.draw(gameDisplay)
        for button in self.__diaryButtons:
            if button != None:
                button.draw(gameDisplay)
        for button in self.__buttons:
            button.draw(gameDisplay)
        return super().draw(gameDisplay)
    
    def update(self, gameClockDelta):
        for button in self.__diaryButtons:
            if button != None:
                button.update(gameClockDelta)
        for button in self.__buttons:
            button.update(gameClockDelta)
        return super().update(gameClockDelta)
    
    def handleTouchEvent(self, event):
        if not(self.__screenController.getFadingStatus()):
            for indexButton, button in enumerate(self.__diaryButtons):
                self.__indexDiaryActive = indexButton
                if button != None and button.handleTouchEvent(event):
                   return True
            for button in self.__buttons:
                if button.handleTouchEvent(event):
                    return True
        return super().handleTouchEvent(event)