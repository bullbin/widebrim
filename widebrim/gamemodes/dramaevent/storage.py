# Centralises assets used in an event so they can be reused
# This reduces asset duplication, as the structure of events
#     mean that the same asset won't be reused in the same
#     frame anyway

# TODO - Figure out remaining data left in event structure
#        Not everything is needed (eg keeping a save screen
#        in memory at all times) but critical images are a must

# TODO - Everything has init positions. Add them where required.

from widebrim.engine_ext.utils import getBottomScreenAnimFromPath
from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from .const import PATH_PRIZE_WINDOW, PATH_CURSOR_WAIT, PATH_ITEM_ICON, PATH_PIECE_ICON, POS_ITEM_ICON_Y
from .const import POS_ITEM_ICON_Y_ALT, PATH_ANIM_REWARD_0, PATH_ANIM_REWARD_1, PATH_ANIM_REWARD_2, PATH_ANIM_REWARD_3

class EventStorage():
    def __init__(self, laytonState):
        self.__prizeWindow2 = None
        self.__animItem     = None
        self.__cursor_wait  = None
        self.__item_icon    = None
        self.__piece_icon   = None
        self.__laytonState = laytonState
    
    def loadItemAnimById(self, idReward):
        if idReward >= 0:
            if idReward < 20:
                self.__animItem = getBottomScreenAnimFromPath(self.__laytonState, PATH_ANIM_REWARD_2)
            elif idReward < 40:
                self.__animItem = getBottomScreenAnimFromPath(self.__laytonState, PATH_ANIM_REWARD_3)
            elif idReward < 60:
                self.__animItem = getBottomScreenAnimFromPath(self.__laytonState, PATH_ANIM_REWARD_1)
            else:
                self.__animItem = getBottomScreenAnimFromPath(self.__laytonState, PATH_ANIM_REWARD_0)
            
            if self.__animItem != None:
                if idReward < 40:
                    self.__animItem.setPos((0, POS_ITEM_ICON_Y + RESOLUTION_NINTENDO_DS[1]))
                else:
                    self.__animItem.setPos((0, POS_ITEM_ICON_Y_ALT + RESOLUTION_NINTENDO_DS[1]))
        return self.__animItem != None
    
    def getAssetItemAnim(self):
        return self.__animItem

    def getAssetPrizeWindow2(self):
        if self.__prizeWindow2 == None:
            self.__prizeWindow2 = getBottomScreenAnimFromPath(self.__laytonState, PATH_PRIZE_WINDOW)
        return self.__prizeWindow2
    
    def getAssetCursorWait(self):
        if self.__cursor_wait == None:
            self.__cursor_wait = getBottomScreenAnimFromPath(self.__laytonState, PATH_CURSOR_WAIT)
        return self.__cursor_wait
    
    def getAssetItemIcon(self):
        if self.__item_icon == None:
            self.__item_icon = getBottomScreenAnimFromPath(self.__laytonState, PATH_ITEM_ICON)
            self.__item_icon.setPos(((RESOLUTION_NINTENDO_DS[0] - self.__item_icon.getDimensions()[0]) // 2, POS_ITEM_ICON_Y + RESOLUTION_NINTENDO_DS[1]))
        return self.__item_icon
    
    def getAssetPieceIcon(self):
        if self.__piece_icon == None:
            self.__piece_icon = getBottomScreenAnimFromPath(self.__laytonState, PATH_PIECE_ICON)
        return self.__piece_icon