from .utils import PrizeWindow2PopupWithCursor
from .const import POS_LOST_SCREEN_PIECE_ICON, ID_LOST_SCREEN, NAME_AUTO_ANIM, POS_PHOTO_PIECE_TEXT
from ....engine_ext.utils import getTxt2String
from ....engine.const import RESOLUTION_NINTENDO_DS, PATH_TEXT_GENERIC
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper

class DoLostPiecePopup(PrizeWindow2PopupWithCursor):
    def __init__(self, laytonState, screenController, eventStorage):
        PrizeWindow2PopupWithCursor.__init__(self, laytonState, screenController, eventStorage)

        self.pieceIcon = eventStorage.getAssetPieceIcon()
        if self.pieceIcon != None:
            self.pieceIcon.setAnimationFromName(NAME_AUTO_ANIM)
            posPieceIcon = ((RESOLUTION_NINTENDO_DS[0] - self.pieceIcon.getDimensions()[0]) // 2,
                            POS_LOST_SCREEN_PIECE_ICON[1] + RESOLUTION_NINTENDO_DS[1])
            self.pieceIcon.setPos(posPieceIcon)

        self.promptText = StaticTextHelper(laytonState.fontEvent)
        self.promptText.setPos((POS_PHOTO_PIECE_TEXT[0], POS_PHOTO_PIECE_TEXT[1] + RESOLUTION_NINTENDO_DS[1]))
        self.promptText.setText(getTxt2String(laytonState, PATH_TEXT_GENERIC % ID_LOST_SCREEN))
    
    def drawForegroundElements(self, gameDisplay):
        if self.pieceIcon != None:
            self.pieceIcon.draw(gameDisplay)
        self.promptText.drawXYCenterPoint(gameDisplay)
        return super().drawForegroundElements(gameDisplay)
    
    def updateForegroundElements(self, gameClockDelta):
        if self.pieceIcon != None:
            self.pieceIcon.update(gameClockDelta)
        return super().updateForegroundElements(gameClockDelta)