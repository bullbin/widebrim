from ..core_popup.utils import FullScreenPopup
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getImageFromPath, offsetVectorToSecondScreen
from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.engine.anim.fader import Fader
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
from widebrim.engine.anim.image_anim import ImageFontRenderer
from .const import PATH_BG_TITLE, PATH_BG_PICARAT, PATH_ANI_TITLE, PATH_ANI_PICARAT_BIG, PATH_ANI_PICARAT_SMALL, PATH_ANI_PICARAT_TOTAL
from pygame import Surface

# Accuracy of this object is hit-or-miss
# What's accurate:
#   - Variables grabbed by animation objects
#   - Behaviour of animation objects chosen for puzzles

def getNumberFontRendererFromImage(anim):
    if anim != None:
        output = ImageFontRenderer(anim)
        if anim.getVariable("pos") != None:
            xRightmost  = anim.getVariable("pos")[0]
            y           = anim.getVariable("pos")[1]
            stride      = anim.getVariable("pos")[2]
            maxNum      = anim.getVariable("pos")[5]

            output.setPos((xRightmost,y))
            output.setStride(stride)
            output.setMaxNum(maxNum)
        
        return output
    return None

def getNumberFontRendererIfValid(laytonState, pathAnim):
    image = getBottomScreenAnimFromPath(laytonState, pathAnim)
    output = getNumberFontRendererFromImage(image)
    output.setPos(offsetVectorToSecondScreen(output.getPos()))
    return output

# TODO - Fix the fader judder when loading new data (async? add a frame to faders?)
class IntroLayer(FullScreenPopup):
    def __init__(self, laytonState, screenController, callbackOnTerminate):
        FullScreenPopup.__init__(self, callbackOnTerminate)
        self.screenController = screenController
        self.laytonState = laytonState
        self.callbackOnTerminate = callbackOnTerminate

        self.rendererPicaratBig     = getNumberFontRendererIfValid(laytonState, PATH_ANI_PICARAT_BIG)
        self.rendererPicaratSmall   = getNumberFontRendererIfValid(laytonState, PATH_ANI_PICARAT_SMALL)
        self.rendererPicaratTotal   = getNumberFontRendererIfValid(laytonState, PATH_ANI_PICARAT_TOTAL)

        self.rendererPicaratBig.setText(self.laytonState.getNazoData().getPicaratStage(0))
        self.rendererPicaratTotal.setText(self.laytonState.getNazoData().getPicaratStage(0))
        self.rendererPicaratSmall.setText(self.laytonState.saveSlot.picarats)

        self._drawPicarats = False
        self._doCountdownAnim = False

        picaratSlot = self.laytonState.saveSlot.puzzleData.getPuzzleData((self.laytonState.getNazoData().idExternal - 1))
        if picaratSlot != None:
            picaratSlot = picaratSlot.levelDecay
        else:
            picaratSlot = 0

        # TODO - Is bottom screen skipped on some modes?
        self._countPicaratDifference = self.laytonState.getNazoData().getPicaratStage(0) - self.laytonState.getNazoData().getPicaratStage(picaratSlot)

        # Clear both screens
        self.screenController.setBgMain(None)
        self.screenController.setBgSub(None)
        
        self.bgTitleScreen = getImageFromPath(self.laytonState, PATH_BG_TITLE % self.laytonState.getNazoData().getBgSubIndex())
        if self.bgTitleScreen == None:
            self.bgTitleScreen = Surface(RESOLUTION_NINTENDO_DS)

        self.aniTitle = getBottomScreenAnimFromPath(self.laytonState, PATH_ANI_TITLE)
        self.__setupScrollingScreen()

        self._fader = Fader(200, initialActiveState=False, invertOutput=True, callbackOnDone=self._doOnTopScreenFinishMove)
        self._posTitle = (0,RESOLUTION_NINTENDO_DS[1])
        self.screenController.fadeIn(callback=self._startAnimation)
        
    def update(self, gameClockDelta):
        self._fader.update(gameClockDelta)
        if self._fader.getActiveState() and self._posTitle[1] != 0:
            self._posTitle = (0, round(RESOLUTION_NINTENDO_DS[1] * self._fader.getStrength()))

        # TODO - Make more asynchronous, so audio blips can happen at correct timing even when FPS is low
        if self._doCountdownAnim:
            difference = round(self._countPicaratDifference * self._fader.getStrength())
            if difference == self._countPicaratDifference:
                self._doCountdownAnim = False

            self.rendererPicaratBig.setText(self.laytonState.getNazoData().getPicaratStage(0) - difference)

    def draw(self, gameDisplay):
        if self._drawPicarats:
            self.rendererPicaratBig.drawBiased(gameDisplay)
            self.rendererPicaratSmall.drawBiased(gameDisplay)
            self.rendererPicaratTotal.drawBiased(gameDisplay)
        gameDisplay.blit(self.bgTitleScreen, self._posTitle)
    
    def doOnKill(self):
        self.screenController.fadeOut(callback=self.callbackOnTerminate)
        return super().doOnKill()

    def _startAnimation(self):
        self._fader.setActiveState(True)

    def _doOnTopScreenFinishMove(self):
        self._posTitle = (0,0)
        self.screenController.fadeOutMain(0)
        self._fader.setCallback(self._doOnTopScreenWaitFinish)
        self._fader.setDurationInFrames(24)
    
    def _doOnTopScreenWaitFinish(self):
        self.screenController.setBgMain(PATH_BG_PICARAT % self.laytonState.language.value)
        self.screenController.fadeInMain(callback=self._doPicaratDecayAnim)
        self._drawPicarats = True
    
    def _doPicaratDecayAnim(self):
        self._fader.setCallback(callback=self._doAfterPicaratDecayAnim)
        self._fader.setDurationInFrames(self._countPicaratDifference)
        self._doCountdownAnim = True
    
    def _doAfterPicaratDecayAnim(self):
        self._fader.setCallback(callback=self.doOnKill)
        self._fader.setDuration(1250)

    def __setupScrollingScreen(self):
        posYTitleText = 0
        if self.aniTitle != None:

            def getVariablePosition(nameVar):
                variable = self.aniTitle.getVariable(nameVar)
                if variable == None:
                    variable = (0,0)
                return variable
            
            def drawOnBgSurface(animName, posVarName):
                # TODO - Variables are grabbed as a list, not tuple. This could break
                self.aniTitle.setAnimationFromName(animName)
                self.aniTitle.setPos(getVariablePosition(posVarName))
                self.aniTitle.draw(self.bgTitleScreen)

            drawOnBgSurface("nazo", "pos2")
            drawOnBgSurface("puzzle", "pos3")

            # WiFi-specific and behaviour here
            # TODO - The game messes back and forth with sbj and spr. So any changes to ROM
            #        need to be done with both images, or widebrim must support arj images
            if self.laytonState.getCurrentNazoListEntry != None:
                nzLstEntry = self.laytonState.getCurrentNazoListEntry()
                if nzLstEntry.idInternal == 206:
                    # Question mode?
                    self.aniTitle.setAnimationFromName("question")
                    for x in [185,155,125]:
                        self.aniTitle.setPos((x,50))
                        self.aniTitle.draw(self.bgTitleScreen)
                elif 153 < nzLstEntry.idExternal:
                    # WiFi
                    self.aniTitle.setAnimationFromName("w")
                    self.aniTitle.setPos((115,50))
                    self.aniTitle.draw(self.bgTitleScreen)
                    # TODO - Implement the rest - 27_Intro_Unk
                elif self.aniTitle.getVariable("pos") != None:
                    fontQNumber = getNumberFontRendererFromImage(self.aniTitle)
                    fontQNumber.setText(nzLstEntry.idExternal)
                    fontQNumber.setUsePadding(True)
                    fontQNumber.drawBiased(self.bgTitleScreen, fromRight=True)

            posYTitleText = getVariablePosition("title")[1]

        fontRenderer = StaticTextHelper(self.laytonState.fontEvent)
        fontRenderer.setText(self.laytonState.getNazoData().textName)
        fontRenderer.setPos((0, posYTitleText))
        fontRenderer.drawXCentered(self.bgTitleScreen)