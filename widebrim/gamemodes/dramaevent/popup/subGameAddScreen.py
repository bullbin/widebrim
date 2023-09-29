from .utils import PrizeWindow2PopupWithCursor
from .const import ID_SUB_GAME_0, ID_SUB_GAME_1, ID_SUB_GAME_2, ID_SUB_GAME_3, POS_TEXT_SUB_GAME_ADD_Y
from ....engine_ext.utils import getTxt2String
from ....engine.const import PATH_TEXT_GENERIC, RESOLUTION_NINTENDO_DS
from ....engine.anim.font.staticFormatted import StaticTextHelper

class SubGameAddPopup(PrizeWindow2PopupWithCursor):
    def __init__(self, laytonState, screenController, eventStorage, idSubGame):
        PrizeWindow2PopupWithCursor.__init__(self, laytonState, screenController, eventStorage)
        # TODO - Audio commands here

        tempPromptText = ""
        if idSubGame == 0:
            tempPromptText = getTxt2String(laytonState, PATH_TEXT_GENERIC % ID_SUB_GAME_0)
        elif idSubGame == 1:
            tempPromptText = getTxt2String(laytonState, PATH_TEXT_GENERIC % ID_SUB_GAME_1)
            if not(laytonState.saveSlot.minigameHamsterState.isEnabled):
                laytonState.saveSlot.minigameHamsterState.setLevel(1)
        elif idSubGame == 2:
            tempPromptText = getTxt2String(laytonState, PATH_TEXT_GENERIC % ID_SUB_GAME_2)
        elif idSubGame == 3:
            tempPromptText = getTxt2String(laytonState, PATH_TEXT_GENERIC % ID_SUB_GAME_3)
            laytonState.saveSlot.anthonyDiaryState.flagEnabled.setSlot(True, 0)
            laytonState.saveSlot.anthonyDiaryState.flagNew.setSlot(True, 0)
            laytonState.saveSlot.menuNewFlag.setSlot(True, 6)
        
        self.promptText = StaticTextHelper(laytonState.fontEvent)
        self.promptText.setText(tempPromptText)
        self.promptText.setPos((RESOLUTION_NINTENDO_DS[0] // 2, POS_TEXT_SUB_GAME_ADD_Y + RESOLUTION_NINTENDO_DS[1]))
    
    def drawForegroundElements(self, gameDisplay):
        self.promptText.drawXYCenterPoint(gameDisplay)