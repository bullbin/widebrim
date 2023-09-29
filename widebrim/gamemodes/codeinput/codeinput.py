from __future__ import annotations

from typing import TYPE_CHECKING
from widebrim.engine.cipher import generatePasscode
from widebrim.gamemodes.codeinput.const import COUNT_KEYS, ID_EVENT_CONCEPT_ART, ID_EVENT_SECRET, LEN_SECRET, PATH_ANIM_BAD_CODE, PATH_ANIM_BTN_CANCEL, PATH_ANIM_BTN_KESU, PATH_ANIM_BTN_KETTEI, PATH_ANIM_CURSOR, PATH_BG_MAIN, PATH_BG_SUB_FUTURE, PATH_BG_SUB_PANDORA, PATH_PACK_TEXT, PATH_SECRET, POS_ANIM_CURSOR, POS_BAD_CODE, POS_KEY_CORNER, POS_KEY_CORNER_19, POS_KEY_CORNER_28, POS_KEY_CORNER_9, POS_TEXT, SIZE_KEY, STRIDE_KEY_X, STRIDE_TEXT_X, VAR_CANCEL_POS
from ...engine.state.layer import ScreenLayerNonBlocking
from ...engine.state.enum_mode import GAMEMODES
from ...engine.const import CIPHER_IV, RESOLUTION_NINTENDO_DS
from ...engine.exceptions import FileInvalidCritical
from ...engine.anim.button import NullButton
from ...engine.anim.font.static import generateImageFromStringStrided
from ...engine_ext.utils import getBottomScreenAnimFromPath, getButtonFromPath

from pygame import MOUSEBUTTONUP, BLEND_RGB_SUB, BLEND_RGB_MULT, Surface
if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController

# TODO - Just adapted from Name handler...

class KeyboardButton(NullButton):
    def __init__(self, pos, posEnd, callback=None):
        NullButton.__init__(self, pos, posEnd, callback=callback)
        self.needsHighlightSurface = False

    def doOnMouseTargetting(self):
        self.needsHighlightSurface = True

    def doOnMouseAwayFromTarget(self):
        self.needsHighlightSurface = False

class CodeInputPlayer(ScreenLayerNonBlocking):

    LENGTH_ENTRY = 8

    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController):
        super().__init__()
        self.screenController = screenController
        self.laytonState = laytonState
        self.__entry = ""
        self.__entryValid = ""
        self.__activeMap = ""

        try:
            self.__activeMap = laytonState.getFileAccessor().getPackedString(PATH_PACK_TEXT, PATH_SECRET)
            self.__activeMap = self.__activeMap[0:min(len(self.__activeMap), LEN_SECRET)]
        except:
            raise FileInvalidCritical

        self.screenController.setBgMain(PATH_BG_MAIN)
        if self.laytonState.getGameMode() == GAMEMODES.CodeInputPandora:
            self.screenController.setBgSub(PATH_BG_SUB_PANDORA % laytonState.language.value)
            self.__entryValid = generatePasscode(CIPHER_IV.Pandora)
        else:
            self.screenController.setBgSub(PATH_BG_SUB_FUTURE % laytonState.language.value)
            self.__entryValid = generatePasscode(CIPHER_IV.Future)

        self.__keys = []
        self.__buttons = []
        self.__activeKey = 0
        self.__drawBadCodeScreen = False

        def addButtonIfNotNone(button):
            if button != None:
                self.__buttons.append(button)

        def callbackOnOk():
            # TODO - Audio effect if pressed and nothing in box
            if len(self.__entry) != 0:
                if self.__entry != self.__entryValid:
                    self.__drawBadCodeScreen = True
                else:
                    if self.laytonState.getGameMode() == GAMEMODES.CodeInputPandora:
                        self.laytonState.saveSlot.codeInputFlags.setSlot(True,0)
                        self.laytonState.setEventId(ID_EVENT_SECRET)
                    else:
                        self.laytonState.saveSlot.codeInputFlags.setSlot(True,8)
                        self.laytonState.setEventId(ID_EVENT_CONCEPT_ART)
                        
                    self.laytonState.setGameMode(GAMEMODES.DramaEvent)
                    self.laytonState.setGameModeNext(GAMEMODES.Passcode)
                    self.screenController.fadeOut(callback=self.doOnKill)

        def callbackOnErase():
            if len(self.__entry) > 0:
                self.__entry = self.__entry[:-1]
                self._updateEntry()

        def callbackOnKeyPress():
            if self.__activeKey < len(self.__activeMap):
                self._addCharToEntry(self.__activeMap[self.__activeKey])

        def callbackOnCancel():
            self.laytonState.setGameMode(GAMEMODES.Passcode)
            self.screenController.fadeOut(callback=self.doOnKill)

        for _indexKey in range(COUNT_KEYS):
            self.__keys.append(KeyboardButton((0,0), SIZE_KEY, callback=callbackOnKeyPress))

        self.__surfaceBadCode = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_BAD_CODE)
        self.__surfaceBadCode.setPos(((RESOLUTION_NINTENDO_DS[0] - self.__surfaceBadCode.getDimensions()[0]) // 2, POS_BAD_CODE[1] + RESOLUTION_NINTENDO_DS[1]))

        self.__animCursor = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_CURSOR)

        addButtonIfNotNone(getButtonFromPath(laytonState, PATH_ANIM_BTN_KETTEI, callback=callbackOnOk))
        addButtonIfNotNone(getButtonFromPath(laytonState, PATH_ANIM_BTN_KESU, callback=callbackOnErase))
        addButtonIfNotNone(getButtonFromPath(laytonState, PATH_ANIM_BTN_CANCEL, callback=callbackOnCancel, namePosVariable=VAR_CANCEL_POS))

        self.__surfaceEntry = None
        self.__surfaceHighlight = Surface(SIZE_KEY)
        # Produces similar colour, but sticking with Pygame's blend modes
        self.__surfaceHighlight.fill((255,128,128))

        self._updateKeyPositionDefault()
        self._updateEntry()
        self.screenController.fadeIn()

    def update(self, gameClockDelta):
        self.__animCursor.update(gameClockDelta)
        for button in self.__buttons:
            button.update(gameClockDelta)
        if self.__drawBadCodeScreen:
            self.__surfaceBadCode.update(gameClockDelta)

    def draw(self, gameDisplay):
        if self.__surfaceEntry != None:
            gameDisplay.blit(self.__surfaceEntry, (POS_TEXT[0] + 1, POS_TEXT[1] + RESOLUTION_NINTENDO_DS[1]), special_flags=BLEND_RGB_SUB)
        
        self.__animCursor.draw(gameDisplay)
        for button in self.__buttons:
            button.draw(gameDisplay)

        for key in self.__keys:
            if key.needsHighlightSurface:
                gameDisplay.blit(self.__surfaceHighlight, key.getPos(), special_flags=BLEND_RGB_MULT)
                break

        if self.__drawBadCodeScreen:
            self.__surfaceBadCode.draw(gameDisplay)

    def handleTouchEvent(self, event):
        if not(self.screenController.getFadingStatus()):
            if self.__drawBadCodeScreen:
                if event.type == MOUSEBUTTONUP:
                    self.__drawBadCodeScreen = False
                    self._clearEntry()
                    return True
            else:
                for indexKey in range(COUNT_KEYS):
                    self.__activeKey = indexKey
                    if self.__keys[indexKey].handleTouchEvent(event):
                        return True
                for button in self.__buttons:
                    if button.handleTouchEvent(event):
                        return True
        return super().handleTouchEvent(event)

    def _updateKeyPositionDefault(self):
        x,y = POS_KEY_CORNER
        for indexKey, key in enumerate(self.__keys):
            key.setPos((x,y + RESOLUTION_NINTENDO_DS[1]))
            x += STRIDE_KEY_X
            if indexKey == 9:
                x,y = POS_KEY_CORNER_9
            elif indexKey == 19:
                x,y = POS_KEY_CORNER_19
            elif indexKey == 28:
                x,y = POS_KEY_CORNER_28

    def _updateEntry(self):
        if len(self.__entry) == CodeInputPlayer.LENGTH_ENTRY:
            self.__animCursor.setPos((POS_ANIM_CURSOR[0] + (STRIDE_TEXT_X * (CodeInputPlayer.LENGTH_ENTRY - 1)), POS_ANIM_CURSOR[1] + RESOLUTION_NINTENDO_DS[1]))
        else:
            self.__animCursor.setPos((POS_ANIM_CURSOR[0] + (STRIDE_TEXT_X * len(self.__entry)), POS_ANIM_CURSOR[1] + RESOLUTION_NINTENDO_DS[1]))
            
        self.__surfaceEntry = generateImageFromStringStrided(self.laytonState.fontEvent, self.__entry, STRIDE_TEXT_X)

    def _clearEntry(self):
        self.__entry = ""
        self._updateEntry()

    def _addCharToEntry(self, char):
        if len(self.__entry) >= CodeInputPlayer.LENGTH_ENTRY:
            self.__entry = self.__entry[0:CodeInputPlayer.LENGTH_ENTRY - 1] + char
            self._updateEntry()
        elif len(self.__entry) < CodeInputPlayer.LENGTH_ENTRY:
            self.__entry += char
            self._updateEntry()