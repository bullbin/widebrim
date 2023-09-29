from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Optional
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController

from pygame import Surface
from widebrim.engine.state.enum_mode import GAMEMODES
from widebrim.gamemodes.nazo_popup.mode.base.const import NAME_ANIM_VAR_POS_BACK_HINT, NAME_ANIM_VAR_POS_UNLOCK, PATH_ANIM_BTN_BACK, PATH_ANIM_BTN_HINTLOCK_1, PATH_ANIM_BTN_HINTLOCK_2, PATH_ANIM_BTN_HINTLOCK_3, PATH_ANIM_BTN_HINTUNLOCK_1, PATH_ANIM_BTN_HINTUNLOCK_2, PATH_ANIM_BTN_HINTUNLOCK_3, PATH_ANIM_BTN_UNLOCK_NO, PATH_ANIM_BTN_UNLOCK_YES, PATH_BG_JITEN_UNLOCKED, PATH_BG_JITEN_WAIT_UNLOCK, PATH_BG_JITEN_WAIT_UNLOCK_1, PATH_BG_JITEN_WAIT_UNLOCK_2, PATH_BG_JITEN_WAIT_UNLOCK_3, PATH_BG_NO_HINT_COIN_1, PATH_BG_NO_HINT_COIN_2, PATH_BG_NO_HINT_COIN_3, PATH_BG_UNLOCKED, PATH_BG_UNLOCKED_3, PATH_BG_WAIT_UNLOCK_1, PATH_BG_WAIT_UNLOCK_2, PATH_BG_WAIT_UNLOCK_3, POS_HINTTEXT
from widebrim.gamemodes.core_popup.utils import MainScreenPopup
from widebrim.engine_ext.utils import getButtonFromPath, offsetVectorToSecondScreen

# TODO - Not accurate, consier Jiten limitations

class BottomScreenOverlayHint(MainScreenPopup):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController, callbackOnTerminate : Optional[Callable]):
        super().__init__(callbackOnTerminate)
        self.__laytonState = laytonState
        self.__screenController = screenController

        self.__textRendererHintText = StaticTextHelper(laytonState.fontQ, yBias=2)
        self.__textRendererHintText.setPos(offsetVectorToSecondScreen(POS_HINTTEXT))
        self.__callbackOnTerminate = callbackOnTerminate

        # TODO - Unique layout for challenge, wifi, etc... Seems to be configured in init commands
        self.__btnBack = getButtonFromPath(laytonState, PATH_ANIM_BTN_BACK, callbackOnTerminate, namePosVariable=NAME_ANIM_VAR_POS_BACK_HINT)

        spawnPuzzleId = None
        nzLstEntry = laytonState.getCurrentNazoListEntry()
        if nzLstEntry != None: # Not possible since puzzle base should fail (intentional), but might as well safeguard
            spawnPuzzleId = nzLstEntry.idInternal

        self.__wasPuzzleSolved                      = False
        self.__puzzleMaxHintCount                   = 1

        self.__levelHint = 0
        self.__idHintSelected = 0

        self.__btnUnlock = []
        self.__btnLock = []
        self.__btnYesNo = []
        self.__btnActiveYesNoIndex = 0
        self.__btnActiveTabIndex = 0

        for pathButton in [PATH_ANIM_BTN_UNLOCK_YES, PATH_ANIM_BTN_UNLOCK_NO]:
            self.__btnYesNo.append(getButtonFromPath(laytonState, pathButton % laytonState.language.value, self.__callbackOnYesNo, namePosVariable=NAME_ANIM_VAR_POS_UNLOCK))
        for pathButton in [PATH_ANIM_BTN_HINTUNLOCK_1, PATH_ANIM_BTN_HINTUNLOCK_2, PATH_ANIM_BTN_HINTUNLOCK_3]:
            self.__btnUnlock.append(getButtonFromPath(laytonState, pathButton % laytonState.language.value, self.__callbackOnSwitchTab))
        for pathButton in [PATH_ANIM_BTN_HINTLOCK_1, PATH_ANIM_BTN_HINTLOCK_2, PATH_ANIM_BTN_HINTLOCK_3]:
            self.__btnLock.append(getButtonFromPath(laytonState, pathButton % laytonState.language.value, self.__callbackOnSwitchTab))

        if laytonState.getGameModeNext() != GAMEMODES.JitenWiFi and spawnPuzzleId != 0xce:
            self.__puzzleMaxHintCount = 3
            puzzleData = self.__laytonState.saveSlot.puzzleData.getPuzzleData(nzLstEntry.idExternal - 1)
            if puzzleData != None:
                if puzzleData.wasSolved:
                    self.__wasPuzzleSolved = True
                    # TODO - Special last hint index check here
                else:
                    self.__levelHint = puzzleData.levelHint

    def __callbackOnYesNo(self):
        if self.__btnActiveYesNoIndex == 0:
            if not(self.__puzzleMaxHintCount == 1 or self.__wasPuzzleSolved):
                self.__laytonState.saveSlot.hintCoinAvailable -= 1
                # TODO - Set when solved...?
                if (nzLstEntry := self.__laytonState.getCurrentNazoListEntry()) != None:
                    if (puzzleData := self.__laytonState.saveSlot.puzzleData.getPuzzleData(nzLstEntry.idExternal - 1)) != None:
                        puzzleData.levelHint += 1

            self.__levelHint += 1
            self.__getTabBackground()
            self.__getTabContents()
        else:
            # TODO - Forget what happens here...
            if callable(self.__callbackOnTerminate):
                self.__callbackOnTerminate()
        
    def __callbackOnSwitchTab(self):
        # Switch background, change buttons to draw
        self.__idHintSelected = self.__btnActiveTabIndex
        self.__getTabBackground()
        self.__getTabContents()

    def doBeforeSwitching(self):
        if self.__puzzleMaxHintCount == 1 or self.__wasPuzzleSolved:
            self.__idHintSelected = 0
        else:
            self.__idHintSelected = min(self.__levelHint, self.__puzzleMaxHintCount - 1)
        self.__getTabBackground()
        self.__getTabContents()

    def draw(self, gameDisplay : Surface):
        if self.__btnBack != None:
            self.__btnBack.draw(gameDisplay)
        
        for indexTab in range(min(self.__levelHint + 1, self.__puzzleMaxHintCount)):
            if indexTab == self.__levelHint:
                button = self.__btnLock[indexTab]
            else:
                button = self.__btnUnlock[indexTab]
            if button != None:
                button.draw(gameDisplay)
        
        if self.__shouldDrawYesNoButton():
            for button in self.__btnYesNo:
                if button != None:
                    button.draw(gameDisplay)

        self.__textRendererHintText.draw(gameDisplay)

    def __getTabBackground(self):
        if self.__levelHint > self.__idHintSelected:
            # Unlock tab
            if self.__puzzleMaxHintCount == 1:
                # WiFi
                self.__screenController.setBgMain(PATH_BG_JITEN_UNLOCKED % self.__laytonState.language.value)
            else:
                self.__screenController.setBgMain(PATH_BG_UNLOCKED % (self.__laytonState.language.value, self.__idHintSelected + 1))
        else:
            # Locked tab
            if self.__wasPuzzleSolved:
                # Just unlock
                self.__screenController.setBgMain([PATH_BG_JITEN_WAIT_UNLOCK_1, PATH_BG_JITEN_WAIT_UNLOCK_2, PATH_BG_JITEN_WAIT_UNLOCK_3][self.__idHintSelected] % self.__laytonState.language.value)
            elif self.__puzzleMaxHintCount == 1:
                self.__screenController.setBgMain(PATH_BG_JITEN_WAIT_UNLOCK % self.__laytonState.language.value)
            elif self.__laytonState.saveSlot.hintCoinAvailable > 0:
                # Pay to unlock
                self.__screenController.setBgMain([PATH_BG_WAIT_UNLOCK_1, PATH_BG_WAIT_UNLOCK_2, PATH_BG_WAIT_UNLOCK_3][self.__idHintSelected] % self.__laytonState.language.value)
            else:
                self.__screenController.setBgMain([PATH_BG_NO_HINT_COIN_1, PATH_BG_NO_HINT_COIN_2, PATH_BG_NO_HINT_COIN_3][self.__idHintSelected] % self.__laytonState.language.value)

    def __getTabContents(self):
        if self.__idHintSelected >= self.__levelHint:
            self.__textRendererHintText.setText("")
        else:
            if (nzData := self.__laytonState.getNazoData()) != None:
                self.__textRendererHintText.setText(nzData.getTextHints()[self.__idHintSelected])

    def __shouldDrawYesNoButton(self):
        if self.__idHintSelected == self.__levelHint:
            if self.__puzzleMaxHintCount == 1 or self.__wasPuzzleSolved:
                return True
            else:
                return self.__laytonState.saveSlot.hintCoinAvailable > 0

    def update(self, gameClockDelta : float):
        if self.__btnBack != None:
            self.__btnBack.update(gameClockDelta)
        
        for indexTab in range(min(self.__levelHint + 1, self.__puzzleMaxHintCount)):
            if indexTab == self.__levelHint:
                button = self.__btnLock[indexTab]
            else:
                button = self.__btnUnlock[indexTab]
            if button != None:
                button.update(gameClockDelta)
        
        if self.__shouldDrawYesNoButton():
            for button in self.__btnYesNo:
                if button != None:
                    button.update(gameClockDelta)

    def handleTouchEvent(self, event):
        if self.__btnBack != None and self.__btnBack.handleTouchEvent(event):
            return True
        
        for indexTab in range(min(self.__levelHint + 1, self.__puzzleMaxHintCount)):
            if indexTab == self.__levelHint:
                button = self.__btnLock[indexTab]
            else:
                button = self.__btnUnlock[indexTab]
            self.__btnActiveTabIndex = indexTab
            if button != None and button.handleTouchEvent(event):
                return True
                
        if self.__shouldDrawYesNoButton():
            for idxButton, button in enumerate(self.__btnYesNo):
                self.__btnActiveYesNoIndex = idxButton
                if button != None and button.handleTouchEvent(event):
                    return True

        return super().handleTouchEvent(event)