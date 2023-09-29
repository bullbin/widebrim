from .base import BaseQuestionObject
from ....engine.const import RESOLUTION_NINTENDO_DS
from ....madhatter.typewriter.strings_lt2 import OPCODES_LT2
from pygame import MOUSEBUTTONDOWN, Surface

class HandlerOnOff2(BaseQuestionObject):
    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)
        
        self._posCorner = (0,0)
        self._boardDimensions = (0,0)
        self._tileDimensions = (0,0)
        self._colourOverlay = (0,0,0,255)
        self._colourOverlaySurface = None

        self._tilesSelected = []
        self._tilesSolution = []
        self._tilesExcluded = []

        self._isValid = False
    
    def _wasAnswerSolution(self):
        for solution in self._tilesSolution:
            if solution not in self._tilesSelected:
                return False
        return len(self._tilesSelected) == len(self._tilesSolution)
    
    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.SetTileOnOff2Info.value and len(operands) == 10:
            self._posCorner = (operands[0].value, operands[1].value + RESOLUTION_NINTENDO_DS[1])
            self._boardDimensions = (operands[2].value, operands[3].value)
            self._tileDimensions = (operands[4].value, operands[5].value)
            self._colourOverlay = (operands[6].value << 3, operands[7].value << 3,
                                   operands[8].value << 3, operands[9].value << 3)
        elif opcode == OPCODES_LT2.AddTileOnOff2Check.value and len(operands) == 4:
            for x in range(operands[2].value):
                for y in range(operands[3].value):
                    self._tilesSolution.append((operands[0].value + x, operands[1].value + y))
        elif opcode == OPCODES_LT2.AddTileOnOff2Disable.value and len(operands) == 4:
            for x in range(operands[2].value):
                for y in range(operands[3].value):
                    self._tilesExcluded.append((operands[0].value + x, operands[1].value + y))
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True

    def doOnComplete(self):
        tileDimensionX, tileDimensionY = self._tileDimensions
        if tileDimensionX != 0 and tileDimensionY != 0:
            self._isValid = True
            self._colourOverlaySurface = Surface(self._tileDimensions)
            self._colourOverlaySurface.fill((self._colourOverlay[0], self._colourOverlay[1], self._colourOverlay[2]))
            self._colourOverlaySurface.set_alpha(self._colourOverlay[3])
        return super().doOnComplete()
    
    def drawPuzzleElements(self, gameDisplay):
        super().drawPuzzleElements(gameDisplay)
        for tilePos in self._tilesSelected:
            screenPos = (tilePos[0] * self._tileDimensions[0] + self._posCorner[0],
                         tilePos[1] * self._tileDimensions[1] + self._posCorner[1])
            gameDisplay.blit(self._colourOverlaySurface, screenPos)
        
    def handleTouchEventPuzzleElements(self, event):
        if self._isValid and event.type == MOUSEBUTTONDOWN:
            # TODO - Check if button-like anim behaviour, probably not
            eventPos = event.pos
            eventPos = (eventPos[0] - self._posCorner[0], eventPos[1] - self._posCorner[1])
            eventPos = (eventPos[0] // self._tileDimensions[0], eventPos[1] // self._tileDimensions[1])
            if (0 <= eventPos[0] < self._boardDimensions[0] and 0 <= eventPos[1] < self._boardDimensions[1]):
                if not(eventPos in self._tilesExcluded):
                    if eventPos in self._tilesSelected:
                        self._tilesSelected.remove(eventPos)
                    else:
                        self._tilesSelected.append(eventPos)
                    return True
        return super().handleTouchEventPuzzleElements(event)