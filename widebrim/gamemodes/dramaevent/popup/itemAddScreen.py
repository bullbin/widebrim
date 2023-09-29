from .utils import PrizeWindow2PopupWithCursor
from .const import ID_ITEM_ADD, POS_TEXT_ITEM_ADD_Y
from ....engine_ext.utils import getTxtString, getTxt2String
from ....engine.anim.font.staticFormatted import StaticTextHelper
from ....engine.const import PATH_TEXT_ITEM, PATH_TEXT_GENERIC, RESOLUTION_NINTENDO_DS

class ItemAddPopup(PrizeWindow2PopupWithCursor):
    def __init__(self, laytonState, screenController, eventStorage, itemIndex):
        PrizeWindow2PopupWithCursor.__init__(self, laytonState, screenController, eventStorage)

        self.itemIcon = eventStorage.getAssetItemIcon()
        if self.itemIcon != None:
            self.itemIcon.setAnimationFromName(str(itemIndex + 1))

        self.promptText = StaticTextHelper(laytonState.fontEvent)
        tempPromptText = getTxtString(laytonState, PATH_TEXT_ITEM % itemIndex)
        if len(tempPromptText) == 0:
            tempPromptText = "NO DATA"
        
        try:
            # TODO - Unknown failsafe string
            tempPromptText = getTxt2String(laytonState, PATH_TEXT_GENERIC % ID_ITEM_ADD) % tempPromptText
        except:
            pass

        self.promptText.setText(tempPromptText)
        self.promptText.setPos((RESOLUTION_NINTENDO_DS[0] // 2, POS_TEXT_ITEM_ADD_Y + RESOLUTION_NINTENDO_DS[1]))
    
    def drawForegroundElements(self, gameDisplay):
        if self.itemIcon != None:
            self.itemIcon.draw(gameDisplay)
        self.promptText.drawXYCenterPoint(gameDisplay)
        return super().drawForegroundElements(gameDisplay)
    
    def updateForegroundElements(self, gameClockDelta):
        if self.itemIcon != None:
            self.itemIcon.update(gameClockDelta)
        return super().updateForegroundElements(gameClockDelta)