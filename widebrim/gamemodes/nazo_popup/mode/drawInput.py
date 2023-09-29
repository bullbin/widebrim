# SetDrawInputBG
# BG name

# SetAnswerBox 4
# Index box
# MaybePosX - Verified unused
# MaybePosY - Verified unused
# Length

# SetAnswer
# Index box
# Text

# 60 x 70

# This handler isn't well researched...
# The game originally uses Zi Corporation's Decuma handwriting engine
#     This has not been reversed, too much work for minimal return
# Instead, Google's Tesseract engine is used. Nowhere near as fast or accurate!

# TODO - Puzzles like Pass the Apples, what happens with 1 empty square? Same for the fountain one
# TODO - Thread safe digit display
# TODO - Skip if tesseract unusable

from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.madhatter.common import log
from ....engine_ext.utils import getButtonFromPath
from .base import BaseQuestionObject
from .const import PATH_BG_DRAWINPUT
from ....madhatter.typewriter.strings_lt2 import OPCODES_LT2
from pygame import Surface, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from pygame.image import tostring
from pygame.draw import line

from threading import Thread
import pytesseract
from PIL import Image

# TODO - Switch rendering to draw on an invisible or virtual surface before recognition
#        This is because the OCR engine is limited by the resolution of the surface.
#            Smaller handwriting has HORRIBLE accuracy, and thin text doesn't get recognised!
# TODO - Retrain Tesseract on MNIST or switch to basic ML model
# TODO - Does this have a restart button?

# TODO - Consts where?
WIDTH_PEN = 4
PATH_ANI_BTN_DRAWINPUT_SUBMIT   = "nazo/drawinput/%s/di_hantei.spr"
PATH_ANI_BTN_BACK               = "nazo/drawinput/%s/di_modoru.spr"
PATH_ANI_BTN_CLEAR              = "nazo/drawinput/%s/di_allreset.spr"

# TODO - Class for moveable elements
class DrawInputBox():

    SIZE_MED = (60,70)
    SIZE_BIG = (80,80)

    def __init__(self, pos=(0,0), useAlphabet=False, size=SIZE_BIG):
        self._drawSurface = Surface(size)
        self._colourKey = (255,255,255)
        self._drawSurface.set_colorkey(self._colourKey)

        if useAlphabet:
            self.charFilter = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
        else:
            self.charFilter = "0123456789"

        self._clearSurface()

        self._colourLine = (0,0,0)
        self._pos = pos
        self._isDrawSurfaceUpdated = True
        self._handwritingSymbol = None
        self._isSymbolReady = True

        self._threadOcrActive = None
        self._threadOcrWaiting = None

        self._isPenDrawing = False

    def _clearSurface(self):
        self._drawSurface.fill(self._colourKey)
    
    def getAnswerForce(self):
        # Force join thread to get answer. Only useful for final submission
        if self._threadOcrActive != None:
            self._threadOcrActive.join()
        self._threadOcrWaiting = None
        return self._handwritingSymbol
    
    def clearAnswer(self):
        if self._threadOcrActive != None:
            self._threadOcrActive.join()
        self._threadOcrWaiting = None
        self._handwritingSymbol = None
        self._isDrawSurfaceUpdated = True
        self._isSymbolReady = True
        self._clearSurface()

    def setPos(self, pos):
        self._pos = pos

    def _deployThreads(self):
        if self._threadOcrActive != None:
            if not(self._threadOcrActive.is_alive()):
                self._threadOcrActive = None
        if self._threadOcrActive == None and self._threadOcrWaiting != None:
            self._threadOcrActive = self._threadOcrWaiting
            self._threadOcrWaiting = None
            self._threadOcrActive.start()

    def update(self, gameClockDelta):
        self._deployThreads()

    def draw(self, gameDisplay):
        gameDisplay.blit(self._drawSurface, self._pos)
    
    def _queueHandwritingRecognition(self):

        def startTesseractLoading(imageCopy):
            log("Performing handwriting recognition...", name="TssrctOCR")
            im = Image.frombytes("RGBA",(imageCopy.get_width(), imageCopy.get_height()),
                                         tostring(imageCopy,"RGBA",False))
            self._handwritingSymbol = pytesseract.image_to_string(im,config="--psm 10 -c tessedit_char_whitelist=" + self.charFilter)
            if len(self._handwritingSymbol) > 0:
                if self._handwritingSymbol[0] in self.charFilter:
                    # TODO - Capitalise symbol
                    self._handwritingSymbol = self._handwritingSymbol[0]
                else:
                    self._handwritingSymbol = "?"
            else:
                self._handwritingSymbol = "?"

            # TODO - Adjust character type based on handler
            log(self._handwritingSymbol, name="TssrctOCR")
            self._isSymbolReady = True

        # Make copy of surface to keep thread-safe, and lock the handwriting symbol until thread finished
        self._isSymbolReady = False
        surfCopy = self._drawSurface.copy()
        self._threadOcrWaiting = Thread(target=startTesseractLoading, args=(surfCopy,))
        self._deployThreads()

    def _drawLineToCurrentPoint(self, pos):
        # TODO - Generalise a clamp function for pen point, since used globally right now to tie inputs to bottom screen
        # TODO - Lock to mouse button 1

        def clampPoint(point):

            def clamp(data, minimum, maximum):
                return max(minimum, min(data, maximum))

            point = (clamp(point[0], self._pos[0], self._pos[0] + self._drawSurface.get_width()),
                     clamp(point[1], self._pos[1], self._pos[1] + self._drawSurface.get_height()))
            return point
        
        def offsetPoint(point):
            return (point[0] - self._pos[0], point[1] - self._pos[1])

        offsetLastPoint = offsetPoint(clampPoint(self._penLastPoint))
        offsetPos = offsetPoint(clampPoint(pos))
        line(self._drawSurface, self._colourLine, offsetLastPoint, offsetPos, width=WIDTH_PEN)

    def handleTouchEvent(self, event):

        def checkInBounds(eventPos):
            if self._pos[0] <= event.pos[0] < self._pos[0] + self._drawSurface.get_width():
                return self._pos[1] <= event.pos[1] < self._pos[1] + self._drawSurface.get_height()
            return False

        if event.type == MOUSEBUTTONDOWN:
            if checkInBounds(event.pos):
                self._isPenDrawing = True
                self._penLastPoint = event.pos
                return True

        elif self._isPenDrawing:
            if event.type == MOUSEMOTION:
                self._drawLineToCurrentPoint(event.pos)
                self._penLastPoint = event.pos

            elif event.type == MOUSEBUTTONUP:
                self._isPenDrawing = False
                if self._penLastPoint != None:
                    self._drawLineToCurrentPoint(event.pos)
                    self._queueHandwritingRecognition()
                    self._penLastPoint = None
            return True
        return False

class DrawInputAnswer():
    def __init__(self, handlerId, length):
        self.boxes = []
        self.answer = None
        self.isAlphabetical = handlerId == 16
        self.handlerId = handlerId

        # The behaviour is verified but simplified here
        # These are 'accurate' - their OCR and pen methods are different so they're being adapted

        # TODO - Make constants
        if handlerId < 28:
            if length <= 2:
                size = DrawInputBox.SIZE_BIG
                cornerOffset = 57
            else:
                size = DrawInputBox.SIZE_MED
                cornerOffset = 66

            cornerPos = ((RESOLUTION_NINTENDO_DS[0] - (size[0] * length)) // 2,
                        cornerOffset + RESOLUTION_NINTENDO_DS[1])

            for indexBox in range(length):
                self.boxes.append(DrawInputBox(pos=(cornerPos[0] + (size[0] * indexBox), cornerPos[1]), size=size, useAlphabet=self.isAlphabetical))
        
        # These handlers all force their own answer length, so do not use the size from puzzle
        elif handlerId == 28:
            for posX in [0x39, 0x95]:
                self.boxes.append(DrawInputBox(pos=(posX - 5, 0x43 - 1 + RESOLUTION_NINTENDO_DS[1]), size=DrawInputBox.SIZE_MED, useAlphabet=self.isAlphabetical))
        elif handlerId == 32:
            for posX in [0x15,0x61,0xad]:
                # TODO - Is alphabet allowed?
                self.boxes.append(DrawInputBox(pos=(posX - 5, 0x43 - 1 + RESOLUTION_NINTENDO_DS[1]), size=DrawInputBox.SIZE_MED, useAlphabet=self.isAlphabetical))
        else:
            for posX in [0xb,0x47,0x87,0xc3]:
                self.boxes.append(DrawInputBox(pos=(posX - 5, 0x43 - 1 + RESOLUTION_NINTENDO_DS[1]), size=DrawInputBox.SIZE_MED, useAlphabet=self.isAlphabetical))

    def update(self, gameClockDelta):
        for box in self.boxes:
            box.update(gameClockDelta)

    def handleTouchEvent(self, event):
        for box in self.boxes:
            if box.handleTouchEvent(event):
                return True
        return False

    def draw(self, gameDisplay):
        for box in self.boxes:
            box.draw(gameDisplay)

    def setAnswer(self, answer):
        self.answer = answer
    
    def isAnswerValid(self):
        for box in self.boxes:
            if box.getAnswerForce() == "?":
                return False
        return True
    
    def isAnswerEmpty(self):
        if self.isAnswerValid():
            for box in self.boxes:
                answerChar = box.getAnswerForce()
                if answerChar != None and answerChar != " ":
                    return False
        return True
    
    def wasAnswerSolution(self):
        if self.isAnswerValid():
            answer = ""
            for box in self.boxes:
                answerChar = box.getAnswerForce()
                if answerChar == None:
                    answerChar = " "
                answer += answerChar
            log(self.answer, "got", answer, name="DrawInput")

            if self.isAlphabetical:
                # TODO - Is this stripped?
                return answer.upper() == self.answer.upper()
            else:
                if self.handlerId == 35:
                    firstNum = int(answer[:2])
                    secondNum = int(answer[2:])
                    answer = "%02d%02d" % (firstNum, secondNum)
                    return answer == self.answer
                elif self.handlerId == 28:
                    return answer == self.answer
                else:
                    return int(answer) == int(self.answer)
        return False

    def clearAnswer(self):
        for box in self.boxes:
            box.clearAnswer()

class HandlerDrawInput(BaseQuestionObject):
    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)
        self._pathBg = None
        self._answers = [None,None,None,None]
        self._inAnswerMode = False

        self.__buttons = []
        
        def addIfNotNone(button):
            if button != None:
                self.__buttons.append(button)
        
        addIfNotNone(getButtonFromPath(laytonState, PATH_ANI_BTN_DRAWINPUT_SUBMIT, callback=self._doOnSubmitAnswer))
        addIfNotNone(getButtonFromPath(laytonState, PATH_ANI_BTN_BACK, callback=self._doOnLeaveEntry))
        addIfNotNone(getButtonFromPath(laytonState, PATH_ANI_BTN_CLEAR, callback=self._doOnClearAnswer))
    
    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.SetAnswerBox.value and len(operands) == 4:
            # yeah idk how this works
            if 0 <= operands[0].value < len(self._answers):
                self._answers[operands[0].value] = DrawInputAnswer(self.laytonState.getNazoData().idHandler, operands[3].value)
            else:
                return False
        elif opcode == OPCODES_LT2.SetAnswer.value:
            if 0 <= operands[0].value < len(self._answers) and self._answers[operands[0].value] != None:
                self._answers[operands[0].value].setAnswer(operands[1].value)
            else:
                return False
        elif opcode == OPCODES_LT2.SetDrawInputBG.value and len(operands) == 1:
            self._pathBg = PATH_BG_DRAWINPUT % operands[0].value
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True
    
    def updatePuzzleElements(self, gameClockDelta):
        for answer in self._answers:
            if answer != None:
                answer.update(gameClockDelta)
        
        if self._inAnswerMode:
            for button in self.__buttons:
                button.update(gameClockDelta)

        return super().updatePuzzleElements(gameClockDelta)

    def drawPuzzleElements(self, gameDisplay):
        if self._inAnswerMode:
            for button in self.__buttons:
                button.draw(gameDisplay)
            for answer in self._answers:
                if answer != None:
                    answer.draw(gameDisplay)
        return super().drawPuzzleElements(gameDisplay)
    
    def handleTouchEventPuzzleElements(self, event):
        # TODO - Make one box. Idk what game is trying to do
        if self._inAnswerMode:
            for button in self.__buttons:
                if button.handleTouchEvent(event):
                    return True
            for answer in self._answers:
                if answer != None:
                    return answer.handleTouchEvent(event)
        return super().handleTouchEventPuzzleElements(event)

    def _doOnLeaveEntry(self):
        self._inAnswerMode = False

        # TODO - Clear answer text too!
        self._doOnClearAnswer()
        self._enableButtons()
        self._setPuzzleTouchBounds(RESOLUTION_NINTENDO_DS[1])
        self._loadPuzzleBg()

    def _wasAnswerSolution(self):
        # TODO - What happens if no answer provided?
        for answer in self._answers:
            if answer != None and answer.wasAnswerSolution():
                return True
        return False

    def _doOnSubmitAnswer(self):

        validAnswers = []
        for answer in self._answers:
            if answer != None and answer.isAnswerValid():
                validAnswers.append(answer)
        
        if len(validAnswers) > 0:
            hasNonEmptyAnswer = False
            for answer in validAnswers:
                if not(answer.isAnswerEmpty()):
                    hasNonEmptyAnswer = True
                    break
            
            if hasNonEmptyAnswer:
                self._startJudgement()
            else:
                log("Answer is empty!", name="DrawInput")
        else:
            # Do valid answer screen
            log("No valid answer available!", name="DrawInput")

    def _doOnClearAnswer(self):
        for answer in self._answers:
            if answer != None:
                answer.clearAnswer()

    def _doOnJudgementPress(self):
        # TODO - Disable touch when faders active
        # TODO - Fades between the two
        self._inAnswerMode = True
        self._disableButtons()
        # Allow use of whole screen for interaction
        self._setPuzzleTouchBounds(RESOLUTION_NINTENDO_DS[0])
        # TODO - Clear all handwriting on start
        self.screenController.setBgMain(self._pathBg)