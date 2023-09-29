from .utils import PrizeWindow2PopupWithCursor
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getTxt2String
from widebrim.engine.const import RESOLUTION_NINTENDO_DS, PATH_TEXT_GENERIC
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
from .const import ID_STOCK_SCREEN, PATH_ANIM_NAZO_ICON, POS_STOCK_SCREEN_NAZO_ICON, POS_TEXT_STOCK_SCREEN_Y

class StockPopup(PrizeWindow2PopupWithCursor):
    def __init__(self, laytonState, screenController, eventStorage):
        PrizeWindow2PopupWithCursor.__init__(self, laytonState, screenController, eventStorage)
        self._nazoIcon = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_NAZO_ICON, pos=POS_STOCK_SCREEN_NAZO_ICON)

        try:
            tempPromptText = getTxt2String(laytonState, PATH_TEXT_GENERIC % ID_STOCK_SCREEN)
            tempPromptText = tempPromptText % (laytonState.entryNzList.idExternal, laytonState.entryNzList.name)
        except:
            tempPromptText = ""
        
        self.promptText = StaticTextHelper(laytonState.fontEvent)
        self.promptText.setPos((RESOLUTION_NINTENDO_DS[0] // 2, POS_TEXT_STOCK_SCREEN_Y + RESOLUTION_NINTENDO_DS[1]))
        self.promptText.setText(tempPromptText)
    
    def updateForegroundElements(self, gameClockDelta):
        if self._nazoIcon != None:
            self._nazoIcon.update(gameClockDelta)
        return super().updateForegroundElements(gameClockDelta)

    def drawForegroundElements(self, gameDisplay):
        if self._nazoIcon != None:
            self._nazoIcon.draw(gameDisplay)
        self.promptText.drawXYCenterPoint(gameDisplay)
        return super().drawForegroundElements(gameDisplay)