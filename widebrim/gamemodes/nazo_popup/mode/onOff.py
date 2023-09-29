from typing import List
from .base import BaseQuestionObject
from .const import PATH_ANI_ONOFF
from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.engine.anim.button import StaticButton
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath
from widebrim.madhatter.typewriter.strings_lt2 import OPCODES_LT2

class OnOffButton(StaticButton):
    def __init__(self, pos, surfaceButton, callback):
        super().__init__(pos, surfaceButton, callback=callback, targettedOffset=(0,0))
        self._isHidden = True
    
    def doBeforePressedCallback(self):
        self._isHidden = not(self._isHidden)
        return super().doBeforePressedCallback()
    
    def getEnabledState(self):
        return not(self._isHidden)
    
    def reset(self):
        self._isHidden = True

    def draw(self, gameDisplay):
        if not(self._isHidden):
            super().draw(gameDisplay)

# TODO - OnOff has two variants, 3 and 14
#        There is no difference in functionality other than sounds,
#        which is also determined by puzzle ID

class HandlerOnOff(BaseQuestionObject):
    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)
        self._buttons : List[OnOffButton] = []
        self._buttonsEnabledSolution = []
    
    def hasRestartButton(self):
        return False
    
    def _wasAnswerSolution(self):
        for indexButton, button in enumerate(self._buttons):
            if button.getEnabledState() != self._buttonsEnabledSolution[indexButton]:
                return False
        return True
    
    def drawPuzzleElements(self, gameDisplay):
        for button in self._buttons:
            button.draw(gameDisplay)
        return super().drawPuzzleElements(gameDisplay)
    
    def handleTouchEventPuzzleElements(self, event):
        for button in self._buttons:
            if button.handleTouchEvent(event):
                return True
        return super().handleTouchEventPuzzleElements(event)
    
    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.AddOnOffButton.value and len(operands) == 5:
            buttonAnim = getBottomScreenAnimFromPath(self.laytonState, PATH_ANI_ONOFF % operands[2].value)
            if len(self._buttons) < 24 and buttonAnim != None and buttonAnim.setAnimationFromIndex(1) and buttonAnim.getActiveFrame() != None:
                pos = (operands[0].value, operands[1].value + RESOLUTION_NINTENDO_DS[1])
                self._buttons.append(OnOffButton(pos, buttonAnim.getActiveFrame(), None))
                self._buttonsEnabledSolution.append(operands[3].value != 0)
            else:
                return False
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True