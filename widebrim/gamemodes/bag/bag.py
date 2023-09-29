from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
from widebrim.gamemodes.core_popup.save import SaveLoadScreenPopup
from widebrim.gamemodes.core_popup.utils import FullScreenPopup
from widebrim.gamemodes.dramaevent.const import PATH_ITEM_ICON
from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getButtonFromPath, getClickableButtonFromPath, getTopScreenAnimFromPath
from widebrim.engine.anim.image_anim.imageAsNumber import StaticImageAsNumericalFont
from widebrim.engine.anim.button import AnimatedButton
from widebrim.gamemodes.mystery import MysteryPlayer

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController
    from widebrim.engine.anim.image_anim import AnimatedImageObject

from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine.state.enum_mode import GAMEMODES
from .const import *
from .popupReset import ResetPopup

class BagPlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController):

        self.__buttons  : List[AnimatedButton]      = []
        self.__anims    : List[AnimatedImageObject] = []

        ScreenLayerNonBlocking.__init__(self)
        self.laytonState = laytonState
        self.screenController = screenController

        self.__isInteractable : bool = False
        self.__popup : Optional[FullScreenPopup] = None

        # TODO - Buttons draw slightly differently, the tojiru button won't go back to OFF state after being pressed.
        self.__addButton(getButtonFromPath(laytonState, PATH_BTN_RESET, namePosVariable=VARIABLE_DEFAULT_POS, callback=self.__callbackOnReset))
        self.__addButton(getClickableButtonFromPath(laytonState, PATH_BTN_TOJIRU, namePosVariable=VARIABLE_DEFAULT_POS, callback=self.__callbackOnCloseBag, unclickOnCallback=False))
        self.__addButton(getButtonFromPath(laytonState, PATH_BTN_MEMO, namePosVariable=VARIABLE_DEFAULT_POS, callback=self.__callbackOnStartMemo))
        self.__addButton(getButtonFromPath(laytonState, PATH_BTN_MYSTERY, namePosVariable=VARIABLE_DEFAULT_POS, callback=self.__callbackOnStartMystery))
        self.__addButton(getButtonFromPath(laytonState, PATH_BTN_PUZZLE, namePosVariable=VARIABLE_DEFAULT_POS, callback=self.__callbackOnStartJiten))
        self.__addButton(getButtonFromPath(laytonState, PATH_BTN_SAVE, namePosVariable=VARIABLE_DEFAULT_POS, callback=self.__callbackOnStartSave))
        
        if (hintCoinAnim := getTopScreenAnimFromPath(self.laytonState, PATH_ANI_MEDAL_ICON, pos=POS_ANI_MEDAL_ICON)) != None:
            indexAnimation = 1
            for indexLimit, limit in enumerate([0] + MEDAL_ICON_LIMITS):
                if self.laytonState.saveSlot.hintCoinAvailable < limit:
                    break
                else:
                    indexAnimation = indexLimit + 1
            hintCoinAnim.setAnimationFromIndex(indexAnimation)
            self.__addAnim(hintCoinAnim)

        if (laytonWalkAnim := getTopScreenAnimFromPath(laytonState, PATH_ANI_DOT_LAYTON_WALK, pos=POS_ANI_DOT_LAYTON_WALK)) != None:
            if not(self.laytonState.timeGetRunningTime() < (DOT_LAYTON_WALK_OLD_ANIM_HOURS * 60 * 60) - 1):
                laytonWalkAnim.setAnimationFromIndex(2)
            self.__addAnim(laytonWalkAnim)

        self.__loadAdditionalButtons()
        self.__animNewButton : Optional[AnimatedImageObject] = getBottomScreenAnimFromPath(self.laytonState, PATH_ANI_NEW)
        self.__animItemIcons : Optional[AnimatedImageObject] = getBottomScreenAnimFromPath(self.laytonState, PATH_ITEM_ICON)
        self.__rendererStaticNumber     : Optional[StaticImageAsNumericalFont] = None
        self.__rendererStaticNumber2    : Optional[StaticImageAsNumericalFont] = None
        self.__rendererPlaceName = StaticTextHelper(laytonState.fontEvent)

        # TODO - Weird positioning
        self.__rendererPlaceName.setPos((POS_TEXT_PLACE_NAME[0], POS_TEXT_PLACE_NAME[1] + 2))
        # TODO - Breaks long strings
        self.__rendererPlaceName.setText(laytonState.namePlace[0:min(len(laytonState.namePlace),64)])

        # TODO - What's with the stride here?
        if (staticNumber := getTopScreenAnimFromPath(laytonState, PATH_ANI_STATUS_NUMBER)) != None:
            self.__rendererStaticNumber = StaticImageAsNumericalFont(staticNumber, stride=staticNumber.getDimensions()[0] - 2)
        if (staticNumber := getTopScreenAnimFromPath(laytonState, PATH_ANI_STATUS_NUMBER2)) != None:
            self.__rendererStaticNumber2 = StaticImageAsNumericalFont(staticNumber, stride=staticNumber.getDimensions()[0] + 1)

        if self.__animNewButton != None:
            self.__animNewButton.setAnimationFromIndex(1)

        self.screenController.setBgMain(PATH_BG_MAIN)
        self.screenController.setBgSub(PATH_BG_SUB)
        self.screenController.fadeIn(callback=self.__enableInteractivity)

        self.__drawBottomScreen : bool = True
        self.__drawTopScreenGraphics    : bool = True
        self.laytonState.setGameModeNext(GAMEMODES.Bag)
        
    def draw(self, gameDisplay):
        # TODO - Preserve order. But messy
        def drawBase():
            # TODO - Horrible hack. Please please please separate the screens.
            for drawable in self.__buttons + self.__anims:
                if isinstance(drawable, AnimatedButton):
                    if drawable.image.getPos()[1] < RESOLUTION_NINTENDO_DS[1]:
                        if self.__drawTopScreenGraphics:
                            drawable.draw(gameDisplay)
                    elif self.__drawBottomScreen:
                        drawable.draw(gameDisplay)
                else:
                    if drawable.getPos()[1] < RESOLUTION_NINTENDO_DS[1]:
                        if self.__drawTopScreenGraphics:
                            drawable.draw(gameDisplay)
                    elif self.__drawBottomScreen:
                        drawable.draw(gameDisplay)

            if self.__drawBottomScreen:
                self.__drawNewButton(gameDisplay)
                self.__drawItemIcons(gameDisplay)
            
            if self.__drawTopScreenGraphics:
                self.__drawTopScreen(gameDisplay)

        drawBase()
        if self.__popup != None:
            self.__popup.draw(gameDisplay)

        return super().draw(gameDisplay)

    def update(self, gameClockDelta):
        for updatable in self.__buttons + self.__anims:
            updatable.update(gameClockDelta)
        if self.__animNewButton != None:
            self.__animNewButton.update(gameClockDelta)
        if self.__popup != None:
            self.__popup.update(gameClockDelta)
        return super().update(gameClockDelta)

    def __enableInteractivity(self):
        self.__isInteractable = True

    def __disableInteractivity(self):
        self.__isInteractable = False
    
    def __addButton(self, button : Optional[AnimatedButton]):
            if button != None:
                self.__buttons.append(button)
        
    def __addAnim(self, anim : Optional[AnimatedImageObject]):
        if anim != None:
            self.__anims.append(anim)

    def __callbackOnReset(self):

        # TODO - Setup interactivity checks

        def killReset():
            self.__popup = None
            # TODO - Bag button needs to be drawn too (not mimicking full draw pipeline)
            # The game applies this workaround as well since they don't want to be caught with no buttons
            self.__drawBottomScreen = True
        
        def doReset():
            self.__disableInteractivity()
            self.laytonState.setGameMode(GAMEMODES.Reset)
            self.screenController.fadeOut(callback=self.doOnKill)

        self.__drawBottomScreen = False
        self.__popup = ResetPopup(self.laytonState, self.screenController, doReset, killReset)

    def __callbackOnStartMystery(self):

        def killMystery():
            self.__disableInteractivity()
            self.__drawBottomScreen = True
            self.__drawTopScreenGraphics = True
            self.__popup = None
            self.screenController.setBgMain(PATH_BG_MAIN)
            self.screenController.setBgSub(PATH_BG_SUB)
            self.screenController.fadeIn(callback=self.__enableInteractivity)

        def spawnMystery():
            self.__drawBottomScreen = False
            self.__drawTopScreenGraphics = False
            self.__popup = MysteryPlayer(self.laytonState, self.screenController, killMystery)
            self.__enableInteractivity()

        self.__disableInteractivity()
        self.screenController.fadeOut(callback=spawnMystery)  

    def __callbackOnStartSave(self):

        def endKillSaveLoad():
            self.__drawBottomScreen = True
            self.__popup = None
            self.screenController.setBgMain(PATH_BG_MAIN)
            self.screenController.fadeInMain(callback=self.__enableInteractivity)

        def startKillSaveLoad():
            self.__disableInteractivity()
            self.screenController.fadeOutMain(callback=endKillSaveLoad)

        def spawnSaveLoad():
            self.__drawBottomScreen = False
            self.__popup = SaveLoadScreenPopup(self.laytonState, self.screenController, SaveLoadScreenPopup.MODE_SAVE, 0, callbackOnSlot=startKillSaveLoad, callbackOnTerminate=startKillSaveLoad)
            self.screenController.fadeInMain(callback=self.__enableInteractivity)

        self.__disableInteractivity()
        self.screenController.fadeOutMain(callback=spawnSaveLoad)  

    def __callbackOnCloseBag(self):
        self.__disableInteractivity()
        self.laytonState.setGameMode(GAMEMODES.Room)
        self.screenController.fadeOut(callback=self.doOnKill)
    
    def __callbackOnStartMemo(self):
        self.__disableInteractivity()
        self.laytonState.setGameMode(GAMEMODES.Memo)
        self.screenController.fadeOut(callback=self.doOnKill)
    
    def __callbackOnStartJiten(self):
        self.__disableInteractivity()
        self.laytonState.setGameMode(GAMEMODES.JitenBag)
        self.screenController.fadeOut(callback=self.doOnKill)
    
    def __callbackOnStartCamera(self):
        self.__disableInteractivity()
        self.laytonState.saveSlot.menuNewFlag.setSlot(False, 2)
        if self.laytonState.isCameraAssembled():
            self.laytonState.setGameMode(GAMEMODES.UnkSubPhoto1)
        else:
            if (eventInfo := self.laytonState.getEventInfoEntry(18410)) != None and eventInfo.indexEventViewedFlag != None:
                if self.laytonState.saveSlot.eventViewed.getSlot(eventInfo.indexEventViewedFlag):
                    self.laytonState.setGameMode(GAMEMODES.SubCamera)
                else:
                    self.laytonState.setGameMode(GAMEMODES.DramaEvent)
                    self.laytonState.setEventId(18410)
        self.screenController.fadeOut(callback=self.doOnKill)

    def __callbackOnStartDiary(self):
        self.__disableInteractivity()
        self.laytonState.setGameMode(GAMEMODES.Diary)
        self.screenController.fadeOut(callback=self.doOnKill)

    def __loadAdditionalButtons(self):        
        namePosVariable = VARIABLE_BTN_DIARY_DISABLED
        if self.laytonState.isAnthonyDiaryEnabled():
            self.__addButton(getButtonFromPath(self.laytonState, PATH_BTN_DIARY, namePosVariable=VARIABLE_DEFAULT_POS, callback=self.__callbackOnStartDiary))
            namePosVariable = VARIABLE_BTN_DIARY_ENABLED

        if self.laytonState.isCameraAvailable():
            if self.laytonState.isCameraAssembled():
                self.__addButton(getButtonFromPath(self.laytonState, PATH_BTN_CAMERA_FIXED, namePosVariable=namePosVariable, callback=self.__callbackOnStartCamera))
            else:
                self.__addButton(getButtonFromPath(self.laytonState, PATH_BTN_CAMERA_BROKEN, namePosVariable=namePosVariable, callback=self.__callbackOnStartCamera))
        else:
            self.__addAnim(getBottomScreenAnimFromPath(self.laytonState, PATH_ANI_CAMERA_DISABLED))
        
        if self.laytonState.isHamsterUnlocked():
            if self.laytonState.isHamsterCompleted():
                self.__addButton(getButtonFromPath(self.laytonState, PATH_BTN_HAMSTER_COMPLETE, namePosVariable=namePosVariable))
            else:
                self.__addButton(getButtonFromPath(self.laytonState, PATH_BTN_HAMSTER_ENABLED, namePosVariable=namePosVariable))
        else:
            self.__addAnim(getBottomScreenAnimFromPath(self.laytonState, PATH_ANI_HAMSTER_DISABLED))
        
        if self.laytonState.isTeaEnabled():
            if self.laytonState.isTeaCompleted():
                self.__addButton(getButtonFromPath(self.laytonState, PATH_BTN_TEA_COMPLETE, namePosVariable=namePosVariable))
            else:
                self.__addButton(getButtonFromPath(self.laytonState, PATH_BTN_TEA_ENABLED, namePosVariable=namePosVariable))
        else:
            self.__addAnim(getBottomScreenAnimFromPath(self.laytonState, PATH_ANI_TEA_DISABLED))

    def __drawNewButton(self, gameDisplay):

        def setPosAndDraw(pos):
            self.__animNewButton.setPos((pos[0], pos[1] + RESOLUTION_NINTENDO_DS[1]))
            self.__animNewButton.draw(gameDisplay)

        if self.__animNewButton != None:
            if self.laytonState.saveSlot.menuNewFlag.getSlot(0):
                setPosAndDraw((0xd, 0x26))
            if self.laytonState.saveSlot.menuNewFlag.getSlot(1):
                setPosAndDraw((0x49,0x16))
            if self.laytonState.isCameraAvailable() and self.laytonState.saveSlot.menuNewFlag.getSlot(2):
                if self.laytonState.isAnthonyDiaryEnabled():
                    setPosAndDraw((0x47,0x5e))
                else:
                    setPosAndDraw((0x24,0x5e))
            if self.laytonState.isHamsterUnlocked() and self.laytonState.saveSlot.menuNewFlag.getSlot(3):
                if self.laytonState.isAnthonyDiaryEnabled():
                    setPosAndDraw((0x82,100))
                else:
                    setPosAndDraw((0x66,100))

            # TODO - help_mes, has additional variable check
            if self.laytonState.isTeaEnabled() and self.laytonState.saveSlot.menuNewFlag.getSlot(4):
                if self.laytonState.isAnthonyDiaryEnabled():
                    setPosAndDraw((0xbe,0x5f))
                else:
                    setPosAndDraw((0xab,0x5f))
            
            if self.laytonState.isAnthonyDiaryEnabled() and self.laytonState.saveSlot.menuNewFlag.getSlot(6):
                setPosAndDraw((0xd,0x62))
                
    def __drawItemIcons(self, gameDisplay):
        if self.__animItemIcons != None:
            x = 0x66
            y = 0x9e + RESOLUTION_NINTENDO_DS[1]
            for indexItem in range(8):
                if self.laytonState.saveSlot.storyItemFlag.getSlot(indexItem):
                    self.__animItemIcons.setPos((x,y))
                    self.__animItemIcons.setAnimationFromIndex(indexItem + 1)
                    self.__animItemIcons.draw(gameDisplay)
                    x += 0x1c

    def __drawTopScreen(self, gameDisplay):
        def drawText(renderer : StaticImageAsNumericalFont, pos, value : int, usePadding : bool = False, maxNum : int = 999):
            renderer.setUsePadding(usePadding)
            renderer.setPos(pos)
            renderer.setMaxNum(maxNum)
            renderer.setText(value)
            renderer.drawBiased(gameDisplay)

        self.__rendererPlaceName.drawXYCenterPoint(gameDisplay)

        if self.__rendererStaticNumber2 != None:
            solved, encountered = self.laytonState.saveSlot.getSolvedAndEncounteredPuzzleCount()
            drawText(self.__rendererStaticNumber2, (0x3f,0x2d), solved)
            drawText(self.__rendererStaticNumber2, (0x3f,0x71), encountered)
            drawText(self.__rendererStaticNumber2, (0xbf,0x20), self.laytonState.saveSlot.picarats, maxNum=9999)

        if self.__rendererStaticNumber != None:
            drawText(self.__rendererStaticNumber, (0xce,0x55), self.laytonState.saveSlot.hintCoinAvailable)
            drawText(self.__rendererStaticNumber, (0xe8,0x55), self.laytonState.saveSlot.hintCoinEncountered)

            seconds = self.laytonState.timeGetRunningTime()
            hours = seconds // (60 * 60)
            minutes = (seconds // 60) % 60
            if hours >= 100:
                minutes = 59

            drawText(self.__rendererStaticNumber, (0xa7,0x83), hours, usePadding=True, maxNum=99)
            drawText(self.__rendererStaticNumber, (0xd2,0x83), minutes, usePadding=True, maxNum=99)
    
        # TODO - Generate name place. Should be stored in the save, but not in widebrim
        # Couldn't this lead to some issues in game if the bag was forced to load before room? not possible

    def handleTouchEvent(self, event):
        if self.__isInteractable:
            if self.__popup != None:
                return self.__popup.handleTouchEvent(event)
            else:
                for button in self.__buttons:
                    if button.handleTouchEvent(event):
                        return True
        return super().handleTouchEvent(event)