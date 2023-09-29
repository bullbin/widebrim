from ....engine.anim.font.static import generateImageFromString
from ....engine.const import RESOLUTION_NINTENDO_DS
from ....engine.string import getSubstitutedString
from ...core_popup.utils import FullScreenPopup
from .const import PATH_BG_NAZOBA_MAIN, PATH_BG_NAZOBA_SUB, COUNT_NAZOBA_PER_PAGE, POS_NAZOBA_TEXT, STRIDE_NAZOBA_TEXT

from pygame import BLEND_RGB_SUB, MOUSEBUTTONUP

class NazobaListPopup(FullScreenPopup):
    def __init__(self, laytonState, screenController, callbackOnTerminate, idGroup):
        FullScreenPopup.__init__(self, callbackOnTerminate)
        screenController.setBgMain(PATH_BG_NAZOBA_MAIN)
        screenController.setBgSub(PATH_BG_NAZOBA_SUB)

        self.laytonState = laytonState
        self.screenController = screenController
        self._callbackOnTerminate = callbackOnTerminate

        self._isActive = False
        self._lastDrawnIndex = 0
        self._namesToDraw = []
        self._nameSurfaces = []

        for indexExternalPuzzle in range(1,139):
            entry = laytonState.getNazoListEntryByExternal(indexExternalPuzzle)
            if entry != None and entry.idGroup == idGroup:
                puzzleData = laytonState.saveSlot.puzzleData.getPuzzleData(indexExternalPuzzle - 1)
                if puzzleData != None and not(puzzleData.wasSolved):
                    # TODO - Abstract adjusting nazoba flag as there are index limits, messes with other flags, etc
                    puzzleData.enableNazoba = True
                    tempNameToDraw = "%03d %s" % (indexExternalPuzzle, getSubstitutedString(entry.name))
                    if len(tempNameToDraw) > 0x40:
                        tempNameToDraw = tempNameToDraw[:0x40]
                    self._namesToDraw.append(tempNameToDraw)
        
        self._cacheNextNames()
        screenController.fadeIn(callback=self._makeActive())
    
    def doOnKill(self):
        if callable(self._callbackOnTerminate):
            self._callbackOnTerminate()
        return super().doOnKill()

    def _makeActive(self):
        self._isActive = True
    
    def _makeInactive(self):
        self._isActive = False
    
    def _getActive(self):
        return self._isActive

    def _cacheNextNames(self):
        self._nameSurfaces = []
        for indexName in range(self._lastDrawnIndex, min(len(self._namesToDraw), self._lastDrawnIndex + COUNT_NAZOBA_PER_PAGE)):
            self._nameSurfaces.append(generateImageFromString(self.laytonState.fontEvent, self._namesToDraw[indexName]))
            self._lastDrawnIndex += 1
    
    def draw(self, gameDisplay):
        for indexNameSurface, nameSurface in enumerate(self._nameSurfaces):
            gameDisplay.blit(nameSurface, (POS_NAZOBA_TEXT[0], POS_NAZOBA_TEXT[1] + (indexNameSurface * STRIDE_NAZOBA_TEXT) + RESOLUTION_NINTENDO_DS[1]), special_flags=BLEND_RGB_SUB)
    
    def handleTouchEvent(self, event):
        if self._getActive() and event.type == MOUSEBUTTONUP:
            if self._lastDrawnIndex == len(self._namesToDraw):
                self._makeInactive()
                self.screenController.fadeOut(callback=self.doOnKill)
            else:
                self._cacheNextNames()