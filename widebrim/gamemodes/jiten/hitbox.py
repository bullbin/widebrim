from __future__ import annotations
from typing import Optional, TYPE_CHECKING, Tuple
from widebrim.madhatter.hat_io.asset_sav import PuzzleData
from widebrim.engine.anim.image_anim.imageAsNumber import StaticImageAsNumericalFont
from widebrim.engine.state.enum_mode import GAMEMODES
from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.gamemodes.jiten.const import BIAS_HITBOX_SELECT_Y, COUNT_DISPLAY, NAME_ANIM_JITEN_BTN_TOGGLE_FAV_OFF, NAME_ANIM_JITEN_BTN_TOGGLE_FAV_ON, NAME_ANIM_JITEN_TAG_ENCOUNTERED, NAME_ANIM_JITEN_TAG_HAT, NAME_ANIM_JITEN_TAG_SOLVED, NAME_ANIM_JITEN_TAG_UNTOUCHED, POS_CORNER_FAVOURITE, POS_CORNER_HITBOX_SELECT, NAME_MAIN_X_WIFI, NAME_MAIN_X_NORMAL, POS_X_SELECT_BOX
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
from widebrim.engine.anim.image_anim import AnimatedImageObject

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from pygame import Surface

class JitenHitbox():
    def __init__(self, laytonState : Layton2GameState, idExternal : int, indexHitbox : int, imageAll : Optional[AnimatedImageObject], imageNum : Optional[AnimatedImageObject],
                 imageNumText : Optional[StaticImageAsNumericalFont], sourceGamemode, surfaceInternal : Surface):
        self.__laytonState = laytonState
        self.__idExternal = idExternal
        self.__indexHitbox = indexHitbox
        self.__sourceGamemode = sourceGamemode
        self.__surfaceInternal = surfaceInternal

        self.__imageAll = imageAll
        self.__imageNum = imageNum
        self.__textNum  = imageNumText

        self.__textRendererName = StaticTextHelper(laytonState.fontQ)
        if sourceGamemode == GAMEMODES.JitenWiFi:
            nzLstEntry = laytonState.getNazoListEntry(idExternal)
        else:
            nzLstEntry = laytonState.getNazoListEntryByExternal(idExternal)
        
        if nzLstEntry != None:
            # TODO - Will break strings that are too long. Not that they'd work properly anyway
            self.__textRendererName.setText(nzLstEntry.name[0:min(len(nzLstEntry.name), 0x30)])

        self.__posSelect = (0,0)
        self.__posFavourite = (0,0)
        self.__doDraw : bool = True

        self.__applyPos(BIAS_HITBOX_SELECT_Y * indexHitbox)

    def __callbackToggleFavourite(self):
        self.__laytonState.saveSlot.puzzleData.getPuzzleData(self.__idExternal - 1).wasPicked = not(self.__laytonState.saveSlot.puzzleData.getPuzzleData(self.__idExternal - 1).wasPicked)
    
    def __applyPos(self, yOffset : int):
        if yOffset > - BIAS_HITBOX_SELECT_Y and yOffset < BIAS_HITBOX_SELECT_Y * (COUNT_DISPLAY):
            self.__doDraw = True
        else:
            self.__doDraw = False
        self.__posSelect = (POS_CORNER_HITBOX_SELECT[0], POS_CORNER_HITBOX_SELECT[1] + RESOLUTION_NINTENDO_DS[1] + yOffset)
        self.__posFavourite = (POS_CORNER_FAVOURITE[0], POS_CORNER_FAVOURITE[1] + RESOLUTION_NINTENDO_DS[1] + yOffset)

    def applyOffset(self, floatUpperHitbox : float):
        pos = self.__indexHitbox * BIAS_HITBOX_SELECT_Y
        yOffset = pos - floatUpperHitbox
        
        # TODO - Weird positioning again
        if self.__sourceGamemode == GAMEMODES.JitenWiFi:
            self.__textRendererName.setPos((NAME_MAIN_X_WIFI - POS_X_SELECT_BOX, yOffset + 2))
        else:
            self.__textRendererName.setPos((NAME_MAIN_X_NORMAL - POS_X_SELECT_BOX, yOffset + 2))

        self.__applyPos(round(yOffset))
    
    def renderText(self):
        if self.__doDraw:
            self.__textRendererName.draw(self.__surfaceInternal)

    def draw(self, gameDisplay):
        # Note that it may look incorrect to do +1 to position, but game does this too
        if self.__doDraw:
            if self.__imageAll != None and self.__sourceGamemode != GAMEMODES.JitenWiFi:
                if self.__laytonState.saveSlot.puzzleData.getPuzzleData(self.__idExternal - 1).wasPicked:
                    self.__imageAll.setAnimationFromName(NAME_ANIM_JITEN_BTN_TOGGLE_FAV_ON)
                else:
                    self.__imageAll.setAnimationFromName(NAME_ANIM_JITEN_BTN_TOGGLE_FAV_OFF)
                self.__imageAll.setPos(self.__posFavourite)
                self.__imageAll.draw(gameDisplay)
            
            if self.__imageNum != None:
                
                puzzleData : Optional[PuzzleData] = None  
                if self.__sourceGamemode != GAMEMODES.JitenWiFi:
                    statusX =  0x26
                    self.__imageNum.setAnimationFromName(NAME_ANIM_JITEN_TAG_HAT)
                    self.__imageNum.setPos((0x35, self.__posFavourite[1] + 1))
                    self.__imageNum.draw(gameDisplay)
                    puzzleData = self.__laytonState.saveSlot.puzzleData.getPuzzleData(self.__idExternal - 1)
                else:
                    statusX = 0x12
                    nzLstEntry = self.__laytonState.getNazoListEntry(self.__idExternal)
                    if nzLstEntry != None:
                        puzzleData = self.__laytonState.saveSlot.puzzleData.getPuzzleData(nzLstEntry.idExternal - 1)
                
                self.__imageNum.setPos((statusX, self.__posFavourite[1]))

                if puzzleData != None:
                    if puzzleData.wasSolved:
                        self.__imageNum.setAnimationFromName(NAME_ANIM_JITEN_TAG_SOLVED)
                    elif puzzleData.wasEncountered:
                        self.__imageNum.setAnimationFromName(NAME_ANIM_JITEN_TAG_ENCOUNTERED)
                    else:
                        self.__imageNum.setAnimationFromName(NAME_ANIM_JITEN_TAG_UNTOUCHED)
                
                self.__imageNum.draw(gameDisplay)
            
            if self.__textNum != None and self.__sourceGamemode != GAMEMODES.JitenWiFi:
                self.__textNum.setUsePadding(True)
                self.__textNum.setMaxNum(999)
                self.__textNum.setText(self.__idExternal)
                self.__textNum.setPos((0x53, self.__posFavourite[1] + 1))
                self.__textNum.setStride(6)
                self.__textNum.drawBiased(gameDisplay)
                # TODO - WiFi - DrawDate