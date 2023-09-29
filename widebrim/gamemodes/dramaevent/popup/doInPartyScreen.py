from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
from widebrim.engine.const import PATH_TEXT_GENERIC, RESOLUTION_NINTENDO_DS
from widebrim.gamemodes.dramaevent.popup.const import ID_FLORA_JOIN_PARTY, PATH_ANIM_PARTY, POS_PARTY_SCREEN_NAZO_ICON, POS_PHOTO_PIECE_TEXT
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getTxt2String
from widebrim.gamemodes.dramaevent.popup.utils import PrizeWindow2PopupWithCursor

# TODO - Reduce code copy (copied from doOutPartyScreen)

class DoInPartyPopup(PrizeWindow2PopupWithCursor):
    def __init__(self, laytonState, screenController, eventStorage):
        PrizeWindow2PopupWithCursor.__init__(self, laytonState, screenController, eventStorage)
        self.__animParty = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_PARTY, spawnAnimIndex=3, pos=POS_PARTY_SCREEN_NAZO_ICON)
        self._prompt = StaticTextHelper(laytonState.fontEvent)
        self._prompt.setText(getTxt2String(laytonState, PATH_TEXT_GENERIC % ID_FLORA_JOIN_PARTY))
        self._prompt.setPos((POS_PHOTO_PIECE_TEXT[0], POS_PHOTO_PIECE_TEXT[1] + RESOLUTION_NINTENDO_DS[1]))
    
    def drawForegroundElements(self, gameDisplay):
        if self.__animParty != None:
            self.__animParty.draw(gameDisplay)
        self._prompt.drawXYCenterPoint(gameDisplay)
        return super().drawForegroundElements(gameDisplay)
    
    def updateForegroundElements(self, gameClockDelta):
        if self.__animParty != None:
            self.__animParty.update(gameClockDelta)
        return super().updateForegroundElements(gameClockDelta)