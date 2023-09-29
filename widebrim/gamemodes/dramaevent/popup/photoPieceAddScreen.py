from .utils import PrizeWindow2PopupWithCursor
from .const import ID_PHOTO_ALL_FOUND, ID_PHOTO_NEARLY_FOUND, ID_PHOTO_NEW_FOUND, POS_PHOTO_PIECE_PIECE_ICON, POS_PHOTO_PIECE_TEXT
from ....engine.anim.font.staticFormatted import StaticTextHelper
from ....engine_ext.utils import getTxt2String
from ....engine.const import RESOLUTION_NINTENDO_DS, PATH_TEXT_GENERIC

class PhotoPieceAddPopup(PrizeWindow2PopupWithCursor):
    def __init__(self, laytonState, screenController, eventStorage):
        PrizeWindow2PopupWithCursor.__init__(self, laytonState, screenController, eventStorage)

        countRemainingPieces = 0x10 - bytearray(laytonState.saveSlot.eventCounter.toBytes(outLength=128))[0x18]
        if countRemainingPieces == 0:
            idText = ID_PHOTO_ALL_FOUND
        elif countRemainingPieces < 2:
            idText = ID_PHOTO_NEARLY_FOUND
        else:
            idText = ID_PHOTO_NEW_FOUND

        self.pieceIcon = eventStorage.getAssetPieceIcon()
        if self.pieceIcon != None:
            self.pieceIcon.setPos((POS_PHOTO_PIECE_PIECE_ICON[0], POS_PHOTO_PIECE_PIECE_ICON[1] + RESOLUTION_NINTENDO_DS[1]))
            self.pieceIcon.setAnimationFromName("gfx")

        self.promptText = StaticTextHelper(laytonState.fontEvent)
        try:
            if countRemainingPieces > 0:
                self.promptText.setText(getTxt2String(laytonState, PATH_TEXT_GENERIC % idText) % countRemainingPieces)
            else:
                self.promptText.setText(getTxt2String(laytonState, PATH_TEXT_GENERIC % idText))
        except:
            self.promptText.setText("NO DATA")

        self.promptText.setPos((POS_PHOTO_PIECE_TEXT[0], POS_PHOTO_PIECE_TEXT[1] + RESOLUTION_NINTENDO_DS[1]))
    
    def drawForegroundElements(self, gameDisplay):
        self.promptText.drawXYCenterPoint(gameDisplay)
        if self.pieceIcon != None:
            self.pieceIcon.draw(gameDisplay)
        return super().drawForegroundElements(gameDisplay)
    
    def updateForegroundElements(self, gameClockDelta):
        if self.pieceIcon != None:
            self.pieceIcon.update(gameClockDelta)
        return super().updateForegroundElements(gameClockDelta)