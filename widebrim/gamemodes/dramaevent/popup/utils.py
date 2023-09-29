from typing import Callable, List, Optional
from widebrim.madhatter.hat_io.asset_image.image import AnimatedImage
from widebrim.engine.anim.image_anim.image import AnimatedImageObject, AnimatedImageObjectWithSubAnimation
from ...core_popup.utils import MainScreenPopup
from ....engine.anim.fader import Fader
from ....engine.const import RESOLUTION_NINTENDO_DS
from .const import NAME_AUTO_ANIM, NAME_POS_VARIABLE

# TODO - Popups and characters all share the same layers, so alpha transitions cause colours to immediately bleed.
# What is the best way to mimick this behaviour?

# TODO - Bugfix, there's clicking during the animation causes shit to start breaking!
# TODO - Clicking should terminate the fader immediately, not constantly restart it
# TODO - Move this class to a different module since tobj will be using this too.

from pygame import MOUSEBUTTONUP

class FadingPopup(MainScreenPopup):

    DURATION_FADE = 300

    def __init__(self, laytonState, screenController, callbackOnTerminate, bgSurface, bgSurfacePos):
        MainScreenPopup.__init__(self, callbackOnTerminate)
        self._alphaFader = Fader(FadingPopup.DURATION_FADE)
        self._surfaceBackground = bgSurface
        self._surfaceBackgroundPos = bgSurfacePos
        self._callbackOnTerminate = callbackOnTerminate

        self._isTryingToTerminate = False
    
    def doOnKill(self):
        self._alphaFader.setActiveState(False)
        super().doOnKill()
        if callable(self._callbackOnTerminate):
            self._callbackOnTerminate()

    def updateForegroundElements(self, gameClockDelta):
        pass
    
    def drawForegroundElements(self, gameDisplay):
        pass

    def handleTouchEventForegroundElements(self, event):
        # Return True if the touch event was used in the popup, meaning termination is not required.
        return False

    def _drawBackground(self, gameDisplay):
        # TODO - Only update surface where required
        self._surfaceBackground.set_alpha(round(self._alphaFader.getStrength() * 255))
        gameDisplay.blit(self._surfaceBackground, self._surfaceBackgroundPos)

    def draw(self, gameDisplay):
        self._drawBackground(gameDisplay)
        if not(self._alphaFader.getActiveState()):
            self.drawForegroundElements(gameDisplay)

    def update(self, gameClockDelta):
        self._alphaFader.update(gameClockDelta)
        if not(self._alphaFader.getActiveState()):
            self.updateForegroundElements(gameClockDelta)
    
    def startTerminateBehaviour(self):
        self._isTryingToTerminate = True
        self._alphaFader.setInvertedState(True)
        self._alphaFader.reset()
        self._alphaFader.setCallback(self.doOnKill)

    def handleTouchEvent(self, event):
        if not(self._isTryingToTerminate):
            if self._alphaFader.getStrength():
                if not(self.handleTouchEventForegroundElements(event)) and not(self._alphaFader.getActiveState()) and event.type == MOUSEBUTTONUP:
                    self.startTerminateBehaviour()

            elif self._alphaFader.getActiveState() and not(self._isTryingToTerminate) and event.type == MOUSEBUTTONUP:
                self._alphaFader.skip()

class FadingPopupAnimBackground(FadingPopup):
    def __init__(self, laytonState, screenController, callbackOnTerminate : Optional[Callable], bgAnim : Optional[AnimatedImageObject]):
        MainScreenPopup.__init__(self, callbackOnTerminate)
        self._alphaFader = Fader(FadingPopup.DURATION_FADE)
        self._bgAnim = bgAnim
        self._callbackOnTerminate = callbackOnTerminate
        self._isTryingToTerminate = False
    
    def _drawBgAnimRecursive(self, anim : AnimatedImageObject, gameDisplay):
        if anim != None:
            if (frame := anim.getActiveFrame()) != None:
                frame.set_alpha(round(self._alphaFader.getStrength() * 255))
                gameDisplay.blit(frame, anim.getPosWithOffset())
            if type(anim) == AnimatedImageObjectWithSubAnimation:
                self._drawBgAnimRecursive(anim.subAnimation, gameDisplay)
    
    def _updateBase(self, gameClockDelta : float):
        super().update(gameClockDelta)

    def _drawBackground(self, gameDisplay):
        self._drawBgAnimRecursive(self._bgAnim, gameDisplay)
    
    def update(self, gameClockDelta):
        if self._bgAnim != None:
            self._bgAnim.update(gameClockDelta)
        self._updateBase(gameClockDelta)

class FadingPopupMultipleAnimBackground(FadingPopupAnimBackground):
    def __init__(self, laytonState, screenController, callbackOnTerminate : Optional[Callable], bgAnim : List[Optional[AnimatedImageObject]]):
        FadingPopupAnimBackground.__init__(self, laytonState, screenController, callbackOnTerminate, None)
        self._bgAnim = bgAnim
    
    def _drawBackground(self, gameDisplay):
        for anim in self._bgAnim:
            self._drawBgAnimRecursive(anim, gameDisplay)
    
    def update(self, gameClockDelta):
        for anim in self._bgAnim:
            if anim != None:
                anim.update(gameClockDelta)
        self._updateBase(gameClockDelta)

class PrizeWindow2PopupWithCursor(FadingPopupAnimBackground):
    def __init__(self, laytonState, screenController, eventStorage):
        prizeWindow2 = eventStorage.getAssetPrizeWindow2()
        if prizeWindow2 != None:
            prizeWindow2.setAnimationFromName(NAME_AUTO_ANIM)
            prizeWindow2Pos = prizeWindow2.getVariable(NAME_POS_VARIABLE)
            if prizeWindow2Pos != None:
                prizeWindow2.setPos((prizeWindow2Pos[0], prizeWindow2Pos[1] + RESOLUTION_NINTENDO_DS[1]))

        FadingPopupAnimBackground.__init__(self, laytonState, screenController, None, prizeWindow2)

        self._cursorWait = eventStorage.getAssetCursorWait()
        if self._cursorWait != None:
            self._cursorWait.setAnimationFromName(NAME_AUTO_ANIM)