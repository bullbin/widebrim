from .utils import PrizeWindow2PopupWithCursor
from .const import ID_UNLOCK_END_CHALLENGE, POS_HAMSTER_TEXT
from ....engine.anim.font.staticFormatted import StaticTextHelper
from ....engine_ext.utils import getTxt2String
from ....engine.const import RESOLUTION_NINTENDO_DS, PATH_TEXT_GENERIC

class EndingAddChallengePopup(PrizeWindow2PopupWithCursor):
    def __init__(self, laytonState, screenController, eventStorage):
        PrizeWindow2PopupWithCursor.__init__(self, laytonState, screenController, eventStorage)

        # TODO - Missing sound, wait from time definition database, etc...
        self.promptText = StaticTextHelper(laytonState.fontEvent)
        try:
            self.promptText.setText(getTxt2String(laytonState, PATH_TEXT_GENERIC % ID_UNLOCK_END_CHALLENGE))
            self.promptText.setPos((POS_HAMSTER_TEXT[0],POS_HAMSTER_TEXT[1] + RESOLUTION_NINTENDO_DS[1]))
        except:
            pass
    
    def drawForegroundElements(self, gameDisplay):
        self.promptText.drawXYCenterPoint(gameDisplay)
        return super().drawForegroundElements(gameDisplay)