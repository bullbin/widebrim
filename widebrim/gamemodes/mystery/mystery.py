from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from widebrim.engine.anim.fader import Fader

from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getButtonFromPath, getStaticButtonFromAnim, getStaticButtonFromPath, getTxtString
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
from .const import *

from pygame.transform import scale
from pygame import Surface
from math import sin, pi

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController
    from widebrim.engine.anim.button import StaticButton
    from widebrim.engine.anim.button import AnimatedButton
    from widebrim.engine.anim.image_anim.image import AnimatedImageObject

class MysteryPlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController, callbackOnTerminate : Optional[callable] = None):
        ScreenLayerNonBlocking.__init__(self)
        # TODO - Image button supports click offset, but only static button supports it in widebrim
        # TODO - Unify ? replacement in anim grabber
        # TODO - Check behaviour if button already exists, in terms of drawing
        #        Eg called to unlock something already unlocked. Same for solved.
        self.__btnCharacters        : List[Optional[StaticButton]]  = []
        self.__btnCancel            : Optional[AnimatedButton]      = None
        self.__animNew              : Optional[AnimatedImageObject] = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_NEW)
        self.__indexMysteryPressed  : int                           = -1
        self.__laytonState          : Layton2GameState              = laytonState
        self.__screenController     : ScreenController              = screenController
        self.__allowInteractivity   : bool                          = False
        self.__lastPressedButton    : int   = -1

        # TODO - AnimNew, auto gfx
        if self.__animNew != None:
            self.__animNew.setAnimationFromIndex(1)

        animBank = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_MYSTERY_BUTTONS)
        pos = (POS_BTN_ROW_0[0], POS_BTN_ROW_0[1])
        for indexChar in range(10):
            if animBank != None:
                if laytonState.saveSlot.mysteryState.flagSolved.getSlot(indexChar):
                    self.__btnCharacters.append(getStaticButtonFromAnim(animBank, str(indexChar + 11), callback=self.__callbackOnMysteryPress, pos=pos, clickOffset=BTN_MYSTERY_CLICK_OFFSET))
                else:
                    self.__btnCharacters.append(getStaticButtonFromAnim(animBank, str(indexChar + 1), callback=self.__callbackOnMysteryPress, pos=pos, clickOffset=BTN_MYSTERY_CLICK_OFFSET))
            else:
                self.__btnCharacters.append(None)
            pos = (pos[0] + POS_STRIDE_X, pos[1])
            if indexChar == 4:
                pos = (POS_BTN_ROW_0[0], POS_BTN_ROW_0[1] + POS_STRIDE_Y)

        # Not accurate
        self.__textRendererTitle    = StaticTextHelper(self.__laytonState.fontEvent)
        self.__textRendererBody     = StaticTextHelper(self.__laytonState.fontEvent)
        self.__textRendererTitle.setPos(POS_TEXT_TITLE_CENTER)
        self.__textRendererBody.setPos(POS_TEXT_CORNER)
        self.__storedMysteryIndex   : int   = laytonState.getEncodedMysteryIndex()
        self.__callbackOnTerminate  : Optional[callable]    = callbackOnTerminate

        if self.__storedMysteryIndex == -1:
            self.__btnCancel = getButtonFromPath(laytonState, PATH_ANIM_BUTTON_CANCEL, callback=self.__callbackOnCancelPress)
        else:
            self.__btnCancel = getButtonFromPath(laytonState, PATH_ANIM_BUTTON_OK, callback=self.__callbackOnCancelPress)

        self.__screenController.setBgSub(PATH_BG_SUB_NONE_LOADED % self.__laytonState.language.value)
        self.__screenController.setBgMain(PATH_BG_MAIN)

        if 0 <= self.__storedMysteryIndex < 10:
            self.__doUnlockAnim()
        elif self.__storedMysteryIndex >= 10:
            self.__doSolvedAnim()
        else:
            self.__doNormalBehaviour()

    def doOnKill(self):
        if callable(self.__callbackOnTerminate):
            self.__callbackOnTerminate()
        return super().doOnKill()

    def __enableInteractivitity(self):
        self.__allowInteractivity = True
    
    def __disableInteractivity(self):
        self.__allowInteractivity = False

    def __updateMenuNewFlag(self):
        hasNew = False
        for indexMystery in range(10):
            if self.__laytonState.saveSlot.mysteryState.flagNew.getSlot(indexMystery):
                hasNew = True
                break
        
        if not(hasNew):
            self.__laytonState.saveSlot.menuNewFlag.setSlot(False, 1)

    def __switchActiveMystery(self, indexMystery):
        if self.__indexMysteryPressed == indexMystery:
            return

        if self.__indexMysteryPressed == -1:
            self.__screenController.setBgSub(PATH_BG_SUB_LOADED)
        
        self.__indexMysteryPressed = indexMystery
        self.__laytonState.saveSlot.mysteryState.flagNew.setSlot(False, indexMystery)
        self.__updateMenuNewFlag()

        indexMystery += 1
        self.__textRendererTitle.setText(TEXT_MISSING_TITLE % indexMystery)
        self.__textRendererBody.setText(TEXT_MISSING_DATA % indexMystery)
        # TODO - No way to know if string grab failed, should return None

        if (text := getTxtString(self.__laytonState, PATH_TXT_TITLE % indexMystery)) != "":
            self.__textRendererTitle.setText(text[0:min(len(text), LENGTH_TITLE)])

        if self.__laytonState.saveSlot.mysteryState.flagSolved.getSlot(indexMystery - 1):
            if (text := getTxtString(self.__laytonState, PATH_TXT_SOLVED % indexMystery)) != "":
                self.__textRendererBody.setText(text[0:min(len(text), LENGTH_TEXT)])
        else:
            if (text := getTxtString(self.__laytonState, PATH_TXT_UNSOLVED % indexMystery)) != "":
                self.__textRendererBody.setText(text[0:min(len(text), LENGTH_TEXT)])

    def __drawButtonsAndNew(self, gameDisplay, drawNewButton : bool):
        for indexMystery in range(10):
            button = self.__btnCharacters[indexMystery]
            if button != None:
                if self.__laytonState.saveSlot.mysteryState.flagEnabled.getSlot(indexMystery):
                    button.draw(gameDisplay)
                
                if self.__animNew != None and drawNewButton and self.__laytonState.saveSlot.mysteryState.flagNew.getSlot(indexMystery) and not(self.__laytonState.saveSlot.mysteryState.flagSolved.getSlot(indexMystery)):
                    x,y = button.getPos()
                    self.__animNew.setPos((x + 9, y + 0xe))
                    self.__animNew.draw(gameDisplay)

        if self.__btnCancel != None:
            self.__btnCancel.draw(gameDisplay)
    
    # Always return True to prevent bag from taking control
    def handleTouchEvent(self, event):
        return True

    def __handleTouchEvent(self, event):
        if self.__allowInteractivity:
            if self.__btnCancel != None and self.__btnCancel.handleTouchEvent(event):
                return True

            for indexBtn, btn in enumerate(self.__btnCharacters):
                if self.__laytonState.saveSlot.mysteryState.flagEnabled.getSlot(indexBtn):
                    self.__lastPressedButton = indexBtn
                    if btn != None:
                        if btn.handleTouchEvent(event):
                            return True
            
        return True

    def __draw(self, gameDisplay):
        self.__drawButtonsAndNew(gameDisplay, True)

        # TODO - Really need to separate screens... not great since this can introduce bugs like text overflowing into other screen
        self.__textRendererTitle.drawXCentered(gameDisplay)
        self.__textRendererBody.draw(gameDisplay)

    def __update(self, gameClockDelta):
        if self.__animNew != None:
            self.__animNew.update(gameClockDelta)

    def __doUnlockAnim(self):
        indexMystery = self.__storedMysteryIndex

        def draw(self : MysteryPlayer, gameDisplay):
            self.__drawButtonsAndNew(gameDisplay, False)

        def drawPopIn(self : MysteryPlayer, gameDisplay):
            draw(self, gameDisplay)
            ratio = faderTiming.getStrength()
            ratio = 1.2 - (0.2 * faderTiming.getStrength())
            safeMystery = indexMystery
            # TODO - Game uses grid calculation, so will still try to do something even if index is invalid. Ignored in widebrim
            if animButton != None and 0 <= safeMystery < 10:
                scaleFrame = animButton.getActiveFrame()
                if scaleFrame != None:
                    x = scaleFrame.get_width()
                    y = scaleFrame.get_height()
                    scaleFrame : Surface
                    scaleFrame = scale(scaleFrame, (round(ratio * x), round(ratio * y)))
                    pos = self.__btnCharacters[safeMystery].getPos()
                    center = (pos[0] + (x // 2), pos[1] + (y // 2))
                    pos = (center[0] - (scaleFrame.get_width() // 2), center[1] - (scaleFrame.get_height() // 2))
                    gameDisplay.blit(scaleFrame, pos)
            
        def update(self : MysteryPlayer, gameClockDelta):
            faderTiming.update(gameClockDelta)
            if self.__animNew != None:
                self.__animNew.update(gameClockDelta)
            if animButton != None:
                animButton.update(gameClockDelta)
        
        def updateFinish(self : MysteryPlayer, gameClockDelta):
            self.__doNormalBehaviour()

        def terminate():
            self.__laytonState.saveSlot.mysteryState.flagNew.setSlot(True, indexMystery)
            self.__laytonState.saveSlot.menuNewFlag.setSlot(True, 1)
            MysteryPlayer.update = updateFinish

        def doShakeAndPause():
            MysteryPlayer.draw = draw
            self.__laytonState.saveSlot.mysteryState.flagEnabled.setSlot(True, indexMystery)
            faderTiming.setDurationInFrames(50)
            faderTiming.setCallback(terminate)
            self.__screenController.shakeBg(320)

        def doPopAnimation():
            MysteryPlayer.draw = drawPopIn
            faderTiming.setDurationInFrames(10)
            faderTiming.setCallback(doShakeAndPause)

        def smallPause():
            faderTiming.setDurationInFrames(4)
            faderTiming.setCallback(doPopAnimation)

        def doFlash():
            self.__screenController.flashMain(callback=smallPause)

        def startPause():
            faderTiming.setDurationInFrames(30)
            faderTiming.setCallback(doFlash)
        
        faderTiming = Fader(0, initialActiveState=False)
        # TODO - What was this??
        animButton = getBottomScreenAnimFromPath(self.__laytonState, PATH_ANIM_MYSTERY_BUTTONS, spawnAnimName=str(indexMystery + 1))
        self.__screenController.fadeInMain(callback=startPause)
        
        MysteryPlayer.update = update
        MysteryPlayer.draw = draw

    def __doSolvedAnim(self):
        # TODO - Stamp anim is a little odd in real game, code indicates some sprite indexing. Do a better job implementing it :)
        indexMystery = self.__storedMysteryIndex - 10
        animSolved = getBottomScreenAnimFromPath(self.__laytonState, PATH_ANIM_STAMP)

        def update(self : MysteryPlayer, gameClockDelta):
            faderTiming.update(gameClockDelta)

        def updateFinish(self : MysteryPlayer, gameClockDelta):
            self.__doNormalBehaviour()

        def draw(self : MysteryPlayer, gameDisplay):
            self.__drawButtonsAndNew(gameDisplay, False)
        
        def drawHighlightBox(self : MysteryPlayer, gameDisplay):
            self.__drawButtonsAndNew(gameDisplay, False)
            alpha = round(abs(sin(pi * 2 * faderTiming.getStrength())) * MAX_ALPHA * 255)
            surfHighlight.set_alpha(alpha)
            self.__drawButtonsAndNew(gameDisplay, False)

            x = ((indexMystery % 5) * POS_ROW_STRIDE_X) + ROW_OFFSET_X
            y = ((indexMystery // 5) * POS_ROW_STRIDE_Y) + ROW_OFFSET_Y + RESOLUTION_NINTENDO_DS[1]
            gameDisplay.blit(surfHighlight, (x,y))

        def drawSolved(self : MysteryPlayer, gameDisplay):
            self.__drawButtonsAndNew(gameDisplay, False)
            if animSolved != None:
                animSolved.draw(gameDisplay)

        def updateSolved(self : MysteryPlayer, gameClockDelta):
            update(self, gameClockDelta)
            if animSolved != None:
                animSolved.update(gameClockDelta)

        def terminate():
            MysteryPlayer.update = updateFinish

        def startShake():
            # TODO - shake bg is for 20 frames, which is 333 ms
            self.__screenController.shakeBg(320)
            faderTiming.setDurationInFrames(20)
            faderTiming.setCallback(terminate)
            self.__laytonState.saveSlot.mysteryState.flagSolved.setSlot(True, indexMystery)

            if 0 <= indexMystery < 10:
                x = POS_BTN_ROW_0[0] + (POS_STRIDE_X * (indexMystery % 5))
                y = POS_BTN_ROW_0[1] + (POS_STRIDE_Y * (indexMystery // 5))
                self.__btnCharacters[indexMystery] = getStaticButtonFromPath(self.__laytonState, PATH_ANIM_MYSTERY_BUTTONS, str(indexMystery + 11), callback=self.__callbackOnMysteryPress, pos=(x,y), clickOffset=BTN_MYSTERY_CLICK_OFFSET)
            MysteryPlayer.update = update

        def startStampAnim():
            # TODO - not correct, should be 3 blanks...
            faderTiming.setDurationInFrames(5)
            faderTiming.setCallback(startShake)
            x = ((indexMystery % 5) * POS_ROW_STRIDE_X)
            y = ((indexMystery // 5) * POS_ROW_STRIDE_Y) + ROW_OFFSET_Y_STAMP + RESOLUTION_NINTENDO_DS[1]
            if animSolved != None:
                animSolved.setPos((x,y))
                animSolved.setAnimationFromIndex(1)

            MysteryPlayer.draw = drawSolved
            MysteryPlayer.update = updateSolved

        def startFlashAnim():
            faderTiming.setDurationInFrames(90)
            faderTiming.setCallback(startStampAnim)
            MysteryPlayer.draw = drawHighlightBox

        faderTiming = Fader(0, initialActiveState=False)
        surfHighlight = Surface(DIMENSIONS_HIGHLIGHT_BOX)
        surfHighlight.fill((255,255,255))

        animButton = getBottomScreenAnimFromPath(self.__laytonState, "event/hukmaru_hanko.spr")
        self.__screenController.fadeInMain(callback=startFlashAnim)

        MysteryPlayer.draw = draw
        MysteryPlayer.update = update

    def __doNormalBehaviour(self):
        self.__screenController.fadeIn(callback=self.__enableInteractivitity)
        MysteryPlayer.draw = self.__draw
        MysteryPlayer.update = self.__update
        MysteryPlayer.handleTouchEvent = self.__handleTouchEvent

    def __callbackOnMysteryPress(self):
        self.__switchActiveMystery(self.__lastPressedButton)
    
    def __callbackOnCancelPress(self):
        self.__disableInteractivity()
        self.__screenController.fadeOut(callback=self.doOnKill)