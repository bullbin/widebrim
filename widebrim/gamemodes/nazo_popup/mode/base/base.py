from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Union
from widebrim.engine.anim.button import AnimatedButton, AnimatedClickableButton
from widebrim.gamemodes.nazo_popup.mode.base.const import NAME_ANIM_HINT_OFF, NAME_ANIM_HINT_ON, PATH_ANIM_HINT_GLOW, POS_ANIM_HINT_GLOW
from widebrim.gamemodes.nazo_popup.mode.base.screenHint import BottomScreenOverlayHint
from widebrim.gamemodes.nazo_popup.mode.base.screenQuit import BottomScreenOverlayQuit
from widebrim.gamemodes.nazo_popup.mode.base.screenTutorial import BottomScreenOverlayTutorial, shouldTutorialSpawn
if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController

from widebrim.engine.state.enum_mode import GAMEMODES
from widebrim.engine.const import PATH_PUZZLE_SCRIPT, PATH_PACK_PUZZLE, PATH_PUZZLE_BG, PATH_PUZZLE_BG_LANGUAGE, PATH_PUZZLE_BG_NAZO_TEXT, RESOLUTION_NINTENDO_DS
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getButtonFromPath, getClickableButtonFromPath, offsetVectorToSecondScreen
from widebrim.engine.anim.font.scrolling import ScrollingFontHelper
from widebrim.engine.anim.image_anim import ImageFontRenderer
from widebrim.engine.anim.fader import Fader
from widebrim.gamemodes.core_popup.script import ScriptPlayer
from widebrim.madhatter.hat_io.asset_script import GdScript
from widebrim.gamemodes.nazo_popup.mode.const import ANIM_TOUCH_5BIT_ALPHA_BOUNDS, PATH_ANI_BTN_HINT, PATH_ANI_BTN_HINT_WIFI, PATH_ANI_SUB_TEXT, PATH_ANI_BTN_MEMO, PATH_ANI_BTN_QUIT, PATH_ANI_BTN_RESTART, PATH_ANI_BTN_SUBMIT, PATH_ANI_WAIT_FOR_TOUCH

from pygame import MOUSEBUTTONDOWN, MOUSEBUTTONUP

# TODO - What happens if the scroller draws too many lines for the top screen? Does it go to the bottom?
# TODO - Fix popup... ScriptPlayer has its own system. But this should operate after completion.

# TODO - This is from intro...
def getNumberFontRendererFromImage(anim, varName):
    if anim != None:
        output = ImageFontRenderer(anim)
        if anim.getVariable(varName) != None:
            xRightmost  = anim.getVariable(varName)[0]
            y           = anim.getVariable(varName)[1]
            stride      = anim.getVariable(varName)[2]
            maxNum      = anim.getVariable(varName)[5]

            output.setPos((xRightmost,y))
            output.setStride(stride)
            output.setMaxNum(maxNum)
        
        return output
    return None

class BaseQuestionObject(ScriptPlayer):

    POS_QUESTION_TEXT = (13,22)

    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, GdScript())

        self._callbackOnTerminate = callbackOnTerminate

        nzLstEntry = laytonState.getCurrentNazoListEntry()
        nazoData = laytonState.getNazoData()

        # TODO - Do not disable hint button - all other buttons are disabled
        self.__useButtons = True

        # TODO - Per-handler X limiting
        self.__puzzleXLimit = RESOLUTION_NINTENDO_DS[0]
        
        self.__isPuzzleElementsActive = False
        self.__scrollerPrompt = ScrollingFontHelper(self.laytonState.fontQ, yBias=2)
        self.__scrollerPrompt.setPos(BaseQuestionObject.POS_QUESTION_TEXT) # Verified, 27_Question_MaybeDrawTopText

        self.__animSubText = getBottomScreenAnimFromPath(laytonState, PATH_ANI_SUB_TEXT)
        self.__animHintGlow = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_HINT_GLOW, pos=POS_ANIM_HINT_GLOW)

        self._loadPuzzleBg()
        if nazoData != None:
            self.screenController.setBgSub(PATH_PUZZLE_BG_NAZO_TEXT % nazoData.bgSubId)
            self.__scrollerPrompt.setText(nazoData.getTextPrompt())

        # Some wifi check here
        
        # Initialise script
        if nzLstEntry != None:
            scriptData = laytonState.getFileAccessor().getPackedData(PATH_PUZZLE_SCRIPT, PATH_PACK_PUZZLE % nzLstEntry.idInternal)
            if scriptData != None:
                self._script.load(scriptData)

        # Set end gamemode on finish
        # TODO - Gamemode 11 used?
        if laytonState.getGameModeNext() not in [GAMEMODES.UnkNazo, GAMEMODES.Room,
                                                 GAMEMODES.JitenBag, GAMEMODES.JitenWiFi,
                                                 GAMEMODES.JitenSecret, GAMEMODES.Challenge,
                                                 GAMEMODES.Nazoba]:
            laytonState.setGameModeNext(GAMEMODES.EndPuzzle)

        # TODO - Create hint mode popup and buttons to grab
        self.__buttons = []
        self.__btnHintLevel = -1
        self.__btnHint : Optional[Union[AnimatedButton, AnimatedClickableButton]] = None
        self.__btnHintWiFiPathway = False
        self.__getButtons()

        self.__screenHint   = BottomScreenOverlayHint(laytonState, screenController, self.__switchFromHintMode)
        self.__inHintMode   = False
        
        self.__popup        : Optional[BottomScreenOverlayHint] = None

        self._isTerminating = False
        self.__isInteractingWithPuzzle = False
        self.__hasDoneInitialTouch = False

        def resetFader():
            self.__faderTouchAlpha.reset()
            self.__faderTouchAlpha.setInvertedState(not(self.__faderTouchAlpha.getInvertedState()))

        self.__faderTouchAlpha = Fader(0, callbackOnDone=resetFader, callbackClearOnDone=False)
        self.__faderTouchAlpha.setDurationInFrames(60)

        self.__animWaitForTouch = getBottomScreenAnimFromPath(laytonState, PATH_ANI_WAIT_FOR_TOUCH)
        if self.__animWaitForTouch != None:
            # TODO - Replicate the anim width and height getters. Uses current frame to get values, solving some button issues elsewhere
            self.__animWaitForTouch.setPos((0, RESOLUTION_NINTENDO_DS[1]))
            if (surface := self.__animWaitForTouch.getActiveFrame()) != None:
                width = surface.get_width()
                height = surface.get_height()
                pos = offsetVectorToSecondScreen(((RESOLUTION_NINTENDO_DS[0] - width) // 2, (RESOLUTION_NINTENDO_DS[1] - height) // 2))
                self.__animWaitForTouch.setPos(pos)
            self.__setAnimTouchAlpha()

    def __updateHintButtonLevel(self):
        if self.__btnHint != None:
            if not(self.__btnHintWiFiPathway):
                # TODO - Add hint level getter to state
                targetLevel = None
                if (nzLstEntry := self.laytonState.getCurrentNazoListEntry()) != None:
                    puzzleData = self.laytonState.saveSlot.puzzleData.getPuzzleData(nzLstEntry.idExternal - 1)
                    if puzzleData != None:
                        targetLevel = puzzleData.levelHint
                if targetLevel != None and targetLevel != self.__btnHintLevel:
                    self.__btnHintLevel = targetLevel
                    self.__btnHint.setAnimNameUnpressed(NAME_ANIM_HINT_OFF % self.__btnHintLevel)
                    self.__btnHint.setAnimNamePressed(NAME_ANIM_HINT_ON % self.__btnHintLevel)

    def __switchToTutorialMode(self):
        if shouldTutorialSpawn(self.laytonState):
            self.__popup = BottomScreenOverlayTutorial(self.laytonState, self.screenController, self.__callbackOnRemovePopup)

    def __switchToHintMode(self):
        self.__screenHint.doBeforeSwitching()
        self.__inHintMode = True

    def __switchFromHintMode(self):
        self._loadPuzzleBg()
        self.__updateHintButtonLevel()
        self.__inHintMode = False

    def __enablePuzzleElements(self):
        self.__isPuzzleElementsActive = True
    
    def __disablePuzzleElements(self):
        self.__isPuzzleElementsActive = False
    
    def __getPuzzleElementsEnabledState(self):
        return self.__isPuzzleElementsActive

    def _doUnpackedCommand(self, opcode, operands):
        # Puzzles stub out all other commands, so always return False
        return False
    
    def _doReset(self):
        pass

    def _setButtonEnabled(self):
        pass

    def __setAnimTouchAlpha(self):
        lower, upper = ANIM_TOUCH_5BIT_ALPHA_BOUNDS
        diff = (upper - lower) * self.__faderTouchAlpha.getStrength()
        self.__animWaitForTouch.setAlpha5Bit(lower + diff)

    def update(self, gameClockDelta):
        # TODO - Maybe patch update on doOnComplete from script to ensure that unintended blocking behaviour from calling bad commands
        #        doesn't lead the puzzle handler to start prematurely (even though this would be an invalid state)
        if not(self._isTerminating):
            super().update(gameClockDelta)
            if self.__getPuzzleElementsEnabledState():
                if self.__hasDoneInitialTouch:
                    if self.__inHintMode:
                        self.__screenHint.update(gameClockDelta)
                    elif self.__popup != None:
                        self.__popup.update(gameClockDelta)
                    else:
                        self.updatePuzzleElements(gameClockDelta)
                else:
                    if self.__animWaitForTouch != None:
                        self.__setAnimTouchAlpha()
                        self.__animWaitForTouch.update(gameClockDelta)
                        self.__faderTouchAlpha.update(gameClockDelta)
                    self.__scrollerPrompt.update(gameClockDelta)
                
                # TODO - when to flash hint button?
                if self.__useButtons:
                    for button in self.__buttons:
                        button.update(gameClockDelta)
                if self.__animHintGlow != None and not(self.__btnHintWiFiPathway):
                    self.__animHintGlow.update(gameClockDelta)
        
        self.__screenHint.update(gameClockDelta)
    
    def draw(self, gameDisplay):
        super().draw(gameDisplay)
        self.__drawSubScreenOverlay(gameDisplay)
        self.__scrollerPrompt.draw(gameDisplay)

        if self.__inHintMode:
            self.__screenHint.draw(gameDisplay)
        elif self.__popup != None:
            self.__popup.draw(gameDisplay)
        else:
            if self.__useButtons:
                for button in self.__buttons:
                    button.draw(gameDisplay)
            
            if self.__animHintGlow != None and not(self.__btnHintWiFiPathway):
                self.__animHintGlow.draw(gameDisplay)

            self.drawPuzzleElements(gameDisplay)

            if not(self.__hasDoneInitialTouch):
                if self.__animWaitForTouch != None:
                    self.__animWaitForTouch.draw(gameDisplay)
    
    def _setPuzzleTouchBounds(self, xLimit):
        self.__puzzleXLimit = xLimit
    
    def _disableButtons(self):
        self.__useButtons = False

    def _enableButtons(self):
        self.__useButtons = True
    
    def handleTouchEvent(self, event):
        # TODO - TOUCH! animation
        if not(self._isTerminating):
            # TODO - Get mouse region, it's somewhere in binary
            if self.__hasDoneInitialTouch:
                if self.__inHintMode:
                    if self.__screenHint.handleTouchEvent(event):
                        return True
                elif self.__popup != None:
                    if self.__popup.handleTouchEvent(event):
                        return True
                else:
                    if self.__useButtons:
                        for button in self.__buttons:
                            if button.handleTouchEvent(event):
                                return True

                    if event.type == MOUSEBUTTONDOWN:
                        x,y = event.pos
                        if 0 <= x < self.__puzzleXLimit:
                            self.__isInteractingWithPuzzle = True
                        else:
                            self.__isInteractingWithPuzzle = False
                    
                    if self.__isInteractingWithPuzzle:
                        x, y = event.pos
                        if x > self.__puzzleXLimit:
                            x = self.__puzzleXLimit
                        if y < RESOLUTION_NINTENDO_DS[1]:
                            y = RESOLUTION_NINTENDO_DS[1]
                        event.pos = x,y
                        self.handleTouchEventPuzzleElements(event)
                    
                        if event.type == MOUSEBUTTONUP:
                            self.__isInteractingWithPuzzle = False
                        # TODO - Should return handleTouchEventPuzzleElements probably
                        return True
            else:
                if event.type == MOUSEBUTTONUP:
                    self.__hasDoneInitialTouch = True
                    self.__scrollerPrompt.skip()
                    self.__switchToTutorialMode()
                    return True
        return False

    def updatePuzzleElements(self, gameClockDelta):
        pass

    def drawPuzzleElements(self, gameDisplay):
        pass

    def handleTouchEventPuzzleElements(self, event):
        return False

    def _wasAnswerSolution(self):
        return False

    def _startJudgement(self):
        self.laytonState.wasPuzzleSolved = self._wasAnswerSolution()
        self._isTerminating = True
        self.screenController.fadeOut(callback=self._callbackOnTerminate)

    def _doOnJudgementPress(self):
        self._startJudgement()

    def doOnComplete(self):
        # Start puzzle, so fade in...
        # Override kill behaviour, since this indicates puzzle script has finished loading
        self.screenController.fadeIn(callback=self.__enablePuzzleElements)
        pass

    def hasQuitButton(self):
        return True
    
    def hasMemoButton(self):
        return True
    
    def hasSubmitButton(self):
        return True
    
    def hasRestartButton(self):
        return True
    
    def __getButtons(self):

        def addIfNotNone(button):
            if button != None:
                self.__buttons.append(button)
        
        if (nzLstEntry := self.laytonState.getCurrentNazoListEntry()) != None:
            # TODO - Constants on story puzzles...
            if 0 < nzLstEntry.idExternal < 0x9a:
                self.__btnHint = getButtonFromPath(self.laytonState, PATH_ANI_BTN_HINT, self.__switchToHintMode)
            else:
                self.__btnHintWiFiPathway = True
                self.__btnHint = getClickableButtonFromPath(self.laytonState, PATH_ANI_BTN_HINT_WIFI, self.__switchToHintMode)
            addIfNotNone(self.__btnHint)
            self.__updateHintButtonLevel()

        if self.hasQuitButton():
            addIfNotNone(getButtonFromPath(self.laytonState, PATH_ANI_BTN_QUIT, callback=self.__doQuit))
        if self.hasMemoButton():
            addIfNotNone(getButtonFromPath(self.laytonState, PATH_ANI_BTN_MEMO))
        if self.hasRestartButton():
            addIfNotNone(getButtonFromPath(self.laytonState, PATH_ANI_BTN_RESTART, callback=self._doReset))
        if self.hasSubmitButton():
            addIfNotNone(getButtonFromPath(self.laytonState, PATH_ANI_BTN_SUBMIT, callback=self._doOnJudgementPress))

    def __callbackOnQuit(self):
        self.laytonState.wasPuzzleSkipped = True
        self.screenController.fadeOut(callback=self._callbackOnTerminate)
    
    def __callbackOnRemovePopup(self):
        self.__popup = None
        self._loadPuzzleBg()

    def __doQuit(self):
        self.__popup = BottomScreenOverlayQuit(self.laytonState, self.screenController, self.__callbackOnRemovePopup, self.__callbackOnQuit, self.__animSubText)

    def _loadPuzzleBg(self):
        nzLstEntry = self.laytonState.getCurrentNazoListEntry()
        nazoData = self.laytonState.getNazoData()

        # Set backgrounds
        if nazoData != None and nzLstEntry != None:
            if nazoData.isBgPromptLanguageDependent():
                self.screenController.setBgMain(PATH_PUZZLE_BG_LANGUAGE % nazoData.bgMainId)
            else:
                self.screenController.setBgMain(PATH_PUZZLE_BG % nazoData.bgMainId)

    def __drawSubScreenOverlay(self, gameDisplay):
        # TODO - 27_Question_MaybeDrawTopText
        # TODO - Probably more efficient to create a surface and cache this, since it only changes with hint coin usage
        nzLstEntry = self.laytonState.getCurrentNazoListEntry()
        if nzLstEntry != None and self.__animSubText != None:

            def drawFromVariable(nameVar, nameAnim):
                posVars = self.__animSubText.getVariable(nameVar)
                if posVars != None:
                    self.__animSubText.setAnimationFromName(nameAnim)
                    self.__animSubText.setPos((posVars[0], posVars[1]))
                    self.__animSubText.draw(gameDisplay)
            
            def drawFontRenderer(nameVar, text, usePadding=False):
                fontRenderer = getNumberFontRendererFromImage(self.__animSubText, nameVar)
                fontRenderer.setUsePadding(usePadding)
                fontRenderer.setText(text)
                fontRenderer.drawBiased(gameDisplay)
                
            drawFromVariable("nazo_p", "nazo")
            
            if nzLstEntry.idInternal == 206:
                # Unk?
                pass
            elif nzLstEntry.idExternal < 154:
                # Standard
                drawFromVariable("pk_p", "pk")
                drawFromVariable("hint_p", "hint")

                picaratSlot = self.laytonState.saveSlot.puzzleData.getPuzzleData((self.laytonState.getNazoData().idExternal - 1))
                if picaratSlot != None:
                    picaratSlot = picaratSlot.levelDecay
                else:
                    picaratSlot = 0

                drawFontRenderer("pos", nzLstEntry.idExternal, usePadding=True)
                drawFontRenderer("pos2", self.laytonState.getNazoData().getPicaratStage(picaratSlot))
                drawFontRenderer("pos3", self.laytonState.getNazoData().getPicaratStage(0))
                drawFontRenderer("pos4", self.laytonState.saveSlot.hintCoinAvailable)
            else:
                # WiFi
                drawFromVariable("w_p", "w")