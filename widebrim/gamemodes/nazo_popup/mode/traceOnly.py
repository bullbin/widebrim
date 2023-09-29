from widebrim.madhatter.common import logSevere
from ....engine.const import RESOLUTION_NINTENDO_DS
from ....madhatter.typewriter.strings_lt2 import OPCODES_LT2

from .base import BaseQuestionObject
from pygame import Surface, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from pygame.draw import polygon, line
from random import randint

# Points in LAYTON2 appear to already be pre-sorted,
#     so no convex hull is calculated

WIDTH_PEN = 3

class HandlerTraceOnly(BaseQuestionObject):

    MAX_COUNT_POINTS = 10

    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)
        self._surfaceSolution = Surface(RESOLUTION_NINTENDO_DS)
        
        # TODO - Solution bounding rect, intersect on complete
        # TODO - Is solution used? Game leaves it alone after init
        self._pointsIn = []
        self._pointsOut = []
        self._posFill = (0,0)

        # TODO - Abstract pen type, used by game frequently too. This is all from TraceButton
        self._penLastPoint = None
        self._penSurface = None
        self._isPenDrawing = False
        self._colourLine = (0,0,0)
        self._colourKey = (0,0,0)

        self._pointsLine = []
        self._lineIsSolution = False

    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.SetFillPos.value and len(operands) == 2:
            self._posFill = (operands[0].value, operands[1].value)
        elif opcode == OPCODES_LT2.AddInPoint.value and len(operands) == 2:
            if len(self._pointsIn) < HandlerTraceOnly.MAX_COUNT_POINTS:
                self._pointsIn.append((operands[0].value, operands[1].value))
        elif opcode == OPCODES_LT2.AddOutPoint.value and len(operands) == 2:
            if len(self._pointsOut) < HandlerTraceOnly.MAX_COUNT_POINTS:
                self._pointsOut.append((operands[0].value, operands[1].value))
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True
    
    def _wasAnswerSolution(self):
        # TODO - This is disgusting

        # Detect if user started or ended line outside the surface.
        for point in self._pointsLine:
            if self._surfaceSolution.get_at((point[0], point[1] - RESOLUTION_NINTENDO_DS[1])) == (0,0,0):
                return False
        
        def getIntersectionPoint(checkLineStart, checkLineEnd, collideLineStart, collideLineEnd):

            def getGradient(xStart, xEnd, yStart, yEnd):
                if xStart - xEnd == 0:
                    return None
                return (yEnd - yStart) / (xEnd - xStart)

            checkLineGradient = getGradient(checkLineStart[0], checkLineEnd[0], checkLineStart[1], checkLineEnd[1])
            collideLineGradient = getGradient(collideLineStart[0], collideLineEnd[0], collideLineStart[1], collideLineEnd[1])

            def getOffset(grad, point):
                x = point[0] * grad
                return point[1] - x

            def isLineVertical(grad):
                return grad == None
            
            def areLinesParallel(grad1, grad2):
                return grad1 == grad2
            
            # Lines have same gradient so cannot have intersected
            if areLinesParallel(checkLineGradient, collideLineGradient):
                return None

            if (isLineVertical(checkLineGradient) or isLineVertical(collideLineGradient)):
                # Case: One line is vertical
                if isLineVertical(checkLineGradient):
                    c = getOffset(collideLineGradient, collideLineStart)
                    grad = collideLineGradient
                    x = checkLineEnd[0]
                else:
                    c = getOffset(checkLineGradient, checkLineStart)
                    grad = checkLineGradient
                    x = collideLineEnd[0]

                y = (x * grad) + c
                return (x,y)
            
            else:
                # Both diagonal
                # napkin math, don't judge

                c = getOffset(checkLineGradient, checkLineStart)
                d = getOffset(collideLineGradient, collideLineStart)

                x = (d - c) / (checkLineGradient - collideLineGradient)
                y = (x * checkLineGradient) + c
                return (x,y)

        def wasIntersectionOnLine(checkLineStart, checkLineEnd, collideLineStart, collideLineEnd):

            def isInBounds(pos, xStart, xEnd, yStart, yEnd):
                startX = min(xStart, xEnd)
                startY = min(yStart, yEnd)
                endX = max(xStart, xEnd)
                endY = max(yStart, yEnd)
                x = pos[0]
                y = pos[1]
                if startX <= x <= endX:
                    return startY <= y <= endY
                return False

            intersection = getIntersectionPoint(checkLineStart, checkLineEnd, collideLineStart, collideLineEnd)
            if intersection == None:
                return False
            return (isInBounds(intersection, checkLineStart[0], checkLineEnd[0], checkLineStart[1], checkLineEnd[1]) and 
                    isInBounds(intersection, collideLineStart[0], collideLineEnd[0], collideLineStart[1], collideLineEnd[1]))
        
        linesToConnect = []
        for indexLine in range(len(self._pointsIn)):
            linesToConnect.append((self._pointsIn[indexLine], self._pointsOut[indexLine])) 

        for indexPoint, point in enumerate(self._pointsLine):
            if len(linesToConnect) > 0:
                pointStart = point
                if indexPoint + 1 < len(self._pointsLine):
                    pointEnd = self._pointsLine[indexPoint + 1]
                else:
                    pointEnd = self._pointsLine[0]
                
                for indexLine, line in enumerate(reversed(linesToConnect)):
                    indexLine = len(linesToConnect) - indexLine - 1
                    collidePointStart, collidePointEnd = line
                    collidePointStart = (collidePointStart[0], collidePointStart[1] + RESOLUTION_NINTENDO_DS[1])
                    collidePointEnd = (collidePointEnd[0], collidePointEnd[1] + RESOLUTION_NINTENDO_DS[1])
                    if wasIntersectionOnLine(pointStart, pointEnd, collidePointStart, collidePointEnd):
                        linesToConnect.pop(indexLine)
            else:
                break
        
        return len(linesToConnect) == 0

    def doOnComplete(self):
        # TODO - Do the lengths of points in and out need to be the same? Solution algorithm
        polygon(self._surfaceSolution, (255,255,255), self._pointsOut)
        polygon(self._surfaceSolution, (0,0,0), self._pointsIn)
        if self._surfaceSolution.get_at(self._posFill) != (0,0,0):
            # Have to swap answer regions
            # TODO - Would involve inverting this surface or NOT the check (which is only used for points) and adjusting bounds check for line
            logSevere("Inversion not supported!", name="NazoTrceOnly")

        self._penSurface = Surface(RESOLUTION_NINTENDO_DS)
        while self._colourLine == self._colourKey:
            self._colourKey = (randint(0,255), 0, 0)
        self._penSurface.set_colorkey(self._colourKey)
        self._clearSurface()
        return super().doOnComplete()

    def _clearSurface(self):
        self._penSurface.fill(self._colourKey)

    def _doReset(self):
        self._pointsLine = []
        self._clearSurface()
    
    def _addLastPoint(self):
        self._pointsLine.append(self._penLastPoint)
    
    def _drawLineToCurrentPoint(self, pos):
        offsetLastPoint = (self._penLastPoint[0], self._penLastPoint[1] - RESOLUTION_NINTENDO_DS[1])
        offsetPos = (pos[0], pos[1] - RESOLUTION_NINTENDO_DS[1])
        line(self._penSurface, self._colourLine, offsetLastPoint, offsetPos, width=WIDTH_PEN)

    def drawPuzzleElements(self, gameDisplay):
        gameDisplay.blit(self._penSurface, (0, RESOLUTION_NINTENDO_DS[1]))
        return super().drawPuzzleElements(gameDisplay)
    
    def handleTouchEventPuzzleElements(self, event):
        if event.type == MOUSEBUTTONDOWN:
            self._isPenDrawing = True
            self._clearSurface()
            self._penLastPoint = event.pos

        elif self._isPenDrawing:
            if event.type == MOUSEMOTION:
                self._drawLineToCurrentPoint(event.pos)
                self._addLastPoint()
                self._penLastPoint = event.pos

            elif event.type == MOUSEBUTTONUP:
                self._isPenDrawing = False
                if self._penLastPoint != None:
                    self._drawLineToCurrentPoint(event.pos)
                    self._addLastPoint()
                    self._penLastPoint = None
        return True