from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from .base import BaseQuestionObject
from ....madhatter.typewriter.strings_lt2 import OPCODES_LT2

from math import sqrt, atan2, degrees
from pygame import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, Rect
from pygame.draw import line

# When drawing lines, this is the behaviour
# - Point is lit up green
# - Line snaps to closest cardinal direction
# - Going over the same line inverts it (disables)

# TODO - Find image of circle around point
# TODO - Limit the moves
# TODO - Look into lengths of allowed items - eg region count, line count...

class HandlerDivide(BaseQuestionObject):

    DISTANCE_MIN_GRAB = 10

    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)

        self._sizeBlock = 2
        self._colourLine = (0,0,0)
        self._colourPen = (0,0,0)
        
        if laytonState.getNazoData().idHandler == 15:
            self._isMovesLimited = True
        else:
            self._isMovesLimited = False

        self._limitMoves = 0
        self._countMoves = 0

        self._allowDiagonalMoves = False

        self._posGridCorner = (0,RESOLUTION_NINTENDO_DS[1])
        self._sizeGrid = (0,0)
        self._posTouchPoints = []

        self._lines = []
        self._solutionLines = []
        self._forbiddenLines = []
        self._gridAllowedRegion = []

        self._mouseLineEnd = (0,0)

        self._pointStart = None

    def _doReset(self):
        self._lines = []
        return super()._doReset()
    
    def _wasAnswerSolution(self):
        if len(self._lines) != len(self._solutionLines):
            return False

        for solution in self._solutionLines:
            indexStart, indexStop = solution
            if not((indexStart, indexStop) in self._lines or (indexStop, indexStart) in self._lines):
                return False
        return True

    def _getClosestTouchPoint(self, pos):

        def calculateDistance(x0, x1, y0, y1):
            return sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)

        minDistance = RESOLUTION_NINTENDO_DS[0]
        minPointIndex = None
        for indexPoint, point in enumerate(self._posTouchPoints):
            # TODO - Reduce complexity by using grid scale
            x, y = point
            x += self._posGridCorner[0]
            y += self._posGridCorner[1]

            distance = calculateDistance(x, pos[0], y, pos[1])
            if distance <= minDistance:
                minPointIndex = indexPoint
                minDistance = distance
        
        return (minPointIndex, minDistance)

    def _isNextMoveOnXAxis(self, deltaPos):
        direction = degrees(atan2(deltaPos[1], deltaPos[0]))
        return -45 <= direction < 45 or (135 <= direction < 180 or -180 > direction >= -135)

    def _doesLineExist(self, pointFrom, pointTo):
        indexLine = None
        try:
            indexLine = self._lines.index((pointFrom, pointTo))
        except ValueError:
            try:
                indexLine = self._lines.index((pointTo, pointFrom))
            except ValueError:
                pass
        return indexLine

    def _getPointsOnGridBetweenPoints(self, point0, point1):

        x0, y0 = point0
        x1, y1 = point1
        diffY = y1 - y0

        if diffY != 0:
            gradient = (x1 - x0) / diffY
        else:
            gradient = None

        def isPointOnLine(point):
            x,y = point
            if gradient == None:
                # No change in Y, just needs to have Y equal to point
                return y == y0
            else:
                deltaX = x - x0
                deltaY = y - y0
                if deltaY != 0:
                    return (deltaX / deltaY) == gradient
                return False
        
        # TODO - Maybe separate to some other library
        def calculateDistance(xStart, xEnd, yStart, yEnd):
            return sqrt((xEnd - xStart) ** 2 + (yEnd - yStart) ** 2)

        distance = []
        distanceToPoint = {}

        for x in range(min(x0, x1), max(x0,x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                if (x,y) in self._posTouchPoints:
                    if isPointOnLine((x,y)):
                        tempDistance = calculateDistance(x0, x, y0, y)
                        distance.append(tempDistance)

                        # TODO - Assumes point already isn't in dictionary
                        distanceToPoint[tempDistance] = self._posTouchPoints.index((x,y))

        distance.sort()
        output = []
        for distanceKey in distance:
            output.append(distanceToPoint[distanceKey])

        if len(output) > 0:
            if output[0] != self._posTouchPoints.index(point0):
                output.insert(0, self._posTouchPoints.index(point0))
        else:
            output.append(self._posTouchPoints.index(point0))
        return output

    def drawPuzzleElements(self, gameDisplay):
        # TODO - Draw green point at start point
        # Render lines...

        lineWidth = 3
        super().drawPuzzleElements(gameDisplay)

        for linePair in self._lines:
            startLine, stopLine = linePair
            xStart, yStart = self._posTouchPoints[startLine]
            xStop, yStop = self._posTouchPoints[stopLine]
            line(gameDisplay, self._colourLine, (xStart + self._posGridCorner[0], yStart + self._posGridCorner[1]),
                                       (xStop + self._posGridCorner[0], yStop + self._posGridCorner[1]), lineWidth)

        if self._pointStart != None:
            xStart, yStart = self._posTouchPoints[self._pointStart]
            line(gameDisplay, self._colourPen, (xStart + self._posGridCorner[0], yStart + self._posGridCorner[1]),
                                       self._mouseLineEnd, lineWidth)

        return super().drawPuzzleElements(gameDisplay)

    def _doAddRemoveLineAndReturnNextPoint(self, pointStart, pointEnd):
        pointsFromLine = self._getPointsOnGridBetweenPoints(pointStart, pointEnd)
        for indexPoint in range(len(pointsFromLine) - 1):
            startIndex = pointsFromLine[indexPoint]
            endIndex = pointsFromLine[indexPoint + 1]
            if startIndex != endIndex:
                indexLine = self._doesLineExist(startIndex, endIndex)
                if indexLine == None:
                    self._lines.append((startIndex, endIndex))
                else:
                    self._lines.pop(indexLine)
        return pointsFromLine[-1]

    def handleTouchEventNonDiagonal(self, event):

        def doGrabDestinationBehaviour(event):
            pointX, pointY = self._posTouchPoints[self._pointStart]

            deltaX = event.pos[0]
            deltaX -= (pointX + self._posGridCorner[0])
            deltaY = event.pos[1]
            deltaY -= (pointY + self._posGridCorner[1])

            if self._isNextMoveOnXAxis((deltaX, deltaY)):
                targetPointPos = (event.pos[0], pointY + self._posGridCorner[1])
            else:
                targetPointPos = (pointX + self._posGridCorner[0], event.pos[1])
            self._mouseLineEnd = targetPointPos
            
            # Remap to point space
            targetPointPos = (targetPointPos[0] - self._posGridCorner[0], targetPointPos[1] - self._posGridCorner[1])
            self._pointStart = self._doAddRemoveLineAndReturnNextPoint(self._posTouchPoints[self._pointStart], targetPointPos)

        if event.type == MOUSEBUTTONDOWN:
            indexPoint, distance = self._getClosestTouchPoint(event.pos)
            if indexPoint != None and distance < HandlerDivide.DISTANCE_MIN_GRAB:
                # Point was grabbed
                self._pointStart = indexPoint
                self._mouseLineEnd = (self._posTouchPoints[indexPoint][0] + self._posGridCorner[0],
                                      self._posTouchPoints[indexPoint][1] + self._posGridCorner[1])
                return True
        
        if self._pointStart != None:
            eventPos = event.pos
            if event.type == MOUSEBUTTONUP:
                # On event up, attempt to snap to closest point first
                indexPoint, distance = self._getClosestTouchPoint(event.pos)
                if indexPoint != None and distance < HandlerDivide.DISTANCE_MIN_GRAB:
                    eventPos = (self._posTouchPoints[indexPoint][0] + self._posGridCorner[0],
                                self._posTouchPoints[indexPoint][1] + self._posGridCorner[1])
            
            doGrabDestinationBehaviour(event)
            if event.type == MOUSEBUTTONUP:
                self._pointStart = None
            return True
        return False

    def handleTouchEventDiagonal(self, event):
        if event.type == MOUSEBUTTONDOWN or event.type == MOUSEBUTTONUP:
            self._mouseLineEnd = event.pos
            indexPoint, distance = self._getClosestTouchPoint(event.pos)
            if indexPoint != None and distance < HandlerDivide.DISTANCE_MIN_GRAB:
                
                if event.type == MOUSEBUTTONDOWN:
                    self._pointStart = indexPoint
                elif self._pointStart != None:
                    self._doAddRemoveLineAndReturnNextPoint(self._posTouchPoints[self._pointStart], self._posTouchPoints[indexPoint])
            
            if event.type == MOUSEBUTTONUP:
                self._pointStart = None

            # TODO - Return False if mouse button clicked outside of grid
        
        elif event.type == MOUSEMOTION:
            # TODO - Restrict to grid
            self._mouseLineEnd = event.pos
        else:
            return False
        return True

    def handleTouchEventPuzzleElements(self, event):
        eventValid = event.type == MOUSEBUTTONUP or event.type == MOUSEMOTION
        if not(eventValid) and event.type == MOUSEBUTTONDOWN:
            for region in self._gridAllowedRegion:
                region : Rect
                if region.collidepoint(event.pos):
                    eventValid = True
                    break
            if not(eventValid):
                indexPoint, distance = self._getClosestTouchPoint(event.pos)
                if distance < HandlerDivide.DISTANCE_MIN_GRAB:
                    eventValid = True

        if eventValid:
            if self._allowDiagonalMoves:
                if self.handleTouchEventDiagonal(event):
                    return True
            elif self.handleTouchEventNonDiagonal(event):
                return True
        return super().handleTouchEventPuzzleElements(event)

    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.SetNumTouch.value and len(operands) == 1:
            self._limitMoves = operands[0].value
        elif opcode == OPCODES_LT2.SetGridPosition.value and len(operands) == 2:
            self._posGridCorner = (operands[0].value, operands[1].value + RESOLUTION_NINTENDO_DS[1])
        elif opcode == OPCODES_LT2.SetGridSize.value and len(operands) == 2:
            self._sizeGrid = (operands[0].value, operands[1].value)
        elif opcode == OPCODES_LT2.SetBlockSize.value and len(operands) == 1:
            self._sizeBlock = operands[0].value

        # TODO - Colour incorrect!
        elif opcode == OPCODES_LT2.SetLineColor.value and len(operands) == 3:
            self._colourLine = (operands[0].value, operands[1].value, operands[2].value)
        elif opcode == OPCODES_LT2.SetPenColor.value and len(operands) == 3:
            self._colourPen = (operands[0].value, operands[1].value, operands[2].value)
        elif opcode == OPCODES_LT2.SetGridTypeRange.value and len(operands) == 5:
            if operands[4].value == 1:
                minX = min(operands[0].value, operands[2].value)
                minY = min(operands[1].value, operands[3].value)
                maxX = max(operands[0].value, operands[2].value)
                maxY = max(operands[1].value, operands[3].value)
                # TODO - Sanitisation check
                self._gridAllowedRegion.append((minX, minY, maxX, maxY))
            elif operands[4].value == 2:
                self._forbiddenLines.append(((operands[0].value, operands[1].value), (operands[2].value, operands[3].value)))
            else:
                return False
            return False
        elif opcode == OPCODES_LT2.EnableNaname.value and len(operands) == 0:
            self._allowDiagonalMoves = True
        elif opcode == OPCODES_LT2.AddTouchPoint.value and len(operands) == 2:
            self._posTouchPoints.append((operands[0].value, operands[1].value))
        elif opcode == OPCODES_LT2.AddCheckLine.value and len(operands) == 4:
            self._solutionLines.append(((operands[0].value, operands[1].value),
                                        (operands[2].value, operands[3].value)))
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True
    
    def doOnComplete(self):
        self._sizeGrid = (self._sizeGrid[0] * self._sizeBlock, self._sizeGrid[0] * self._sizeBlock)
        for indexTouchPoint, touchPoint in enumerate(self._posTouchPoints):
            touchPointX, touchPointY = touchPoint
            self._posTouchPoints[indexTouchPoint] = (touchPointX * self._sizeBlock, touchPointY * self._sizeBlock)
        
        simplifiedSolutionLines = []
        for indexLine, line in enumerate(self._solutionLines):
            point0, point1 = line
            point0 = (point0[0] * self._sizeBlock, point0[1] * self._sizeBlock)
            point1 = (point1[0] * self._sizeBlock, point1[1] * self._sizeBlock)

            # TODO - Crash if points given not already in grid
            subdividedLines = self._getPointsOnGridBetweenPoints(point0, point1)
            for indexLine in range(len(subdividedLines) - 1):
                simplifiedSolutionLines.append((subdividedLines[indexLine], subdividedLines[indexLine + 1]))

        simplifiedForbiddenLines = []
        for indexLine, line in enumerate(self._forbiddenLines):
            point0, point1 = line
            point0 = (point0[0] * self._sizeBlock, point0[1] * self._sizeBlock)
            point1 = (point1[0] * self._sizeBlock, point1[1] * self._sizeBlock)

            # TODO - Crash if points given not already in grid
            # TODO - Crash on The Ant's Journey
            subdividedLines = self._getPointsOnGridBetweenPoints(point0, point1)
            for indexLine in range(len(subdividedLines) - 1):
                simplifiedForbiddenLines.append((subdividedLines[indexLine], subdividedLines[indexLine + 1]))

        self._solutionLines = simplifiedSolutionLines
        self._forbiddenLines = simplifiedForbiddenLines

        def transformPoint(inPoint):
            inPoint = (inPoint[0] * self._sizeBlock, inPoint[1] * self._sizeBlock)
            inPoint = (inPoint[0] + self._posGridCorner[0], inPoint[1] + self._posGridCorner[1])
            return inPoint

        for indexRect, dimensions in enumerate(self._gridAllowedRegion):
            minX, minY, maxX, maxY = dimensions
            topLeft = transformPoint((minX, minY))
            bottomRight = transformPoint((maxX, maxY))
            self._gridAllowedRegion[indexRect] = Rect(topLeft[0], topLeft[1], bottomRight[0] - topLeft[0], bottomRight[1] - topLeft[1])

        return super().doOnComplete()