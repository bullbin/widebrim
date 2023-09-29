from __future__ import annotations
from typing import TYPE_CHECKING
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine.anim.image_anim import AnimatedImageObject

from .utils import PrizeWindow2PopupWithCursor
from .const import ANIM_NAME_TEA, TEXT_INVALID_PART, ID_CAM_PART_FOUND, TEXT_INVALID_HERB, ID_HERB_ELEMENT_FOUND, TEXT_INVALID_HAM
from .const import ID_HAM_ELEMENT_FOUND, ID_DIARY_ELEMENT_FOUND, POS_TEXT_ITEM_ADD_Y, POS_TEXT_STOCK_SCREEN_Y
from widebrim.engine.const import RESOLUTION_NINTENDO_DS, PATH_TEXT_CAM, PATH_TEXT_GENERIC, PATH_TEXT_HERB, PATH_TEXT_HAM
from widebrim.engine_ext.utils import getTxt2String, getTxtString
from widebrim.engine.string import getSubstitutedString

class SubItemAddPopup(PrizeWindow2PopupWithCursor):
    def __init__(self, laytonState : Layton2GameState, screenController, eventStorage):
        PrizeWindow2PopupWithCursor.__init__(self, laytonState, screenController, eventStorage)

        self.laytonState = laytonState
        # TODO - Add function to image item both in reverse and widebrim
        def centerCurrentAnimFrame(imageAnim : AnimatedImageObject):
            if imageAnim.getActiveFrame() != None:
                x = imageAnim.getActiveFrame().get_width()
                x = (RESOLUTION_NINTENDO_DS[0] - x) // 2
                imageAnim.setPos((x, imageAnim.getPos()[1]))
        
        def getTextForPopup(pathTxt, textInvalidTxt, idTxt2, rewardIndex):
            namePart = getTxtString(self.laytonState, pathTxt % rewardIndex)
            # TODO - No way of knowing if string wasn't grabbed or string just empty
            if namePart == "":
                namePart = textInvalidTxt % self.laytonState.puzzleLastReward
            
            textPopup = getSubstitutedString(getTxt2String(self.laytonState, PATH_TEXT_GENERIC % idTxt2))
            try:
                return textPopup % namePart
            except:
                return textPopup

        self.__itemIcon = eventStorage.getAssetItemAnim()
        if self.__itemIcon != None:
            self.__itemIcon : AnimatedImageObject

        self.laytonState : Layton2GameState
        self.promptText = StaticTextHelper(laytonState.fontEvent)

        if self.laytonState.puzzleLastReward >= 0:
            if self.laytonState.puzzleLastReward < 20:
                # Enable camera flags and select correct part for display
                self.laytonState.saveSlot.minigameCameraState.cameraAvailableFlags.setSlot(True, self.laytonState.puzzleLastReward)
                if self.__itemIcon != None and self.__itemIcon.setAnimationFromName(str(self.laytonState.puzzleLastReward + 1)):
                    centerCurrentAnimFrame(self.__itemIcon)
                
                textPopup = getTextForPopup(PATH_TEXT_CAM, TEXT_INVALID_PART, ID_CAM_PART_FOUND, self.laytonState.puzzleLastReward)

            elif self.laytonState.puzzleLastReward < 40:
                # Enable item in tea
                self.laytonState.saveSlot.minigameTeaState.flagElements.setSlot(True, self.laytonState.puzzleLastReward - 20)
                # TODO - Const the menu slots
                self.laytonState.saveSlot.menuNewFlag.setSlot(True, 4)

                if self.__itemIcon != None and self.__itemIcon.setAnimationFromName(ANIM_NAME_TEA % (self.laytonState.puzzleLastReward - 19)):
                    centerCurrentAnimFrame(self.__itemIcon)

                textPopup = getTextForPopup(PATH_TEXT_HERB, TEXT_INVALID_HERB, ID_HERB_ELEMENT_FOUND, self.laytonState.puzzleLastReward - 20)

            elif self.laytonState.puzzleLastReward < 60:
                # Add reward to hamster
                # TODO - Check item count not too high

                if self.laytonState.puzzleLastReward == 40:
                    # TODO - Enable hamster
                    pass

                self.laytonState.saveSlot.menuNewFlag.setSlot(True, 3)
                indexItem = self.laytonState.puzzleLastReward - 40
                if indexItem < len(self.laytonState.saveSlot.minigameHamsterState.countItems):
                    self.laytonState.saveSlot.minigameHamsterState.countItems[indexItem] += 1
                if self.__itemIcon != None and self.__itemIcon.setAnimationFromName(str(self.laytonState.puzzleLastReward - 39)):
                    centerCurrentAnimFrame(self.__itemIcon)
                
                textPopup = getTextForPopup(PATH_TEXT_HAM, TEXT_INVALID_HAM, ID_HAM_ELEMENT_FOUND, self.laytonState.puzzleLastReward - 40)

            else:
                # Unlock Anthony diary entry
                # TODO - Animation const
                if self.__itemIcon != None and self.__itemIcon.setAnimationFromName("gfx"):
                    centerCurrentAnimFrame(self.__itemIcon)

                self.laytonState.saveSlot.menuNewFlag.setSlot(True, 6)
                indexTargetDiary = self.laytonState.puzzleLastReward - 60
                if indexTargetDiary < 12:
                    self.laytonState.saveSlot.anthonyDiaryState.flagEnabled.setSlot(True, indexTargetDiary)
                    self.laytonState.saveSlot.anthonyDiaryState.flagNew.setSlot(True, indexTargetDiary)
                
                textPopup = getTxt2String(self.laytonState, PATH_TEXT_GENERIC % ID_DIARY_ELEMENT_FOUND)
        
            self.promptText.setText(textPopup)
            if self.laytonState.puzzleLastReward < 60:
                self.promptText.setPos((RESOLUTION_NINTENDO_DS[0] // 2, POS_TEXT_STOCK_SCREEN_Y + RESOLUTION_NINTENDO_DS[1]))
            else:
                self.promptText.setPos((RESOLUTION_NINTENDO_DS[0] // 2, POS_TEXT_ITEM_ADD_Y + RESOLUTION_NINTENDO_DS[1]))
    
    def drawForegroundElements(self, gameDisplay):
        if self.__itemIcon != None:
            self.__itemIcon.draw(gameDisplay)
        self.promptText.drawXYCenterPoint(gameDisplay)
        return super().drawForegroundElements(gameDisplay)
    
    def updateForegroundElements(self, gameClockDelta):
        if self.__itemIcon != None:
            self.__itemIcon.update(gameClockDelta)
        return super().updateForegroundElements(gameClockDelta)