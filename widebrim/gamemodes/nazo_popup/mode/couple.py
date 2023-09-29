from widebrim.gamemodes.nazo_popup.mode.const import PATH_ANI_COUPLE
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath
from pygame import Rect
from pygame.draw import rect
from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from .base import BaseQuestionObject
from widebrim.madhatter.typewriter.strings_lt2 import OPCODES_LT2

class Jar():
    def __init__(self, surfaceOff, surfaceOn, jarType, x, y):
        pass

class HandlerCouple(BaseQuestionObject):
    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)

        self._assets = getBottomScreenAnimFromPath(laytonState, PATH_ANI_COUPLE)

        self.jars = []
        self._collisionRects = []

        self._lengthColliders = 0
        self._lengthJars = 0
        self._offsetX = 0
        self._offsetY = 0x50 + RESOLUTION_NINTENDO_DS[1]
    
    def hasSubmitButton(self):
        return False
    
    def drawPuzzleElements(self, gameDisplay):
        for collider in self._collisionRects:
            rect(gameDisplay, (255,255,255), collider)
        return super().drawPuzzleElements(gameDisplay)

    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.Couple_SetInfo.value and len(operands) == 3:
            self._lengthColliders = operands[1].value
            self._lengthJars = operands[0].value
            self._offsetX = operands[2].value
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True
    
    def doOnComplete(self):
        for collider in range(min(16, self._lengthColliders)):
            self._collisionRects.append(Rect(self._offsetX, self._offsetY, 16, 32))
            self._offsetX += self._collisionRects[-1].width

        for indexJar in range(min(16, self._lengthJars, self._lengthColliders)):
            pass

        return super().doOnComplete()