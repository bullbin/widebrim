from __future__ import annotations
from math import sqrt
from random import randint
from typing import List, Optional, TYPE_CHECKING, Tuple, Union
from widebrim.engine.anim.image_anim.imageAsNumber import StaticImageAsNumericalFont
from widebrim.engine.anim.button import NullButton
from pygame.constants import BLEND_RGB_SUB, MOUSEBUTTONDOWN, MOUSEBUTTONUP
from widebrim.madhatter.common import logVerbose
from widebrim.madhatter.hat_io.asset_dat.place import Exit, PlaceDataNds
from widebrim.madhatter.hat_io.asset_placeflag import PlaceFlagCounterFlagEntry

from widebrim.engine.const import PATH_PACK_PLACE_NAME, PATH_TEXT_GOAL, PATH_TEXT_PLACE_NAME, RESOLUTION_NINTENDO_DS
from widebrim.engine.state.enum_mode import GAMEMODES

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController
    from widebrim.engine.anim.button import AnimatedButton
    from widebrim.madhatter.hat_io.asset_dat.place import HintCoin, TObjEntry, BgAni, EventEntry
    from widebrim.engine.anim.image_anim.image import AnimatedImageObject
    from pygame import Surface

from widebrim.engine.anim.fader import Fader
from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine.exceptions import FileInvalidCritical
from widebrim.engine.anim.font.static import generateImageFromString
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getClickableButtonFromPath, getTopScreenAnimFromPath, getTxt2String
from .const import *
from .animJump import AnimJumpHelper
from .tobjPopup import TObjPopup

# TODO - Tea event flag check against 0xffff
# TODO - Room behaviour reset to 0 in tea handler

class RoomPlayer(ScreenLayerNonBlocking):
    
    LAYTON_TRANSITION_PIXELS_PER_SECOND = 256
    POS_CENTER_TEXT_ROOM_TITLE  = (170,7)
    POS_CENTER_TEXT_OBJECTIVE   = (128,172)
    
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController):
        super().__init__()
        
        self.laytonState = laytonState
        self.screenController = screenController

        self.__isInteractable : bool = False

        self.__animMemberParty : List[Optional[AnimatedImageObject]] = []
        for indexParty in range(4):
            if len(NAME_ANIM_PARTY) > indexParty and len(POS_X_ANIM_PARTY) > indexParty:
                if indexParty < 2 or self.laytonState.saveSlot.partyFlag.getSlot(indexParty - 2):
                    self.__animMemberParty.append(getTopScreenAnimFromPath(laytonState, PATH_ANIM_PARTY, spawnAnimName=NAME_ANIM_PARTY[indexParty], pos=(POS_X_ANIM_PARTY[indexParty], POS_Y_ANIM_PARTY)))

        self.__animFirstTouch : Optional[AnimatedImageObject] = None
        if self.laytonState.isFirstTouchEnabled:
            self.__animFirstTouch = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_FIRSTTOUCH)
        
        self.__hasPhotoPieceInArea : bool = False
        self.__hasPhotoPieceInAreaBeenTaken : bool = False

        self.__enablePhotoPieceOverlay : bool = False
        self.__photoPieceMessage : Optional[AnimatedImageObject] = None
        self.__photoPieceNumbers : Optional[AnimatedImageObject] = None

        self.__animBackground   : List[Optional[AnimatedImageObject]]   = []
        self.__animEvent        : List[Optional[AnimatedImageObject]]   = []
        self.__animEventDraw    : List[bool]                            = []
        self.__eventTeaFlag     : List[int]                             = []

        self.__animMapArrow     : Optional[AnimatedImageObject]         = None
        self.__enableMapArrow   : bool                                  = False
        self.__animMapIcon      : Optional[AnimatedImageObject]         = getTopScreenAnimFromPath(laytonState, PATH_ANIM_MAPICON)
        self.__animNumberIcon : Optional[AnimatedImageObject]           = getTopScreenAnimFromPath(laytonState, PATH_ANIM_SOLVED_TEXT, pos=POS_SOLVED_TEXT)
        self.__animNumberFont : Optional[StaticImageAsNumericalFont]    = None

        if (animNumberFont := getTopScreenAnimFromPath(laytonState, PATH_ANIM_NUM_MAP_NUMBER)) != None:
            solved, _encountered = self.laytonState.saveSlot.getSolvedAndEncounteredPuzzleCount()
            self.__animNumberFont = StaticImageAsNumericalFont(animNumberFont, text=solved)
            self.__animNumberFont.setStride(animNumberFont.getDimensions()[0])
            self.__animNumberFont.setPos((72,11))

        self.__animTeaEventIcon : Optional[AnimatedImageObject] = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_TEAEVENT_ICON)
        self.__animEventStart : Optional[AnimatedImageObject] = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_ICON_BUTTONS)
        self.__animTouchIcon : Optional[AnimatedImageObject] = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_TOUCH_ICON, pos=POS_TOUCH_ICON)
        if self.__animTouchIcon != None and self.__animTouchIcon.setAnimationFromIndex(1):
            self.__animTouchIcon.setCurrentAnimationLoopStatus(False)

        self.__placeData : Optional[PlaceDataNds] = None

        self.__inMoveMode : bool = False
        self.__btnMoveMode : Optional[AnimatedButton] = getClickableButtonFromPath(laytonState, PATH_BTN_MOVEMODE, callback=self.__startMoveMode)
        self.__btnMenuMode : Optional[AnimatedButton] = getClickableButtonFromPath(laytonState, PATH_BTN_MENU_ICON, callback=self.__startMenuMode, unclickOnCallback=False)
        
        self.__tObjWindow           : Optional[TObjPopup]       = None

        # Not accurate parts
        self.__targetEvent          : Optional[Union[EventEntry, Exit]] = None
        self.__faderEventAnim       : Fader                     = Fader(500, initialActiveState=False)
        self.__positionEventAnim    : Optional[AnimJumpHelper]  = None
        self.__targetExit           : Optional[Exit]            = None
        self.__currentTsMapIndex : Optional[int]                = None
        
        self.__faderTiming          : Fader                     = Fader(500, initialActiveState=False)
        self.__hasTransitionedCompleted : bool                  = False

        self.__highlightedIndexExit : Optional[int]             = None
        self.__buttonsExit          : List[NullButton]          = []

        self.__textObjective        : Optional[Surface]         = None
        self.__textRoomTitle        : Optional[Surface]         = None
        self.__posObjective     = (0,0)
        self.__posRoomTitle     = (0,0)
        self.__currentMapPos    = (0,0)

        # Disgustingly inaccurate
        self.__imageExitOff : List[Optional[Surface]] = []
        self.__imageExitOn  : List[Optional[Surface]] = []
        for indexExitImage in range(8):
            if (exitImage := getBottomScreenAnimFromPath(laytonState, PATH_EXT_EXIT % indexExitImage)) != None:
                exitImage.setAnimationFromName("gfx")
                self.__imageExitOff.append(exitImage.getActiveFrame())
                exitImage.setAnimationFromName("gfx2")
                self.__imageExitOn.append(exitImage.getActiveFrame())
            else:
                self.__imageExitOff.append(None)
                self.__imageExitOn.append(None)

        if self.__hasAutoEvent():
            self.laytonState.setGameMode(GAMEMODES.DramaEvent)
            self.__disableInteractivity()
            self.doOnKill()

        elif self.__loadRoom():
            self.__loadPhotoPieceText()
            # TODO - Generate objective (goal) string text here
            self.screenController.fadeIn(callback=self.__enableInteractivity)

    def draw(self, gameDisplay):
        if self.__textRoomTitle != None:
            gameDisplay.blit(self.__textRoomTitle, self.__posRoomTitle, special_flags=BLEND_RGB_SUB)
        if self.__textObjective != None:
            gameDisplay.blit(self.__textObjective, self.__posObjective, special_flags=BLEND_RGB_SUB)

        if self.__enableMapArrow and self.__animMapArrow != None:
            self.__animMapArrow.draw(gameDisplay)
        
        for anim in self.__animMemberParty + self.__animBackground:
            if anim != None:
                anim.draw(gameDisplay)
        
        indexEventObj = 0
        for anim, canDraw, herbteaIndex in zip(self.__animEvent, self.__animEventDraw, self.__eventTeaFlag):
            if anim != None and canDraw:
                anim.draw(gameDisplay)
                
                if self.__animTeaEventIcon != None and (eventData := self.__placeData.getObjEvent(indexEventObj)) != None:
                    eventData : EventEntry
                    if eventData.idEvent >= LIMIT_ID_TEA_START or herbteaIndex != None:
                        x = eventData.bounding.x + ((eventData.bounding.width - self.__animTeaEventIcon.getDimensions()[0]) // 2)
                        self.__animTeaEventIcon.setPos((x, anim.getPos()[1] + POS_TEAEVENT_ICON_Y_OFFSET))
                        self.__animTeaEventIcon.draw(gameDisplay)
            indexEventObj += 1

        if self.__animNumberIcon != None:
            self.__animNumberIcon.draw(gameDisplay)
        if self.__animNumberFont != None:
            self.__animNumberFont.drawBiased(gameDisplay)

        # Stops being accurate here
        if self.__targetEvent != None and self.__animEventStart != None:
            self.__animEventStart.setPos(self.__positionEventAnim.getPosition(self.__faderEventAnim.getStrength()))
            self.__animEventStart.draw(gameDisplay)
        
        if self.__animMapIcon != None:
            if self.__targetExit != None and not(self.__hasTransitionedCompleted):
                if self.__placeData.bgMapId != self.__currentTsMapIndex:
                    targetPos = self.__targetExit.posTransition
                else:
                    targetPos = self.__placeData.posMap

                x = ((1 - self.__faderTiming.getStrength()) * self.__currentMapPos[0]) + (self.__faderTiming.getStrength() * targetPos[0])
                y = ((1 - self.__faderTiming.getStrength()) * self.__currentMapPos[1]) + (self.__faderTiming.getStrength() * targetPos[1])

                self.__animMapIcon.setPos((round(x), round(y)))
                self.__animMapIcon.draw(gameDisplay)

                if self.__faderTiming.getStrength() == 1.0:
                    self.__hasTransitionedCompleted = True
                    # Trying to minimise jump at end of transition
                    self.__doRoomTransition()
            else:
                self.__animMapIcon.draw(gameDisplay)
        
        if self.__inMoveMode:
            if self.__placeData != None and self.__targetExit == None and self.__targetEvent == None:
                if self.__highlightedIndexExit == None:
                    for indexExit in range(self.__placeData.getCountExits()):
                        exit = self.__placeData.getExit(indexExit)
                        buttonExit = self.__buttonsExit[indexExit]
                        if 0 <= exit.idImage < 8:
                            image = self.__imageExitOff[exit.idImage]
                            if image != None:
                                gameDisplay.blit(image, buttonExit.getPos())
                else:
                    exit = self.__placeData.getExit(self.__highlightedIndexExit)
                    buttonExit = self.__buttonsExit[self.__highlightedIndexExit]
                    if 0 <= exit.idImage < 8:
                        if buttonExit.getTargettedState():
                            image = self.__imageExitOn[exit.idImage]
                        else:
                            image = self.__imageExitOff[exit.idImage]

                        if image != None:
                            gameDisplay.blit(image, buttonExit.getPos())
        else:
            if self.__btnMoveMode != None:
                self.__btnMoveMode.draw(gameDisplay)
            if self.__btnMenuMode != None:
                self.__btnMenuMode.draw(gameDisplay)

        # TODO - Method to do this None check, its excessive. Also order of drawing and updating

        if self.__animTouchIcon != None:
            self.__animTouchIcon.draw(gameDisplay)
        
        if self.__tObjWindow != None:
            self.__tObjWindow.draw(gameDisplay)

        if self.__animFirstTouch != None and self.laytonState.isFirstTouchEnabled:
            self.__animFirstTouch.draw(gameDisplay)

        return super().draw(gameDisplay)

    def update(self, gameClockDelta):
        for anim in self.__animMemberParty + self.__animBackground + self.__animEvent:
            if anim != None:
                anim.update(gameClockDelta)

        if self.__animFirstTouch != None and self.laytonState.isFirstTouchEnabled:
            self.__animFirstTouch.update(gameClockDelta)
        
        if self.__animTeaEventIcon != None:
            self.__animTeaEventIcon.update(gameClockDelta)

        if self.__targetEvent != None:
            self.__faderEventAnim.update(gameClockDelta)
            if self.__animEventStart != None:
                self.__animEventStart.update(gameClockDelta)

        self.__faderTiming.update(gameClockDelta)

        if not(self.__inMoveMode):
            if self.__btnMoveMode != None:
                self.__btnMoveMode.update(gameClockDelta)
            if self.__btnMenuMode != None:
                self.__btnMenuMode.update(gameClockDelta)
        
        if self.__animTouchIcon != None:
            self.__animTouchIcon.update(gameClockDelta)

        if self.__tObjWindow != None:
            self.__tObjWindow.update(gameClockDelta)

        return super().update(gameClockDelta)
    
    def handleTouchEvent(self, event):

        def wasBoundingCollided(bounding, pos):
            if bounding.x <= pos[0] and bounding.y <= pos[1]:
                if (bounding.x + bounding.width) >= pos[0] and (bounding.y + bounding.height) >= pos[1]:
                    return True
            return False
        
        def getPressedEventIndex(pos) -> Optional[int]:
            if self.__placeData != None:
                for indexObjEvent in range(self.__placeData.getCountObjEvents()):
                    objEvent : EventEntry = self.__placeData.getObjEvent(indexObjEvent)
                    if wasBoundingCollided(objEvent.bounding, pos):
                        return indexObjEvent
            return None
        
        def getPressedExit(pos, immediateOnly = False) -> Optional[Exit]:
            for indexExit in range(self.__placeData.getCountExits()):
                exitEntry = self.__placeData.getExit(indexExit)
                if (immediateOnly and exitEntry.canBePressedImmediately()) or not(immediateOnly):
                    if wasBoundingCollided(exitEntry.bounding, boundaryTestPos):
                        return exitEntry
            return None

        if self.__tObjWindow != None:
            self.__tObjWindow.handleTouchEvent(event)
            return True

        if self.__isInteractable:

            boundaryTestPos = (event.pos[0], event.pos[1] - RESOLUTION_NINTENDO_DS[1])

            if self.laytonState.isFirstTouchEnabled:
                if event.type == MOUSEBUTTONUP:
                    self.laytonState.isFirstTouchEnabled = False
                return True

            # Hide touch cursor on press, in case something else is spawned
            if self.__animTouchIcon != None and event.type == MOUSEBUTTONDOWN:
                self.__animTouchIcon.setPos(POS_TOUCH_ICON)

            if self.__inMoveMode:
                for indexButton, button in enumerate(self.__buttonsExit):
                    self.__highlightedIndexExit = indexButton
                    if button.handleTouchEvent(event):
                        return True
                self.__highlightedIndexExit = None

            if self.__inMoveMode and event.type == MOUSEBUTTONDOWN:
                if (objExit := getPressedExit(boundaryTestPos)) != None:
                    self.__startExit(objExit)
                    return True
                self.__inMoveMode = False

            else:
                # TODO - Accurate button order
                if self.__btnMoveMode != None and self.__btnMoveMode.handleTouchEvent(event):
                    return True
                
                if self.__btnMenuMode != None and self.__btnMenuMode.handleTouchEvent(event):
                    return True

                # TODO - Event handling is not very accurate; just reuses code from previous room handler
                if event.type == MOUSEBUTTONDOWN and (objEventIndex := getPressedEventIndex(boundaryTestPos)) != None:
                    # TODO - Check photo flags
                    objEvent = self.__placeData.getObjEvent(objEventIndex)
                    idHerbtea = self.__eventTeaFlag[objEventIndex]
                    canSpawnEvent = True
                    if (eventInfo := self.laytonState.getEventInfoEntry(objEvent.idEvent)) != None:
                        # TODO - Fix this awful syntax, add convenience functions (similar code used elsewhere)
                        if eventInfo.typeEvent != 1 or not(self.laytonState.saveSlot.eventViewed.getSlot(eventInfo.indexEventViewedFlag)):
                            if eventInfo.typeEvent == 4 and (nzLstEntry := self.laytonState.getNazoListEntry(eventInfo.dataPuzzle)) != None:
                                if (puzzleData := self.laytonState.saveSlot.puzzleData.getPuzzleData(nzLstEntry.idExternal - 1)) != None and puzzleData.wasSolved:
                                    canSpawnEvent = False
                            
                            # TODO - Unk tea interaction, check if image attached
                            if canSpawnEvent:
                                self.__startEventSpawn((objEvent, idHerbtea))
                                return True
                
                if event.type == MOUSEBUTTONDOWN and self.__placeData != None:
                    for indexHint in range(self.__placeData.getCountHintCoin()):
                        if (hintCoin := self.__placeData.getObjHintCoin(indexHint)) != None:
                            hintCoin : HintCoin
                            if wasBoundingCollided(hintCoin.bounding, boundaryTestPos):
                                if not(self.laytonState.saveSlot.roomHintData.getRoomHintData(self.laytonState.getPlaceNum()).hintsFound[indexHint]):
                                    self.laytonState.saveSlot.roomHintData.getRoomHintData(self.laytonState.getPlaceNum()).hintsFound[indexHint] = True
                                    # TODO - Coin flip anim, this is just ported from old room handler
                                    self.laytonState.saveSlot.hintCoinEncountered += 1
                                    self.laytonState.saveSlot.hintCoinAvailable += 1
                                    logVerbose("Found a hint coin!", name="DramaEvent")

                                    if indexHint == 0 and self.laytonState.getPlaceNum() == 3:
                                        # Hardcoded behaviour to force the event after encountering first hint coin to play out
                                        self.laytonState.setGameMode(GAMEMODES.DramaEvent)
                                        self.laytonState.setEventId(10080)
                                        self.__disableInteractivity()
                                        self.screenController.fadeOut(callback=self.doOnKill)

                                    return True

                if event.type == MOUSEBUTTONDOWN and self.__placeData != None:
                    for indexTObj in range(self.__placeData.getCountObjText()):
                        if (tObj := self.__placeData.getObjText(indexTObj)) != None:
                            tObj : TObjEntry
                            if wasBoundingCollided(tObj.bounding, boundaryTestPos):
                                self.__startTObj(tObj.idChar, tObj.idTObj, False)
                                return True
                
                if event.type == MOUSEBUTTONDOWN and (objExit := getPressedExit(boundaryTestPos, immediateOnly=True)) != None:
                    self.__startExit(objExit)
                    return True
                
                if self.__animTouchIcon != None and event.type == MOUSEBUTTONDOWN and event.pos[1] >= RESOLUTION_NINTENDO_DS[1]:
                    self.__animTouchIcon.resetActiveAnim()
                    if self.__animTouchIcon.getActiveFrame != None:
                        width, height = self.__animTouchIcon.getDimensions()
                        self.__animTouchIcon.setPos((event.pos[0] - width // 2, event.pos[1] - height // 2))

        return super().handleTouchEvent(event)

    def __disableInteractivity(self):
        self.__isInteractable = False

    def __enableInteractivity(self):
        self.__isInteractable = True
    
    def __startMoveMode(self):
        self.__inMoveMode = not(self.__inMoveMode)
    
    def __startMenuMode(self):
        self.__disableInteractivity()
        self.laytonState.setGameMode(GAMEMODES.Bag)
        # TODO - Is next gamemode room?
        self.screenController.fadeOut(callback=self.doOnKill)

    def __callbackExitFromButton(self):
        self.__startExit(self.__placeData.getExit(self.__highlightedIndexExit))

    def __startTObj(self, idChar, idText, isFirstHintCoin):
        self.__disableInteractivity()
        self.__tObjWindow = TObjPopup(self.laytonState, self.screenController, idText, idChar, callback=self.__callbackEndTObj)

    def __callbackEndTObj(self):
        self.__tObjWindow = None
        self.__enableInteractivity()

    def __callbackEndTObjFirstHint(self):
        self.__callbackEndTObj()
        self.laytonState.setGameMode(GAMEMODES.DramaEvent)
        self.laytonState.setEventId(10080)
        self.screenController.fadeOut(callback=self.doOnKill)

    def __startEventSpawn(self, objEvent : Union[Tuple[EventEntry, Optional[int]], Exit]):
        self.__targetEvent = objEvent
        self.__disableInteractivity()
        
        isExclamation = True
        if type(objEvent) == Exit:
            idEvent = objEvent.spawnData
        else:
            objEvent, idHerbtea = objEvent
            if idHerbtea != None:
                idEvent = 30000 + (10 * idHerbtea)
            else:
                idEvent = objEvent.idEvent

        if 20000 > idEvent or 30000 <= idEvent:
            isExclamation = False
            
        else:
            if (evInf := self.laytonState.getEventInfoEntry(idEvent)) != None and evInf.dataPuzzle != None:
                if (nzLstEntry := self.laytonState.getNazoListEntry(evInf.dataPuzzle)) != None:
                    if (puzzleData := self.laytonState.saveSlot.puzzleData.getPuzzleData(nzLstEntry.idExternal - 1)) != None and puzzleData.wasSolved:
                        isExclamation = False
        
        # TODO - can boundings be backwards?
        boundingCenterX = objEvent.bounding.x + (objEvent.bounding.width // 2)
        boundingCenterY = objEvent.bounding.y + (objEvent.bounding.height // 2)

        initialPos = (boundingCenterX, boundingCenterY)
        if self.__animEventStart != None:
            if isExclamation:
                if self.__animEventStart.setAnimationFromName("1") and (surf := self.__animEventStart.getActiveFrame()) != None:
                    initialPos = (boundingCenterX - (surf.get_width() // 2), boundingCenterY - (surf.get_height() // 2))
            else:
                if self.__animEventStart.setAnimationFromName("2") and (surf := self.__animEventStart.getActiveFrame()) != None:
                    initialPos = (boundingCenterX - (surf.get_width() // 2), (objEvent.bounding.y - surf.get_height()) + 4)

        initialPos = (initialPos[0], RESOLUTION_NINTENDO_DS[1] + initialPos[1])
        self.__positionEventAnim = AnimJumpHelper(initialPos, isExclamation)
        self.__faderEventAnim.setDuration(500)
        self.__faderEventAnim.setCallback(self.__killActiveRoomPlayerEvent)

        # Warning: VERY high level
        self.laytonState.setEventIdBranching(idEvent)
        self.laytonState.setGameMode(GAMEMODES.DramaEvent)

    def __startExit(self, objExit : Exit):
        self.__disableInteractivity()

        if objExit.canSpawnEvent():
            if objExit.canTriggerExclamationPopup():
                self.__startEventSpawn(objExit)
            else:
                self.laytonState.setEventIdBranching(objExit.spawnData)
                self.laytonState.setGameMode(GAMEMODES.DramaEvent)
                self.screenController.fadeOut(callback=self.doOnKill)
            return

        if objExit.spawnData == 0x3f:
            self.laytonState.setGameMode(GAMEMODES.Nazoba)
            self.screenController.fadeOut(callback=self.doOnKill)
            return
        
        self.__targetExit = objExit
        # No evidence behind this but looks better
        self.__prepareNextPlace()
        self.__loadRoomData()

        if self.__targetExit.posTransition == (0,0):
            self.screenController.fadeOutMain(duration=100, callback=self.__doRoomTransition)
        else:
            # TODO - Issue if room data invalid...
            self.screenController.fadeOutMain(duration=100, callback=self.__moveLaytonIcon)

    def __moveLaytonIcon(self):
        # Different map - use transition position
        # Same map - use pos from place

        if self.__placeData != None:
            if self.__placeData.bgMapId != self.__currentTsMapIndex:
                targetPos = self.__targetExit.posTransition
            else:
                targetPos = self.__placeData.posMap

            self.__hasTransitionedCompleted = False
            distanceX = targetPos[0] - self.__currentMapPos[0]
            distanceY = targetPos[1] - self.__currentMapPos[1]
            distance = sqrt(distanceX ** 2 + distanceY ** 2)
            duration = (distance / RoomPlayer.LAYTON_TRANSITION_PIXELS_PER_SECOND) * 1000
        else:
            # TODO - This shouldn't happen, but what's the best way to safeguard? Throw error?
            duration = 1

        self.__faderTiming.setDuration(duration)
        self.__faderTiming.setActiveState(True)

    def __prepareNextPlace(self):
        self.laytonState.setRoomLoadBehaviour(0)
        self.__currentTsMapIndex = self.__placeData.bgMapId
        self.__currentMapPos = self.__placeData.posMap
        self.laytonState.setPlaceNum(self.__targetExit.spawnData)

    def __doRoomTransition(self):

        def loadRoomAfterFullFade():
            self.__loadRoom()
            self.screenController.fadeIn(callback=self.__enableInteractivity)

        if self.__hasAutoEvent():
            self.screenController.fadeOutSub(callback=self.doOnKill)
            self.laytonState.setGameMode(GAMEMODES.DramaEvent)
        else:
            # TODO - will be loaded twice, sorries
            if self.__loadRoomData():
                if self.__placeData.bgMapId != self.__currentTsMapIndex:
                    self.screenController.fadeOutSub(callback=loadRoomAfterFullFade)
                else:
                    self.__loadRoom()
                    self.screenController.fadeInMain(callback=self.__enableInteractivity)

    def __loadPhotoPieceText(self):
        photoPieceByte = self.laytonState.saveSlot.eventCounter.toBytes(outLength=128)[24]
        if 0 < photoPieceByte < 16:
            self.__enablePhotoPieceOverlay = True
            self.__photoPieceMessage = getTopScreenAnimFromPath(self.laytonState, PATH_ANIM_PIECE_MESSAGE, pos=POS_PIECE_MESSAGE)
            self.__photoPieceNumbers = getTopScreenAnimFromPath(self.laytonState, PATH_ANIM_NUM_PIECE_NUM)

    def __killActiveRoomPlayerEvent(self):
        self.screenController.fadeOut(duration=250, callback=self.doOnKill)

    def __loadRoomData(self) -> bool:

        def getPlaceData():
            namePlace = PATH_PACK_PLACE % (self.laytonState.getPlaceNum(), self.laytonState.saveSlot.roomSubIndex)
            if self.laytonState.getPlaceNum() < 40:
                output = self.laytonState.getFileAccessor().getPackedData(PATH_PLACE_A, namePlace)
            else:
                output = self.laytonState.getFileAccessor().getPackedData(PATH_PLACE_B, namePlace)
            
            if output == None:
                raise FileInvalidCritical()
            return output

        self.__calculateRoom()
        if (tempPlaceData := getPlaceData()) != None:
            placeData = PlaceDataNds()
            placeData.load(tempPlaceData)
            self.__placeData = placeData

            # TODO - Check if any entries for photo database here
            # TODO - Check if photo piece taken, set bools, unk camera check

            return True
        return False

    def __loadRoom(self):
        if self.__loadRoomData():

            self.__animBackground   = []
            self.__animEvent        = []
            self.__animEventDraw    = []
            self.__eventTeaFlag     = []
            self.__buttonsExit      = []

            # Remove trace of last state
            self.__targetEvent = None
            self.__targetExit = None
            self.__inMoveMode = False
            self.__highlightedIndexExit = None

            self.__textObjective = generateImageFromString(self.laytonState.fontEvent, getTxt2String(self.laytonState, PATH_TEXT_GOAL % self.laytonState.saveSlot.goal))
            self.__posObjective = (RoomPlayer.POS_CENTER_TEXT_OBJECTIVE[0] - self.__textObjective.get_width() // 2, RoomPlayer.POS_CENTER_TEXT_OBJECTIVE[1])
            
            # Is there a NO ROOM or similar fail string?
            if (titleText := self.laytonState.getFileAccessor().getPackedString(PATH_PACK_PLACE_NAME % self.laytonState.language.value, PATH_TEXT_PLACE_NAME % self.__placeData.idNamePlace)) != "":
                # TODO - String substituter
                self.__textRoomTitle = generateImageFromString(self.laytonState.fontEvent, titleText)
                self.__posRoomTitle = (RoomPlayer.POS_CENTER_TEXT_ROOM_TITLE[0] - self.__textRoomTitle.get_width() // 2, RoomPlayer.POS_CENTER_TEXT_ROOM_TITLE[1])
                self.laytonState.namePlace = titleText

            self.screenController.setBgMain(PATH_PLACE_BG % self.__placeData.bgMainId)
            self.screenController.setBgSub(PATH_PLACE_MAP % self.__placeData.bgMapId)

            if self.__animMapIcon != None and (surf := self.__animMapIcon.getActiveFrame()) != None:
                self.__animMapIcon.setPos(self.__placeData.posMap)

            for indexBackgroundAnim in range(self.__placeData.getCountObjBgEvent()):
                if (bgAni := self.__placeData.getObjBgEvent(indexBackgroundAnim)) != None:
                    bgAni : BgAni
                    if (anim := getBottomScreenAnimFromPath(self.laytonState, PATH_ANIM_BGANI % bgAni.name, pos=bgAni.pos)) != None:
                        self.__animBackground.append(anim)
                        
            for indexObjEvent in range(self.__placeData.getCountObjEvents()):
                self.__eventTeaFlag.append(None)
                objEvent = self.__placeData.getObjEvent(indexObjEvent)
                objEvent : EventEntry

                # TODO - What is the second byte of spawnData used for?
                if objEvent.idImage != 0:
                    if (eventAsset := getBottomScreenAnimFromPath(self.laytonState, PATH_EXT_EVENT % (objEvent.idImage & 0xff))) != None:
                        eventAsset.setPos((objEvent.bounding.x, objEvent.bounding.y + RESOLUTION_NINTENDO_DS[1]))
                    self.__animEvent.append(eventAsset)

                    if (eventInfo := self.laytonState.getEventInfoEntry(objEvent.idEvent)) != None:
                        # TODO - Fix this awful syntax, add convenience functions (similar code used elsewhere)
                        if eventInfo.typeEvent == 1 and self.laytonState.saveSlot.eventViewed.getSlot(eventInfo.indexEventViewedFlag):
                            self.__animEventDraw.append(False)
                        elif eventInfo.typeEvent == 4 and (nzLstEntry := self.laytonState.getNazoListEntry(eventInfo.dataPuzzle)) != None:
                            if (puzzleData := self.laytonState.saveSlot.puzzleData.getPuzzleData(nzLstEntry.idExternal - 1)) != None and puzzleData.wasSolved:
                                self.__animEventDraw.append(False)
                            else:
                                self.__animEventDraw.append(True)
                        else:
                            self.__animEventDraw.append(True)
                        
                        if self.__animEventDraw[indexObjEvent] and self.laytonState.getRoomLoadBehaviour() != 2:
                            idEvent = objEvent.idEvent
                            if LIMIT_ID_PUZZLE_START <= idEvent < LIMIT_ID_TEA_START:
                                # Event depends on puzzle, so check if puzzle was solved
                                if (nazoListEntry := self.laytonState.getNazoListEntry(eventInfo.dataPuzzle)) != None:
                                    # TODO - Isn't this wrong?
                                    if (puzzleData := self.laytonState.saveSlot.puzzleData.getPuzzleData(nazoListEntry.idExternal)) != None:
                                        if puzzleData.wasSolved:
                                            idEvent += 2

                            herbteaEntry = self.laytonState.dlzHerbteaEvent.searchForEntry(idEvent)
                            if herbteaEntry != None and not(self.laytonState.saveSlot.minigameTeaState.flagCorrect.getSlot(herbteaEntry.idHerbteaFlag)):
                                if self.laytonState.getRoomLoadBehaviour() == 1:
                                    self.__eventTeaFlag[indexObjEvent] = herbteaEntry.idHerbteaFlag
                                else:
                                    countTeaCorrect = 0
                                    for indexHerbteaFlag in range(COUNT_HERBTEA):
                                        if self.laytonState.saveSlot.minigameTeaState.flagCorrect.getSlot(indexHerbteaFlag):
                                            countTeaCorrect += 1

                                    skipRemainingPossibilites = False
                                    # Random is not accurate. Algorithm is known but simplified, no guarantee random will be same
                                    if COUNT_HERBTEA_LIMIT < countTeaCorrect:
                                        # TODO - Probability not certain, bitwise operations complicate things
                                        if randint(1,2) == 1:
                                            self.__eventTeaFlag[indexObjEvent] = herbteaEntry.idHerbteaFlag
                                            self.laytonState.setRoomLoadBehaviour(1)
                                            skipRemainingPossibilites = True

                                    if not(skipRemainingPossibilites):
                                        # TODO - Checks if the save slot is completed and modifies probabilities
                                        if not(self.laytonState.saveSlot.isComplete):
                                            probability = 5
                                        else:
                                            probability = 100
                                        
                                        if randint(1,probability) == 1:
                                            self.__eventTeaFlag[indexObjEvent] = herbteaEntry.idHerbteaFlag
                                            self.laytonState.setRoomLoadBehaviour(1)
                                        else:
                                            self.laytonState.setRoomLoadBehaviour(2)

                else:
                    self.__animEvent.append(None)
                    self.__animEventDraw.append(False)
            
            # TODO - Exits, and first strange function
            for indexExit in range(self.__placeData.getCountExits()):
                exit : Exit = self.__placeData.getExit(indexExit)
                pos = (exit.bounding.x, exit.bounding.y + RESOLUTION_NINTENDO_DS[1])
                posEnd = (pos[0] + exit.bounding.width, pos[1] + exit.bounding.height)
                self.__buttonsExit.append(NullButton(pos, posEnd, callback=self.__callbackExitFromButton))

            self.__setupGuideArrows()
            return True
        return False

    def __setupGuideArrows(self):
        if self.__animMapArrow == None:
            self.__animMapArrow = getTopScreenAnimFromPath(self.laytonState, PATH_ANIM_MAP_ARROW)
        
        x = 0
        y = 0
        targetImage = None
        self.__enableMapArrow = False
        self.laytonState.loadSubmapInfo()
        for indexEventViewed in EVENT_VIEWED_MAP_ARROW:
            if (submapEntry := self.laytonState.getSubmapInfoEntry(indexEventViewed)) != None:
                self.__enableMapArrow = True
                x,y = submapEntry.pos
                targetImage = submapEntry.indexImage
                if submapEntry.indexImage == 0:
                    y += 14
                elif submapEntry.indexImage == 5:
                    y -= 14

        self.laytonState.unloadSubmapInfo()
                
        if self.__enableMapArrow and self.__animMapArrow != None:
            if self.__animMapArrow.setAnimationFromName(str(targetImage)):
                if (imageMapArrow := self.__animMapArrow.getActiveFrame()) != None:
                    self.__animMapArrow.setPos((x - imageMapArrow.get_width() // 2,y - imageMapArrow.get_height() // 2))
            else:
                self.__enableMapArrow = False

    def __calculateChapter(self):

        storyFlag = self.laytonState.dbStoryFlag
        saveSlot = self.laytonState.saveSlot

        indexStoryFlag = storyFlag.getIndexFromChapter(saveSlot.chapter)
        if indexStoryFlag == -1:
            # The game apparently does this too
            # Setting chapter and goal to 510 after passing event 15250 causes the chapter to reset to 390, like the game.
            indexStoryFlag = 0

        while indexStoryFlag < 256:

            storyFlagEntry = storyFlag.getGroupAtIndex(indexStoryFlag)

            for indexSubFlag in range(8):
                subFlag = storyFlagEntry.getFlag(indexSubFlag)
                if subFlag.type == 2:

                    nzLstEntry = self.laytonState.getNazoListEntry(subFlag.param)
                    if nzLstEntry != None and not(saveSlot.puzzleData.getPuzzleData(nzLstEntry.idExternal - 1).wasSolved):
                        saveSlot.chapter = storyFlagEntry.getChapter()
                        return

                elif subFlag.type == 1:
                    if not(saveSlot.storyFlag.getSlot(subFlag.param)):
                        saveSlot.chapter = storyFlagEntry.getChapter()
                        return

            indexStoryFlag += 1

    def __calculateRoom(self):

        def checkEventCounter(placeFlagEntry : PlaceFlagCounterFlagEntry):
            if placeFlagEntry.indexEventCounter > 127:
                return False

            eventCounterEncoded = self.laytonState.saveSlot.eventCounter.toBytes(outLength=128)
            
            output = False
            if placeFlagEntry.decodeMode == 2:
                if placeFlagEntry.unk1 <= eventCounterEncoded[placeFlagEntry.indexEventCounter]:
                    output = True
            elif placeFlagEntry.decodeMode == 1:
                if eventCounterEncoded[placeFlagEntry.indexEventCounter] - placeFlagEntry.unk1 != 0:
                    output = True
            elif placeFlagEntry.decodeMode == 0:
                if eventCounterEncoded[placeFlagEntry.indexEventCounter] - placeFlagEntry.unk1 == 0:
                    output = True
            return output

        placeFlag = self.laytonState.dbPlaceFlag
        indexRoom = self.laytonState.getPlaceNum()

        self.__calculateChapter()

        indexSubRoom = 0
        for proposedSubRoom in range(1,16):
            placeFlagEntry = placeFlag.getEntry(indexRoom).getChapterEntry(proposedSubRoom)
            placeFlagCounterEntry = placeFlag.getEntry(indexRoom).getCounterEntry(proposedSubRoom)
            if placeFlagEntry.isEmpty():
                break

            chapter = self.laytonState.saveSlot.chapter
            workingSubRoom = indexSubRoom
            if placeFlagEntry.chapterStart <= chapter and placeFlagEntry.chapterEnd >= chapter:
                workingSubRoom = proposedSubRoom

                if placeFlagCounterEntry.indexEventCounter != 0:
                    workingSubRoom = indexSubRoom
                    if checkEventCounter(placeFlagCounterEntry):
                        workingSubRoom = proposedSubRoom

            indexSubRoom = workingSubRoom
        
        self.laytonState.saveSlot.roomSubIndex = indexSubRoom

    def __hasAutoEvent(self) -> bool:

        def getEventInfoEventViewedIdFlag(eventId):
            eventInfo = self.laytonState.getEventInfoEntry(eventId)
            if eventInfo == None:
                return eventInfo
            return eventInfo.indexEventViewedFlag

        def hasAutoEventBeenExecuted(eventId):
            eventViewedFlag = getEventInfoEventViewedIdFlag(eventId)
            if eventViewedFlag != None:
                return self.laytonState.saveSlot.eventViewed.getSlot(eventViewedFlag)
            return False

        autoEvent = self.laytonState.dbAutoEvent

        autoEventId = None
        for entryId in range(8):
            entry = autoEvent.getEntry(self.laytonState.getPlaceNum()).getSubPlaceEntry(entryId)
            if entry != None and entry.chapterStart <= self.laytonState.saveSlot.chapter <= entry.chapterEnd:
                autoEventId = entry.idEvent
        
        if autoEventId != None:
            # TODO - Can there be multiple autoevents that pass the above check?
            if hasAutoEventBeenExecuted(autoEventId):
                return False
            
            repeatId = getEventInfoEventViewedIdFlag(autoEventId)
            if repeatId == self.laytonState.saveSlot.idHeldAutoEvent:
                # TODO - Figure out exactly how game does this check. Hack implemented in setter for place which works around loops caused by
                # repeating autoevents. Current implementation assumes room set will be executed, which could do weird stuff in longer event chains
                return False

            self.laytonState.setEventId(autoEventId)
            return True
        return False