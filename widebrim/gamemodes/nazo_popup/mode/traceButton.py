from widebrim.engine.string.cmp import strCmp
from .base import BaseQuestionObject
from ....engine.const import RESOLUTION_NINTENDO_DS
from ....engine_ext.utils import getBottomScreenAnimFromPath, getButtonFromPath
from ....madhatter.typewriter.strings_lt2 import OPCODES_LT2
from pygame import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, draw, Surface
from random import randint
from math import sqrt

# TODO - Touch message prevents the arrow buttons from displaying. Oversight? Limitation? Not drawn during touch? Idk
# TODO - Game has better code for detecting circles. Not fooled by scribbles, for example
# TODO - Puzzle specific behaviour - a bunch of unimplemented animation names?
# TODO - Game has unused behaviour for internal ID 10, which was used for a divide puzzle instead
# TODO - Maybe cache background
# TODO - Improve trace behaviour - don't average points, as going slower in one area skews the average

# TODO - Put these constants somewhere
PATH_ANI_RETRY      = "nazo/tracebutton/%s/retry_trace.spr"
PATH_ANI_POINT      = "nazo/tracebutton/point_trace.spr"
PATH_ANI_BTN_LEFT   = "nazo/tracebutton/arrow_left.spr"
PATH_ANI_BTN_RIGHT  = "nazo/tracebutton/arrow_right.spr"

POS_BTN_LEFT        = (   2,0)
POS_BTN_RIGHT       = (0x9e,0)

PATH_BG_TRACE       = "nazo/q%i.bgx"
PATH_BG_TRACE_ALT   = "nazo/q%i_%i.bgx"

WIDTH_PEN = 3

class TraceZone():
    def __init__(self, x, y, diameter, isSolution):
        self.x = x
        self.y = y + RESOLUTION_NINTENDO_DS[1]
        self.radius = diameter / 2
        self.isSolution = isSolution
    
    def wasPressed(self, pos):
        distance = sqrt((pos[0] - self.x) ** 2 + (pos[1] - self.y) ** 2)
        return distance <= self.radius

class HandlerTraceButton(BaseQuestionObject):
    def __init__(self, laytonState, screenController, callbackOnTerminate):

        self._indexSolution = 0
        self._maxIndexSolution = 0

        super().__init__(laytonState, screenController, callbackOnTerminate)

        self.__buttons = []
        
        def addIfNotNone(button):
            if button != None:
                self.__buttons.append(button)

        addIfNotNone(getButtonFromPath(laytonState, PATH_ANI_BTN_LEFT, pos=POS_BTN_LEFT, callback=self._callbackOnLeft))
        addIfNotNone(getButtonFromPath(laytonState, PATH_ANI_BTN_RIGHT, pos=POS_BTN_RIGHT, callback=self._callbackOnRight))

        self._traceZones = [[],[],[],[]]
        self._colourLine = (0,0,0)
        self._colourKey = (0,0,0)

        self._animNoTargetFound = getBottomScreenAnimFromPath(laytonState, PATH_ANI_RETRY)
        self._animPoint         = getBottomScreenAnimFromPath(laytonState, PATH_ANI_POINT)

        self._penLastPoint = None
        self._penSurface = None

        self._hasPenDrawn = False
        self._isPenDrawing = False

        # TODO - Maybe do rolling average to prevent this from being able to get stupidly big
        self._tracePointsTotal = (0,0)
        self._tracePointsCount = 0
        self._tracePointTargetted = None

        self._setPuzzleTouchBounds(RESOLUTION_NINTENDO_DS[1])
    
    def _loadPuzzleBg(self):
        nazoData = self.laytonState.getNazoData()
        if nazoData != None:
            if self._indexSolution == 0:
                self.screenController.setBgMain(PATH_BG_TRACE % nazoData.bgMainId)
            else:
                self.screenController.setBgMain(PATH_BG_TRACE_ALT % (nazoData.bgMainId, self._indexSolution))

    def _callbackOnLeft(self):
        self._indexSolution -= 1
        if self._indexSolution < 0:
            self._indexSolution = self._maxIndexSolution
        self._loadPuzzleBg()
        self._doReset()

    def _callbackOnRight(self):
        self._indexSolution += 1
        if self._indexSolution > self._maxIndexSolution:
            self._indexSolution = 0
        self._loadPuzzleBg()
        self._doReset()
    
    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.SetFontUserColor.value and len(operands) == 3:
            self._colourLine = (operands[0].value, operands[1].value, operands[2].value)
                
        elif opcode == OPCODES_LT2.AddTracePoint.value and len(operands) == 4:
            if self._indexSolution < 4 and len(self._traceZones[self._indexSolution]) < 24:
                wasTrue = strCmp("true", operands[3].value)
                self._traceZones[self._indexSolution].append(TraceZone(operands[0].value, operands[1].value,
                                                                       operands[2].value, wasTrue))
        elif opcode == OPCODES_LT2.AddSolution.value and len(operands) == 0:
            if self._maxIndexSolution < 4:
                self._indexSolution += 1
                self._maxIndexSolution += 1
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True
    
    def doOnComplete(self):
        self._indexSolution = 0
        self._penSurface = Surface(RESOLUTION_NINTENDO_DS)
        while self._colourLine == self._colourKey:
            self._colourKey = (randint(0,255), 0, 0)
        self._penSurface.set_colorkey(self._colourKey)
        self._clearSurface()
        return super().doOnComplete()

    def _clearSurface(self):
        # TODO - Disable pointing overlay, clear targetted point
        self._tracePointsTotal = (0,0)
        self._tracePointsCount = 0
        self._penSurface.fill(self._colourKey)
    
    def _wasAnswerSolution(self):
        return self._tracePointTargetted != None and self._tracePointTargetted.isSolution

    def _doReset(self):
        self._hasPenDrawn = False
        self._tracePointTargetted = None
        self._clearSurface()
    
    def _addLastPoint(self):
        self._tracePointsCount += 1
        self._tracePointsTotal = (self._tracePointsTotal[0] + self._penLastPoint[0], self._tracePointsTotal[1] + self._penLastPoint[1])
    
    def _drawLineToCurrentPoint(self, pos):
        offsetLastPoint = (self._penLastPoint[0], self._penLastPoint[1] - RESOLUTION_NINTENDO_DS[1])
        offsetPos = (pos[0], pos[1] - RESOLUTION_NINTENDO_DS[1])
        draw.line(self._penSurface, self._colourLine, offsetLastPoint, offsetPos, width=WIDTH_PEN)
    
    def updatePuzzleElements(self, gameClockDelta):
        for button in self.__buttons:
            button.update(gameClockDelta)
        return super().updatePuzzleElements(gameClockDelta)

    def _updatePenTarget(self):

        def setPointPositionFromTarget(target):
            if self._animPoint != None and self._animPoint.getActiveFrame() != None:
                y = target.y - (self._animPoint.getActiveFrame().get_height())
                self._animPoint.setPos((target.x,y))

        self._tracePointTargetted = None
        if self._tracePointsCount > 0:
            targetPos = (round(self._tracePointsTotal[0] / self._tracePointsCount), round(self._tracePointsTotal[1] / self._tracePointsCount))
            for target in self._traceZones[self._indexSolution]:
                if target.wasPressed(targetPos):
                    self._tracePointTargetted = target
                    setPointPositionFromTarget(target)
                    break

    def drawPuzzleElements(self, gameDisplay):
        gameDisplay.blit(self._penSurface, (0, RESOLUTION_NINTENDO_DS[1]))
        # TODO - Implement top screen/bottom screen for clipping purposes

        if self._maxIndexSolution > 0:
            for button in self.__buttons:
                button.draw(gameDisplay)

        if self._tracePointTargetted != None:
            # Draw arrow
            if self._animPoint != None:
                self._animPoint.draw(gameDisplay)
        elif self._hasPenDrawn and not(self._isPenDrawing):
            # Draw retry trace screen
            if self._animNoTargetFound != None:
                self._animNoTargetFound.draw(gameDisplay)

        return super().drawPuzzleElements(gameDisplay)

    def handleTouchEventPuzzleElements(self, event):
        if self._maxIndexSolution > 0:
            for button in self.__buttons:
                if button.handleTouchEvent(event):
                    return True

        if event.type == MOUSEBUTTONDOWN:
            self._hasPenDrawn = True
            self._isPenDrawing = True
            self._tracePointTargetted = None
            self._clearSurface()
            self._penLastPoint = event.pos

        elif self._hasPenDrawn and self._isPenDrawing:
            if event.type == MOUSEMOTION:
                self._drawLineToCurrentPoint(event.pos)
                self._addLastPoint()
                self._penLastPoint = event.pos

            elif event.type == MOUSEBUTTONUP:
                self._isPenDrawing = False
                if self._penLastPoint != None:
                    self._drawLineToCurrentPoint(event.pos)
                    self._addLastPoint()
                    self._updatePenTarget()
                    self._penLastPoint = None
        return True