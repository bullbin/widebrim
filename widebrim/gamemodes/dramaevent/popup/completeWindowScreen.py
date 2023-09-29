from .utils import PrizeWindow2PopupWithCursor
from .const import ID_NAMING_HAM, POS_HAMSTER_TEXT
from ....engine.anim.font.staticFormatted import StaticTextHelper
from ....engine_ext.utils import getTxt2String
from ....engine.const import RESOLUTION_NINTENDO_DS, PATH_TEXT_GENERIC

class CompleteWindowPopup(PrizeWindow2PopupWithCursor):
    def __init__(self, laytonState, screenController,  eventStorage, indexText : int, hamsterParam : int):
        PrizeWindow2PopupWithCursor.__init__(self, laytonState, screenController, eventStorage)
        
        self.promptText = StaticTextHelper(laytonState.fontEvent)
        try:
            promptText = getTxt2String(laytonState, PATH_TEXT_GENERIC % indexText)
            if hamsterParam == 1:
                promptText = promptText % laytonState.saveSlot.minigameHamsterState.name

            self.promptText.setText(promptText)
            self.promptText.setPos((POS_HAMSTER_TEXT[0],POS_HAMSTER_TEXT[1] + RESOLUTION_NINTENDO_DS[1]))
        except:
            pass
    
    def drawForegroundElements(self, gameDisplay):
        self.promptText.drawXYCenterPoint(gameDisplay)
        return super().drawForegroundElements(gameDisplay)