from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, offsetVectorToSecondScreen
from widebrim.engine.anim.fader import Fader
from .const import *

# TODO - Abstract further for support of initial text popup
# TODO - Make proper fading popup class that can also be used in rooms and drama event (save popup, item popup, etc)
class NarrationPopup():

    # Timed with audio, not accurate
    DURATION_PER_SLIDE  = 3000
    DURATION_FADE_IN    = 500

    def __init__(self, animation, startIndex, stopIndex, streamIndex, callbackTerminate):
        self._slideSurface = []
        self._slidePos = []
        self._callback = callbackTerminate

        self._isWaiting = False

        def startTextFadeOut():
            self._isWaiting = False
            self.fader.setInvertedState(True)
            self.fader.setCallback(self._callback)
            self.fader.setDuration(NarrationPopup.DURATION_FADE_IN)

        def startWaiting():
            self._isWaiting = True
            self._updateSlideAlpha()
            self.fader.setCallback(startTextFadeOut)
            self.fader.setDuration(NarrationPopup.DURATION_PER_SLIDE)

        self.fader = Fader(NarrationPopup.DURATION_FADE_IN, callbackOnDone=startWaiting)

        hasSlides = False
        for indexImage in range(startIndex, stopIndex):
            if animation.setAnimationFromName(str(indexImage + 1)):
                self._slideSurface.append(animation.getActiveFrame())
                pos = animation.getVariable(ANI_POS_VAR % (indexImage + 1))
                if pos == None:
                    pos = (0,0)
                pos = offsetVectorToSecondScreen(pos)
                self._slidePos.append(pos)

                hasSlides = True
            else:
                self._slideSurface.append(None)
                self._slideSurface.append(None)
        
        if not(hasSlides):
            self._callback()
        else:
            self._updateSlideAlpha()
    
    def _updateSlideAlpha(self):
        for slide in self._slideSurface:
            if slide != None:
                slide.set_alpha(round(self.fader.getStrength() * 255))

    def draw(self, gameDisplay):
        for indexSlide, slide in enumerate(self._slideSurface):
            if slide != None:
                gameDisplay.blit(slide, self._slidePos[indexSlide])

    def update(self, gameClockDelta):
        self.fader.update(gameClockDelta)

        if not(self._isWaiting):
            self._updateSlideAlpha()

class NarrationPlayer(ScreenLayerNonBlocking):

    def __init__(self, laytonState, screenController):
        ScreenLayerNonBlocking.__init__(self)
        self.laytonState = laytonState
        self.screenController = screenController
        self._popup = None

        self._animNarration = None
        self._countNarrationSlides = 0
        self._maxNarrationSlides = 0
        self._arrangementSlides = []
        self._timeElapsed = 0

        def switchSlide():
            self._popup = None
            if len(self._arrangementSlides) > 0:
                startIndex, stopIndex = self._arrangementSlides.pop(0)
                self._popup = NarrationPopup(self._animNarration, startIndex, stopIndex, 0, switchSlide)
            else:
                self.doOnKill()

        def makeActive():
            switchSlide()        

        idEvent = self.laytonState.getEventId()
        if self.laytonState.entryEvInfo != None:
            idEvent = self.laytonState.entryEvInfo.idEvent

        if idEvent == ID_EVENT_NARRATION_0:
            screenController.setBgMain(PATH_BG_NARRATION_0)
            self._animNarration = getBottomScreenAnimFromPath(self.laytonState, PATH_ANI_NARRATION_0)
            self._countNarrationSlides = COUNT_ANI_NARRATION_0
            self._arrangementSlides = SLIDES_ANI_NARRATION_0
        elif idEvent == ID_EVENT_NARRATION_1:
            screenController.setBgMain(PATH_BG_NARRATION_1)
            self._animNarration = getBottomScreenAnimFromPath(self.laytonState, PATH_ANI_NARRATION_1)
            self._countNarrationSlides = COUNT_ANI_NARRATION_1
            self._arrangementSlides = SLIDES_ANI_NARRATION_1
            self.screenController.modifyPaletteMain(120)
        elif idEvent == ID_EVENT_NARRATION_2:
            screenController.setBgMain(PATH_BG_NARRATION_2)
            self._animNarration = getBottomScreenAnimFromPath(self.laytonState, PATH_ANI_NARRATION_2)
            self._countNarrationSlides = COUNT_ANI_NARRATION_2
            self._arrangementSlides = SLIDES_ANI_NARRATION_2
        elif idEvent == ID_EVENT_NARRATION_3:
            screenController.setBgMain(PATH_BG_NARRATION_3)
            self._animNarration = getBottomScreenAnimFromPath(self.laytonState, PATH_ANI_NARRATION_3)
            self._countNarrationSlides = COUNT_ANI_NARRATION_3
            self._arrangementSlides = SLIDES_ANI_NARRATION_3
        else:
            self.doOnKill()
        
        if not(self.getContextState()):
            self.screenController.fadeInMain(callback=makeActive)
    
    def doOnKill(self):
        self.laytonState.setGameMode(self.laytonState.getGameModeNext())
        return super().doOnKill()

    def update(self, gameClockDelta):
        if self._popup != None:
            self._popup.update(gameClockDelta)

    def draw(self, gameDisplay):
        if self._popup != None:
            self._popup.draw(gameDisplay)