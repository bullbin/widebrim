from __future__ import annotations
from typing import TYPE_CHECKING

from pygame.constants import BLEND_RGB_SUB
if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController

from widebrim.engine.anim.font.static import generateImageFromString
from widebrim.engine.const import RESOLUTION_NINTENDO_DS, PATH_TEXT_GENERIC
from widebrim.engine.string import getSubstitutedString

from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine.state.enum_mode import GAMEMODES
from widebrim.engine.anim.button import NullButton
from widebrim.engine_ext.utils import getButtonFromPath, getTxt2String
from .const import *

# Overlay_Nazoba
class NazobaPlayer(ScreenLayerNonBlocking):

    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController):
        super().__init__()
        screenController.setBgMain(PATH_BG_NAZOBA)
        screenController.setBgSub(PATH_BG_NAZOBA_SUB)

        self.laytonState = laytonState
        self.screenController = screenController

        self.__buttons = []
        self.__getButtons()

        self._indexExternalNazoEnabled = []
        self.__getEnabledNazo()

        self._countPages = len(self._indexExternalNazoEnabled) // COUNT_NAZOBA_PER_PAGE
        if len(self._indexExternalNazoEnabled) % COUNT_NAZOBA_PER_PAGE != 0:
            self._countPages += 1
        self._indexPage = 0

        self._stringHasNazo = getTxt2String(laytonState, PATH_TEXT_GENERIC % ID_TEXT_NAZO)
        self._stringHasNoNazo = getTxt2String(laytonState, PATH_TEXT_GENERIC % ID_TEXT_NO_NAZO)
        self._nameSurfaces = []
        self._buttonSurfaces = []
        self._indexButtonActive = 0
        self._prepareNames()

        self.__isInteractive = False

        self.screenController.fadeIn(callback=self.__makeActive)
    
    # TODO - These methods are getting frequent - base drawable needs rewrite anyways
    def __makeActive(self):
        self.__isInteractive = True

    def __makeInactive(self):
        self.__isInteractive = False

    def __isActive(self):
        return self.__isInteractive

    def draw(self, gameDisplay):
        super().draw(gameDisplay)
        for button in self.__buttons:
            button.draw(gameDisplay)
        
        if len(self._indexExternalNazoEnabled) > 0:
            x,y = POS_TEXT_NAZOBA
            y += RESOLUTION_NINTENDO_DS[1]
            for nameSurface in self._nameSurfaces:
                gameDisplay.blit(nameSurface, (x,y), special_flags=BLEND_RGB_SUB)
                y += STRIDE_NAZOBA_Y
    
    def handleTouchEvent(self, event):
        if self.__isActive():
            for button in self.__buttons:
                if button.handleTouchEvent(event):
                    return True
            for indexButton, button in enumerate(self._buttonSurfaces):
                self._indexButtonActive = indexButton
                if button.handleTouchEvent(event):
                    return True  
        return super().handleTouchEvent(event)

    def __getEnabledNazo(self):
        for indexNazo in range(1,154):
            puzzleData = self.laytonState.saveSlot.puzzleData.getPuzzleData(indexNazo - 1)
            if puzzleData.enableNazoba and not(puzzleData.wasSolved):
                self._indexExternalNazoEnabled.append(indexNazo)

    def _prepareNames(self):
        # TODO - no text things, load the no text things
        self._cacheNextNames()
        self._createNameButtons()

    def _cacheNextNames(self):
        if self._stringHasNazo != "":
            self._nameSurfaces = []
            for indexExternal in range(self._indexPage * COUNT_NAZOBA_PER_PAGE, min(len(self._indexExternalNazoEnabled), (self._indexPage + 1) * COUNT_NAZOBA_PER_PAGE)):
                indexExternal = self._indexExternalNazoEnabled[indexExternal]
                entryPuzzle = self.laytonState.getNazoListEntryByExternal(indexExternal)
                nameSurface = None
                if entryPuzzle != None:
                    try:
                        nameSurface = self._stringHasNazo % (indexExternal, getSubstitutedString(entryPuzzle.name))
                        nameSurface = generateImageFromString(self.laytonState.fontEvent, nameSurface)
                    except:
                        nameSurface = None
                self._nameSurfaces.append(nameSurface)

    def _createNameButtons(self):
        x,y = POS_NAZO_BTN
        y += RESOLUTION_NINTENDO_DS[1]
        for _indexButton in range(COUNT_NAZOBA_PER_PAGE):
            self._buttonSurfaces.append(NullButton((x,y), (x + SIZE_CLICK_NAZOBA[0], y + SIZE_CLICK_NAZOBA[1]), callback=self.__callbackOnPuzzleStart))
            y += STRIDE_NAZOBA_Y

    def __callbackOnPuzzleStart(self):
        indexSelected = (self._indexPage * COUNT_NAZOBA_PER_PAGE) + self._indexButtonActive
        if indexSelected < len(self._indexExternalNazoEnabled):
            puzzleExternalId = self._indexExternalNazoEnabled[indexSelected]
            # TODO : Yes or No popup
            entryPuzzle = self.laytonState.getNazoListEntryByExternal(puzzleExternalId)
            if entryPuzzle != None:
                self.laytonState.setPuzzleId(entryPuzzle.idInternal)
                self.laytonState.setGameMode(GAMEMODES.Puzzle)
                self.laytonState.setGameModeNext(GAMEMODES.Nazoba)
                self.screenController.fadeOut(callback=self.doOnKill())
        
    def __callbackStartTermination(self):
        self.laytonState.setGameMode(GAMEMODES.Room)
        self.__makeInactive()
        self.screenController.fadeOut(callback=self.doOnKill)

    def __callbackIncrementPage(self):
        if self._countPages > 0:
            self._indexPage += 1
            while self._indexPage >= self._countPages:
                self._indexPage -= self._countPages
            self._cacheNextNames()

    def __callbackDecrementPage(self):
        if self._countPages > 0:
            self._indexPage -= 1
            while self._indexPage < 0:
                self._indexPage += self._countPages
            self._cacheNextNames()

    def __getButtons(self):

        def addIfNotNone(button):
            if button != None:
                self.__buttons.append(button)

        addIfNotNone(getButtonFromPath(self.laytonState, PATH_ANI_BTN_NAZOBA, animOn=NAME_ANI_BACK_ON, animOff=NAME_ANI_BACK_OFF, pos=POS_ANI_BACK, callback=self.__callbackStartTermination))
        addIfNotNone(getButtonFromPath(self.laytonState, PATH_ANI_BTN_NAZOBA, animOn=NAME_ANI_NEXT_ON, animOff=NAME_ANI_NEXT_OFF, pos=POS_ANI_NEXT, callback=self.__callbackIncrementPage))
        addIfNotNone(getButtonFromPath(self.laytonState, PATH_ANI_BTN_NAZOBA, animOn=NAME_ANI_PREV_ON, animOff=NAME_ANI_PREV_OFF, pos=POS_ANI_PREV, callback=self.__callbackDecrementPage))