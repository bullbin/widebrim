from .utils import PrizeWindow2PopupWithCursor

from .const import ID_SAVE_COMPLETE, PATH_ANIM_BUTTON_YES, PATH_ANIM_BUTTON_NO, ID_SAVE_NOT_COMPLETE, POS_TEXT_SAVE_Y
from ....engine.const import RESOLUTION_NINTENDO_DS, PATH_TEXT_GENERIC
from ....engine.anim.font.static import generateImageFromString
from ....engine_ext.utils import getButtonFromPath, getTxt2String

from pygame import BLEND_RGB_SUB

# TODO - Reuse me for overwrite save confirmation window
# TODO - Add text support

class SaveButtonPopup(PrizeWindow2PopupWithCursor):
    def __init__(self, laytonState, screenController, eventStorage, callbackOnDoSave, callbackOnSkipSave, saveIsComplete=False):
        self._callbackOnDoSave = callbackOnDoSave
        self._callbackOnSkippedSave = callbackOnSkipSave

        def callbackOnYes():
            self._callbackOnTerminate = self._callbackOnDoSave
            self.startTerminateBehaviour()
        
        def callbackOnNo():
            self._callbackOnTerminate = self._callbackOnSkippedSave
            self.startTerminateBehaviour()

        PrizeWindow2PopupWithCursor.__init__(self, laytonState, screenController, eventStorage)

        # TODO - What is the pos name here?
        if saveIsComplete:
            promptId = ID_SAVE_COMPLETE
        else:
            promptId = ID_SAVE_NOT_COMPLETE

        self._prompt = generateImageFromString(laytonState.fontEvent, getTxt2String(laytonState, PATH_TEXT_GENERIC % promptId))
        self._promptPos = ((RESOLUTION_NINTENDO_DS[0] - self._prompt.get_width()) // 2, POS_TEXT_SAVE_Y + RESOLUTION_NINTENDO_DS[1])

        # TODO - Handle if None
        self.buttonYes = getButtonFromPath(laytonState, PATH_ANIM_BUTTON_YES, namePosVariable="win_p", callback=callbackOnYes)
        self.buttonNo = getButtonFromPath(laytonState, PATH_ANIM_BUTTON_NO, namePosVariable="win_p", callback=callbackOnNo)
    
    def updateForegroundElements(self, gameClockDelta):
        self.buttonYes.update(gameClockDelta)
        self.buttonNo.update(gameClockDelta)

    def drawForegroundElements(self, gameDisplay):
        gameDisplay.blit(self._prompt, self._promptPos, special_flags=BLEND_RGB_SUB)
        self.buttonYes.draw(gameDisplay)
        self.buttonNo.draw(gameDisplay)

    def handleTouchEventForegroundElements(self, event):
        self.buttonYes.handleTouchEvent(event)
        self.buttonNo.handleTouchEvent(event)
        return True