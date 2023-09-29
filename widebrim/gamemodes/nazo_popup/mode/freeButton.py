from .base import BaseQuestionObject
from .const import PATH_ANI_FREEBUTTON
from ....engine_ext.utils import getButtonFromPath
from ....madhatter.typewriter.strings_lt2 import OPCODES_LT2

class  HandlerFreeButton(BaseQuestionObject):
    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)
        self.buttons = []
        self.solutions = []
        self.indexButtonPress = None
        self.laytonState = laytonState
    
    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.AddOnOffButton.value and len(operands) == 5:
            if len(self.buttons) < 24:
                self.buttons.append(getButtonFromPath(self.laytonState, PATH_ANI_FREEBUTTON % operands[2].value, pos=(operands[0].value, operands[1].value), callback=self._startJudgement))
                self.solutions.append(operands[3].value == 1)
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True

    def hasSubmitButton(self):
        return False
    
    def hasRestartButton(self):
        return False

    def _wasAnswerSolution(self):
        if len(self.solutions) > self.indexButtonPress:
            return self.solutions[self.indexButtonPress]
        return False

    def drawPuzzleElements(self, gameDisplay):
        for button in self.buttons:
            if button != None:
                button.draw(gameDisplay)
        return super().drawPuzzleElements(gameDisplay)
    
    def updatePuzzleElements(self, gameClockDelta):
        for button in self.buttons:
            if button != None:
                button.update(gameClockDelta)
        return super().updatePuzzleElements(gameClockDelta)
    
    def handleTouchEventPuzzleElements(self, event):
        for indexButton, button in enumerate(self.buttons):
            if button != None:
                self.indexButtonPress = indexButton
                if button.handleTouchEvent(event):
                    return True
        return super().handleTouchEventPuzzleElements(event)