# TODO - Very similar code to save popup
from widebrim.engine.const import PATH_TEXT_GENERIC, RESOLUTION_NINTENDO_DS
from widebrim.gamemodes.dramaevent.popup.const import ID_CAM_PART_FOUND, ID_HERB_ELEMENT_FOUND, ID_STATION_RETURN, PATH_ANIM_BUTTON_NO, PATH_ANIM_BUTTON_YES, POS_RETURN_STATION_TEXT
from .utils import PrizeWindow2PopupWithCursor
from widebrim.engine_ext.utils import getClickableButtonFromPath, getTxt2String
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper

class ReturnStationPopup(PrizeWindow2PopupWithCursor):
    def __init__(self, laytonState, screenController, eventStorage):
        super().__init__(laytonState, screenController, eventStorage)

        def callbackOnYes():
            laytonState.setPlaceNum(0x23)
            self.startTerminateBehaviour()

        self._prompt = StaticTextHelper(laytonState.fontEvent)
        self._prompt.setText(getTxt2String(laytonState, PATH_TEXT_GENERIC % ID_STATION_RETURN))     # This is meant to be blank - missing in original game
        self._prompt.setPos((POS_RETURN_STATION_TEXT[0],POS_RETURN_STATION_TEXT[1] + RESOLUTION_NINTENDO_DS[1]))

        self.buttonNo = getClickableButtonFromPath(laytonState, PATH_ANIM_BUTTON_NO, self.startTerminateBehaviour, namePosVariable="win_p")
        self.buttonYes = getClickableButtonFromPath(laytonState, PATH_ANIM_BUTTON_YES, callbackOnYes, namePosVariable="win_p")
    
    def updateForegroundElements(self, gameClockDelta):
        self.buttonYes.update(gameClockDelta)
        self.buttonNo.update(gameClockDelta)

    def drawForegroundElements(self, gameDisplay):
        self._prompt.drawXYCenterPoint(gameDisplay)
        self.buttonYes.draw(gameDisplay)
        self.buttonNo.draw(gameDisplay)

    def handleTouchEventForegroundElements(self, event):
        self.buttonYes.handleTouchEvent(event)
        self.buttonNo.handleTouchEvent(event)
        return True