from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from widebrim.engine.anim.image_anim.imageAsNumber import StaticImageAsNumericalFont
from widebrim.gamemodes.jiten.hitbox import JitenHitbox
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.gamemodes.mystery.const import PATH_ANIM_BUTTON_CANCEL
from widebrim.engine.anim.button import AnimatedButton, NullButton
from widebrim.engine.anim.image_anim.image import AnimatedImageObject
from widebrim.engine.anim.fader import Fader
from widebrim.engine.state.enum_mode import GAMEMODES

from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getButtonFromPath, getClickableButtonFromPath, getTopScreenAnimFromPath
from .const import *

from pygame import Surface

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController
    from widebrim.madhatter.hat_io.asset_sav import PuzzleData
    from widebrim.madhatter.hat_io.asset_dlz.nz_lst import DlzEntryNzLst

def lerp(valSource, valDest, strength : float) -> float:
    diff = valDest - valSource
    return valSource + (diff * strength)

# TODO - WiFi date, callback and scrollbar

class JitenPlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController, callbackOnTerminate : Optional[callable] = None):
        super().__init__()

        def addIfNotNone(dest : List, obj):
            if obj != None:
                dest.append(obj)
        
        def getHitbox(pos, dimensions, callback=None) -> NullButton:
            pos = (pos[0], pos[1] + RESOLUTION_NINTENDO_DS[1])
            posEnd = (pos[0] + dimensions[0], pos[1] + dimensions[1])
            return NullButton(pos, posEnd, callback=callback)

        self.__laytonState      = laytonState
        self.__screenController = screenController
        self.__sourceGameMode   = self.__laytonState.getGameMode()

        self.__inFavouriteMode              : bool  = False
        self.__lastSelectedFavouriteIndex   : int   = 0
        self.__lastSelectedNormalIndex      : int   = 0
        self.__textRendererLocation     : StaticTextHelper              = StaticTextHelper(laytonState.fontEvent)
        self.__textRendererType         : StaticTextHelper              = StaticTextHelper(laytonState.fontEvent)
        self.__textRendererName         : StaticTextHelper              = StaticTextHelper(laytonState.fontQ)
        self.__animPreview              : Optional[AnimatedImageObject] = None
        self.__isInteractive            : bool = False

        self.__drawables                : List[AnimatedImageObject]     = []
        self.__buttons                  : List[AnimatedButton]          = []
        self.__buttonsHitbox            : List[NullButton]              = []
        self.__buttonsFavouriteHitbox   : List[NullButton]              = []
        self.__buttonsTab               : List[NullButton]              = []
        self.__ids                      : List[int]                     = []

        self.__animModeSelect : Optional[AnimatedImageObject]   = None
        self.__animPrize : Optional[AnimatedImageObject]        = None
        self.__animHintbox : Optional[AnimatedImageObject]      = None
        self.__animShared : Optional[AnimatedImageObject]       = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_BTN_ALL)

        self.__btnUpSlow    : Optional[AnimatedButton] = getButtonFromPath(laytonState, PATH_ANIM_BTN_ALL, self.__callbackOnScrollButtonFinish, NAME_ANIM_JITEN_BTN_UP_OFF, NAME_ANIM_JITEN_BTN_UP_ON, pos=POS_BTN_UP, customDimensions=DIM_BTN_MOVE)
        self.__btnUpFast    : Optional[AnimatedButton] = getButtonFromPath(laytonState, PATH_ANIM_BTN_ALL, self.__callbackOnScrollButtonFinish, NAME_ANIM_JITEN_BTN_UP_MANY_OFF, NAME_ANIM_JITEN_BTN_UP_MANY_ON, pos=POS_BTN_UP_MANY, customDimensions=DIM_BTN_MOVE)
        self.__btnDownSlow  : Optional[AnimatedButton] = getButtonFromPath(laytonState, PATH_ANIM_BTN_ALL, self.__callbackOnScrollButtonFinish, NAME_ANIM_JITEN_BTN_DOWN_OFF, NAME_ANIM_JITEN_BTN_DOWN_ON, pos=POS_BTN_DOWN, customDimensions=DIM_BTN_MOVE)
        self.__btnDownFast  : Optional[AnimatedButton] = getButtonFromPath(laytonState, PATH_ANIM_BTN_ALL, self.__callbackOnScrollButtonFinish, NAME_ANIM_JITEN_BTN_DOWN_MANY_OFF, NAME_ANIM_JITEN_BTN_DOWN_MANY_ON, pos=POS_BTN_DOWN_MANY, customDimensions=DIM_BTN_MOVE)
        self.__btnSolve     : Optional[AnimatedButton] = None

        self.__textJitenNum : Optional[StaticImageAsNumericalFont]  = None
        self.__textUpperNum : Optional[StaticImageAsNumericalFont]  = None

        self.__animJitenNum : Optional[AnimatedImageObject]         = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_NUM_ARC)
        if self.__animJitenNum != None:
            self.__textJitenNum = StaticImageAsNumericalFont(self.__animJitenNum)
        if (anim := getTopScreenAnimFromPath(laytonState, PATH_ANIM_NUM)) != None:
            self.__textUpperNum = StaticImageAsNumericalFont(anim, stride=6, usePadding=True)

        if laytonState.getGameModeNext() == GAMEMODES.JitenWiFi:
            # TODO - Save game to source slot, display message if save failed
            pass

        # Setup shared buttons (navigation, solve and exit)
        addIfNotNone(self.__buttons, self.__btnUpSlow)
        addIfNotNone(self.__buttons, self.__btnUpFast)
        addIfNotNone(self.__buttons, self.__btnDownSlow)
        addIfNotNone(self.__buttons, self.__btnDownFast)
        if self.__sourceGameMode == GAMEMODES.JitenWiFi:
            self.__btnSolve = getButtonFromPath(laytonState, PATH_ANIM_BTN_ALL, self.__callbackOnSolvePressed, NAME_ANIM_JITEN_BTN_SOLVE_OFF_WIFI, NAME_ANIM_JITEN_BTN_SOLVE_ON_WIFI, pos=POS_BTN_SOLVE, customDimensions=DIM_BTN_SOLVE)
            addIfNotNone(self.__buttons, getClickableButtonFromPath(laytonState, PATH_ANIM_BUTTON_CANCEL, self.__callbackOnExit, unclickOnCallback=False))
        else:
            self.__btnSolve = getButtonFromPath(laytonState, PATH_ANIM_BTN_ALL, self.__callbackOnSolvePressed, NAME_ANIM_JITEN_BTN_SOLVE_OFF, NAME_ANIM_JITEN_BTN_SOLVE_ON, pos=POS_BTN_SOLVE, customDimensions=DIM_BTN_SOLVE)
            addIfNotNone(self.__buttons, getClickableButtonFromPath(laytonState, PATH_ANIM_BTN_ALL, self.__callbackOnExit, animOff=NAME_ANIM_JITEN_BTN_ALT_CLOSE_OFF, animOn=NAME_ANIM_JITEN_BTN_ALT_CLOSE_CLICK, animClick=NAME_ANIM_JITEN_BTN_ALT_CLOSE_CLICK, customDimensions=DIM_BTN_CLOSE, pos=POS_BTN_CLOSE, unclickOnCallback=False))

        # HACK - Weird positioning
        self.__textRendererLocation.setPos((POS_TEXT_LOCATION[0], POS_TEXT_LOCATION[1] + 2))
        self.__textRendererName.setPos((0, POS_Y_TEXT_NAME))
        self.__textRendererType.setPos((POS_TEXT_TYPE[0], POS_TEXT_TYPE[1] + 2))

        # TODO - Scroll
        # Generate hitboxes for selecting puzzles
        x = POS_CORNER_HITBOX_SELECT[0]
        y = POS_CORNER_HITBOX_SELECT[1]
        for _indexHitbox in range(COUNT_DISPLAY):
            self.__buttonsHitbox.append(getHitbox((x,y), SIZE_HITBOX_SELECT, callback=self.__callbackOnHitboxPress))
            y += BIAS_HITBOX_SELECT_Y

        if self.__sourceGameMode == GAMEMODES.JitenWiFi:
            # Setup BG and covers for WiFi mode
            self.__screenController.setBgMain(PATH_BG_MAIN_WIFI)
            self.__screenController.setBgSub(PATH_BG_SUB_WIFI.replace("?", laytonState.language.value))
            addIfNotNone(self.__drawables, getBottomScreenAnimFromPath(self.__laytonState, PATH_ANIM_COVER_WIFI_1, namePosVar=ANIM_VAR_POS_TAG_JITEN_GUARD))
            addIfNotNone(self.__drawables, getBottomScreenAnimFromPath(self.__laytonState, PATH_ANIM_COVER_WIFI_2, namePosVar=ANIM_VAR_POS_TAG_JITEN_GUARD))
        else:
            # Setup BG and covers for normal mode
            self.__screenController.setBgMain(PATH_BG_MAIN)
            self.__screenController.setBgSub(PATH_BG_SUB % laytonState.language.value)
            
            self.__buttonsTab.append(getHitbox(POS_BTN_TO_FAV, DIM_BTN_TO_FAVOURITES, callback=self.__switchToFavourites))
            self.__buttonsTab.append(getHitbox(POS_BTN_FROM_FAV, DIM_BTN_FROM_FAVOURITES, callback=self.__switchToAll))
            self.__animModeSelect = getBottomScreenAnimFromPath(self.__laytonState, PATH_ANIM_TABS, namePosVar=ANIM_VAR_POS_TAG_JITEN_GUARD)
            self.__animPrize = getTopScreenAnimFromPath(self.__laytonState, PATH_ANIM_PRIZE, pos=POS_ANIM_PRIZE)    # TODO - Spawn anim index
            
            addIfNotNone(self.__drawables, getBottomScreenAnimFromPath(self.__laytonState, PATH_ANIM_COVER, namePosVar=ANIM_VAR_POS_TAG_JITEN_GUARD))
            addIfNotNone(self.__drawables, self.__animModeSelect)
            addIfNotNone(self.__drawables, getBottomScreenAnimFromPath(self.__laytonState, PATH_ANIM_INTRO_TEXT, pos=POS_ANIM_TITLE))

            # TODO - Unk button 5
            self.__animHintbox = getTopScreenAnimFromPath(self.__laytonState, PATH_ANIM_HINT)

            x = POS_CORNER_FAVOURITE[0]
            y = POS_CORNER_FAVOURITE[1]
            for _indexFavHitbox in range(COUNT_DISPLAY):
                self.__buttonsFavouriteHitbox.append(getHitbox((x,y), SIZE_HITBOX_FAVOURITE, callback=self.__callbackOnFavouritePress))
                y += BIAS_HITBOX_SELECT_Y

            # TODO - Question logo is fetched here and writes some save flags (probably new menu flag)

        # TODO - Not accurate. More scalable approach would be to store closest index and percent to next
        self.__scrollY                      = 0
        self.__indexOverlay : Optional[int] = None
        self.__prevScrollY                  = 0
        self.__indexScrollTop               = 0
        self.__lastScrollSpeed : int        = 0
        self.__hitboxes : List[JitenHitbox] = []
        self.__animTimer                    = Fader(0, initialActiveState=False)
        self.__indexButtonHit               = 0
        self.__loadedExternalPuzzleId       = 0
        self.__surfaceJitenSelectOverlay    = Surface((SIZE_BOX_SELECT_OVERLAY[0], BOUNDS_Y_SELECT_BOX_MAX - BOUNDS_Y_SELECT_BOX_MIN)).convert_alpha()
        self.__surfaceSelectBox             = Surface(SIZE_BOX_SELECT_OVERLAY).convert_alpha()
        self.__surfaceSelectBox.fill((COLOR_BOX_SELECT_OVERLAY[0], COLOR_BOX_SELECT_OVERLAY[1], COLOR_BOX_SELECT_OVERLAY[2], ALPHA_SELECT_OVERLAY))

        self.__canBeSolved : bool           = False

        self.__getSavedTabLocation()
        self.__loadTab()
        self.__screenController.fadeIn(callback=self.__enableInteractivity)

    def __loadTab(self):
        # accuracy in shambles

        self.__indexScrollTop = 0
        if self.__sourceGameMode == GAMEMODES.JitenWiFi:
            self.__getIds()
        else:
            if self.__inFavouriteMode:
                self.__getFavouriteIds()
                if self.__animModeSelect != None:
                    self.__animModeSelect.setAnimationFromName(NAME_ANIM_TAG_TAB_PICKS)
            else:
                self.__getIds()
                if self.__animModeSelect != None:
                    self.__animModeSelect.setAnimationFromName(NAME_ANIM_TAG_TAB_ALL)

    def __getSavedTabLocation(self):
        if self.__sourceGameMode == GAMEMODES.JitenWiFi:
            self.__lastSelectedNormalIndex = self.__laytonState.getLastJitenWiFiExternal()
        else:
            self.__lastSelectedNormalIndex = self.__laytonState.getLastJitenNazoExternal()
            self.__lastSelectedFavouriteIndex = self.__laytonState.getLastJitenFavouriteExternal()

    def __commitTabLocation(self):
        if self.__sourceGameMode == GAMEMODES.JitenWiFi:
            self.__laytonState.setLastJitenWiFiExternal(self.__lastSelectedNormalIndex)
        else:
            self.__laytonState.setLastJitenNazoExternal(self.__lastSelectedNormalIndex)
            self.__laytonState.setLastJitenFavouriteExternal(self.__lastSelectedFavouriteIndex)

    def __getIds(self):
        if self.__sourceGameMode == GAMEMODES.JitenWiFi:
            self.__getWiFiIds()
        else:
            self.__getNormalIds()

    def __selectAndCalculateScrollY(self):
        targetIdExternal = 0
        targetIndex = 0

        if self.__inFavouriteMode:
            targetIdExternal = self.__lastSelectedFavouriteIndex
        else:
            targetIdExternal = self.__lastSelectedNormalIndex

        if targetIdExternal in self.__ids:
            targetIndex = self.__ids.index(targetIdExternal)
        else:
            for indexId, id in enumerate(self.__ids):
                targetIndex = indexId
                if id > targetIdExternal:
                    break

            if len(self.__ids) > 0:
                targetIdExternal = self.__ids[targetIndex]
        
        if self.__inFavouriteMode:
            self.__lastSelectedFavouriteIndex = targetIdExternal
        else:
            self.__lastSelectedNormalIndex = targetIdExternal

        if targetIndex >= len(self.__ids):
            # If this tab is empty, reset scrollY
            self.__applyScrollOffset(0)
        else:
            # Else, select the puzzle from this tab and keep going
            self.__applyScrollOffset(targetIndex * BIAS_HITBOX_SELECT_Y)
        
        # Update selection to ensure correct puzzle highlighted
        self.__updateSelectedPuzzle()

    def __getFavouriteIds(self):
        self.__ids = []
        self.__hitboxes = []
        indexHitbox = 0
        for indexExternal in range(1, 0x9a):
            puzzleData =  self.__laytonState.saveSlot.puzzleData.getPuzzleData(indexExternal - 1)
            if puzzleData != None and (puzzleData.wasEncountered or puzzleData.wasSolved) and puzzleData.wasPicked:
                self.__ids.append(indexExternal)
                self.__hitboxes.append(JitenHitbox(self.__laytonState, indexExternal, indexHitbox, self.__animShared, self.__animJitenNum, self.__textJitenNum, self.__sourceGameMode, self.__surfaceJitenSelectOverlay))
                indexHitbox += 1
        self.__selectAndCalculateScrollY()

    def __getNormalIds(self):
        # TODO - Add engine module for addressing puzzle data, it's all over the place
        # TODO - Add story constant, this is shared across engine
        self.__ids = []
        self.__hitboxes = []
        indexHitbox = 0
        for indexExternal in range(1, 0x9a):
            puzzleData =  self.__laytonState.saveSlot.puzzleData.getPuzzleData(indexExternal - 1)
            if puzzleData != None and puzzleData.wasEncountered or puzzleData.wasSolved:
                self.__ids.append(indexExternal)
                self.__hitboxes.append(JitenHitbox(self.__laytonState, indexExternal, indexHitbox, self.__animShared, self.__animJitenNum, self.__textJitenNum, self.__sourceGameMode, self.__surfaceJitenSelectOverlay))
                indexHitbox += 1
        self.__selectAndCalculateScrollY()

    def __getWiFiIds(self):
        # NOTE - WiFi mode, like the binary, switches to INTERNAL IDs. Don't get this mixed up (devs make life hard)
        self.__ids = []
        self.__hitboxes = []
        indexHitbox = 0
        for indexWiFiPuzzle in range(self.__laytonState.wiFiData.getCountEntries()):
            entry = self.__laytonState.wiFiData.getEntry(indexWiFiPuzzle)
            # Game doesn't do these checks but we might as well
            if entry.idInternal != 0 and self.__laytonState.getNazoListEntry(entry.idInternal) != None:
                self.__ids.append(entry.idInternal)
                self.__hitboxes.append(JitenHitbox(self.__laytonState, entry.idInternal, indexHitbox, self.__animShared, self.__animJitenNum, self.__textJitenNum, self.__sourceGameMode, self.__surfaceJitenSelectOverlay))
                indexHitbox += 1
        self.__selectAndCalculateScrollY()

    def __enableInteractivity(self):
        self.__isInteractive = True

    def __disableInteractivity(self):
        self.__isInteractive = False

    def __switchToFavourites(self):
        if not(self.__inFavouriteMode):
            self.__inFavouriteMode = True
            self.__loadTab()

    def __switchToAll(self):
        if self.__inFavouriteMode:
            self.__inFavouriteMode = False
            self.__loadTab()

    def __updateSelectedPuzzle(self):
        
        def generateGraphics(nzLstEntry):
            if nzLstEntry != None:
                self.__indexOverlay = self.__ids.index(puzzleId)

                self.__laytonState.setPuzzleId(nzLstEntry.idInternal)
                if self.__laytonState.loadCurrentNazoData():
                    nazoData = self.__laytonState.getNazoData()
                    nazoType = nazoData.idHandler
                    if nazoType == 0x23:
                        nazoType = 0x16
                    
                    textType = self.__laytonState.getFileAccessor().getPackedString(PATH_PACK_JITEN.replace("?", self.__laytonState.language.value), PATH_TEXT_NAZO_TYPE % nazoType)
                    self.__textRendererType.setText(textType[0:min(len(textType), 64)])

                    # TODO - Unk validation check (2_Nazo_ValidateAndGetUnkData)
                    
                    if puzzleData.enableNazoba:
                        textLocation = self.__laytonState.getFileAccessor().getPackedString(PATH_PACK_JITEN.replace("?", self.__laytonState.language.value), PATH_TEXT_JITEN_MISSING)
                    else:
                        textLocation = self.__laytonState.getFileAccessor().getPackedString(PATH_PACK_JITEN.replace("?", self.__laytonState.language.value), PATH_TEXT_JITEN_PLACE % nazoData.indexPlace)

                    # TODO - madhatter needs nazoData variable scope changes
                    self.__textRendererLocation.setText(textLocation[0:min(len(textLocation), 64)])
                    self.__textRendererName.setText(nazoData.getTextName()[0:min(len(nazoData.getTextName()), 64)])
        
                self.__animPreview = getTopScreenAnimFromPath(self.__laytonState, PATH_ANIM_PREVIEW % nzLstEntry.idInternal, pos=POS_ANIM_PREVIEW)

            if self.__animPrize != None:
                if not(puzzleData.wasSolved):
                    self.__animPrize.setAnimationFromIndex(4)
                elif puzzleData.levelDecay == 2:
                    self.__animPrize.setAnimationFromIndex(3)
                elif puzzleData.levelDecay == 1:
                    self.__animPrize.setAnimationFromIndex(2)
                else:
                    self.__animPrize.setAnimationFromIndex(1)

        if self.__sourceGameMode != GAMEMODES.JitenWiFi:
            if self.__inFavouriteMode:
                puzzleId = self.__lastSelectedFavouriteIndex
            else:
                puzzleId = self.__lastSelectedNormalIndex

            # TODO - Text renderers and preview will be voided before check, since game does it in awkward way (and can't decide when to use stack)
            if puzzleId != 0 and puzzleId in self.__ids:
                nzLstEntry = self.__laytonState.getNazoListEntryByExternal(puzzleId)

                # Separate the overlay index to prevent tabs from interfering with intended behaviour
                if nzLstEntry != None:
                    self.__indexOverlay = self.__ids.index(puzzleId)
                else:
                    self.__indexOverlay = None

                if puzzleId != self.__loadedExternalPuzzleId:
                    self.__loadedExternalPuzzleId = puzzleId
                    puzzleData = self.__laytonState.saveSlot.puzzleData.getPuzzleData(puzzleId - 1)
                    self.__canBeSolved = puzzleData.wasSolved
                    generateGraphics(nzLstEntry)
            else:
                self.__indexOverlay = None

        else:
            # Already validated (HACK)
            if self.__lastSelectedNormalIndex != 0 and self.__lastSelectedNormalIndex != self.__loadedExternalPuzzleId:
                self.__loadedExternalPuzzleId = self.__lastSelectedNormalIndex
                self.__laytonState.setPuzzleId(self.__lastSelectedNormalIndex)
                self.__canBeSolved = True
                self.__indexOverlay = self.__ids.index(self.__lastSelectedNormalIndex)

    def __callbackOnSolvePressed(self):
        self.__disableInteractivity()
        self.__commitTabLocation()
        self.__laytonState.setGameModeNext(self.__sourceGameMode)
        self.__laytonState.setGameMode(GAMEMODES.Puzzle)
        self.__screenController.fadeOut(callback=self.doOnKill)

    def __callbackOnExit(self):
        # TODO - Reverse this
        self.__disableInteractivity()
        self.__commitTabLocation()
        if self.__sourceGameMode == GAMEMODES.JitenBag:
            self.__laytonState.setGameMode(GAMEMODES.Bag)
        elif self.__sourceGameMode == GAMEMODES.JitenSecret:
            self.__laytonState.setGameMode(GAMEMODES.SecretMenu)
        else:
            self.__laytonState.setGameMode(GAMEMODES.WiFiSecretMenu)
        self.__screenController.fadeOut(callback=self.doOnKill)

    def __callbackOnFavouritePress(self):
        if not(self.__inFavouriteMode) and len(self.__ids) > self.__indexButtonHit + self.__indexScrollTop:
            puzzleData = self.__laytonState.saveSlot.puzzleData.getPuzzleData(self.__ids[self.__indexButtonHit + self.__indexScrollTop] - 1)
            if puzzleData != None:
                puzzleData.wasPicked = not(puzzleData.wasPicked)

    def __callbackOnHitboxPress(self):
        if len(self.__ids) > self.__indexButtonHit + self.__indexScrollTop:
            if self.__inFavouriteMode:
                self.__lastSelectedFavouriteIndex = self.__ids[self.__indexScrollTop + self.__indexButtonHit]
            else:
                self.__lastSelectedNormalIndex = self.__ids[self.__indexScrollTop + self.__indexButtonHit]
            
            self.__updateSelectedPuzzle()

    def __callbackOnScrollButtonFinish(self):
        # TODO - Allow drifting while transition is happening
        closestY = round(self.__scrollY / BIAS_HITBOX_SELECT_Y) * BIAS_HITBOX_SELECT_Y
        timeForY = (abs(closestY - self.__scrollY) / self.__lastScrollSpeed)

        self.__prevScrollY = self.__scrollY
        self.__animTimer.setDuration(timeForY * 1000)
        self.__animTimer.setCallback(self.__callbackUnlockScrolling)
        self.__disableInteractivity()
    
    def __applyScrollOffset(self, value):
        vMax = BIAS_HITBOX_SELECT_Y * (len(self.__ids) - COUNT_DISPLAY)
        self.__scrollY = max(min(value, vMax), 0)
        self.__indexScrollTop = self.__scrollY // BIAS_HITBOX_SELECT_Y
        for hitbox in self.__hitboxes:
            hitbox.applyOffset(self.__scrollY)

    def __callbackUnlockScrolling(self):
        # TODO - Stop doing box code
        self.__applyScrollOffset(round(self.__scrollY / BIAS_HITBOX_SELECT_Y) * BIAS_HITBOX_SELECT_Y)
        self.__enableInteractivity()
    
    def __addScrollOffset(self, speed, value):
        self.__lastScrollSpeed = speed
        self.__applyScrollOffset(self.__scrollY + value)

    def __drawTopScreenNumber(self, nzLstEntry : DlzEntryNzLst, puzzleData : PuzzleData, gameDisplay):
        
        def getMax(countDigit : int):
            return max(0, (10 ** countDigit) - 1)
        
        if self.__textUpperNum != None:
            if self.__laytonState.getNazoData() == None:
                self.__laytonState.loadCurrentNazoData()
            
            if self.__laytonState.getNazoData() != None:
                self.__textUpperNum.setMaxNum(getMax(COUNT_DIGIT_PICARAT))
                self.__textUpperNum.setPos(POS_TEXT_PICARAT_FULL)
                self.__textUpperNum.setText(self.__laytonState.getNazoData().getPicaratStage(0))
                self.__textUpperNum.drawBiased(gameDisplay)
                self.__textUpperNum.setPos(POS_TEXT_PICARAT_DECAY)
                self.__textUpperNum.setText(self.__laytonState.getNazoData().getPicaratStage(puzzleData.levelDecay))
                self.__textUpperNum.drawBiased(gameDisplay)

            self.__textUpperNum.setMaxNum(getMax(COUNT_DIGIT_NUMBER))
            self.__textUpperNum.setPos(POS_TEXT_PUZZLE_NUMBER)
            self.__textUpperNum.setText(nzLstEntry.idExternal)
            self.__textUpperNum.drawBiased(gameDisplay)

    def __drawTopScreen(self, gameDisplay):
        # TODO - Draw order and top screen for WiFi
        if self.__animPreview != None:
            self.__animPreview.draw(gameDisplay)
        if self.__animPrize != None:
            self.__animPrize.draw(gameDisplay)
        
        self.__textRendererType.drawXYCenterPoint(gameDisplay)
        self.__textRendererName.drawXCentered(gameDisplay)
        self.__textRendererLocation.drawXYCenterPoint(gameDisplay)

        if self.__loadedExternalPuzzleId != 0:
            nzLstEntry = self.__laytonState.getCurrentNazoListEntry()
            if nzLstEntry != None:
                puzzleData = self.__laytonState.saveSlot.puzzleData.getPuzzleData(nzLstEntry.idExternal - 1)
                if puzzleData != None:
                    if self.__animHintbox != None:
                        x,y = POS_ANIM_HINT_OPEN
                        for indexHint in range(puzzleData.levelHint):
                            self.__animHintbox.setAnimationFromIndex(indexHint + 1)
                            self.__animHintbox.setPos((x,y))
                            self.__animHintbox.draw(gameDisplay)
                            x += BIAS_X_HINT_OPEN
        
                    self.__drawTopScreenNumber(nzLstEntry, puzzleData, gameDisplay)
    
    def __drawBottomScreen(self, gameDisplay):
        self.__surfaceJitenSelectOverlay.fill((0,0,0,0))
        if self.__indexOverlay != None:
            targetY = (BIAS_HITBOX_SELECT_Y * self.__indexOverlay) - self.__scrollY
            self.__surfaceJitenSelectOverlay.blit(self.__surfaceSelectBox, (0,targetY))

        for drawable in self.__hitboxes:
            drawable.renderText()

        gameDisplay.blit(self.__surfaceJitenSelectOverlay, (POS_X_SELECT_BOX, BOUNDS_Y_SELECT_BOX_MIN + RESOLUTION_NINTENDO_DS[1]))

        for drawable in self.__hitboxes + self.__buttons + self.__drawables:
            drawable.draw(gameDisplay)
        
        if self.__canBeSolved and self.__btnSolve != None:
            self.__btnSolve.draw(gameDisplay)

    def update(self, gameClockDelta):
        if self.__animTimer.getActiveState():
            self.__scrollY = lerp(self.__prevScrollY, round(self.__scrollY / BIAS_HITBOX_SELECT_Y) * BIAS_HITBOX_SELECT_Y, self.__animTimer.getStrength())
            for hitbox in self.__hitboxes:
                hitbox.applyOffset(self.__scrollY)

        self.__animTimer.update(gameClockDelta)
        if self.__animPreview != None:
            self.__animPreview.update(gameClockDelta)
        if self.__animPrize != None:
            self.__animPrize.update(gameClockDelta)
        
        if self.__btnDownSlow != None and self.__btnDownSlow.getTargettedState():
            self.__addScrollOffset(SPEED_BTN_SLOW, SPEED_BTN_SLOW * (gameClockDelta / 1000))
        elif self.__btnDownFast != None and self.__btnDownFast.getTargettedState():
            self.__addScrollOffset(SPEED_BTN_FAST, SPEED_BTN_FAST * (gameClockDelta / 1000))
        if self.__btnUpSlow != None and self.__btnUpSlow.getTargettedState():
            self.__addScrollOffset(SPEED_BTN_SLOW, -SPEED_BTN_SLOW * (gameClockDelta / 1000))
        elif self.__btnUpFast != None and self.__btnUpFast.getTargettedState():
            self.__addScrollOffset(SPEED_BTN_FAST, -SPEED_BTN_FAST * (gameClockDelta / 1000))

        for drawable in self.__drawables:
            drawable.update(gameClockDelta)

        return super().update(gameClockDelta)

    def draw(self, gameDisplay):
        self.__drawBottomScreen(gameDisplay)
        if self.__sourceGameMode != GAMEMODES.JitenWiFi:
            self.__drawTopScreen(gameDisplay)
    
        return super().draw(gameDisplay)
    
    def handleTouchEvent(self, event):
        if self.__isInteractive:
            if self.__canBeSolved and self.__btnSolve != None:
                if self.__btnSolve.handleTouchEvent(event):
                    return True

            for interactable in self.__buttons:
                if interactable.handleTouchEvent(event):
                    return True
            
            for indexHitbox, hitbox in enumerate(self.__buttonsHitbox):
                self.__indexButtonHit = indexHitbox
                if hitbox.handleTouchEvent(event):
                    return True
            
            if self.__sourceGameMode != GAMEMODES.JitenWiFi:
                for interactable in self.__buttonsTab:
                    if interactable.handleTouchEvent(event):
                        return True
                
                for indexHitbox, hitbox in enumerate(self.__buttonsFavouriteHitbox):
                    self.__indexButtonHit = indexHitbox
                    if hitbox.handleTouchEvent(event):
                        return True

        return super().handleTouchEvent(event)