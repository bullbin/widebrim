from widebrim.engine_ext.utils import getBottomScreenAnimFromPath
from widebrim.engine.anim.fader import Fader
from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.madhatter.typewriter.strings_lt2 import OPCODES_LT2

from .base import BaseQuestionObject
from .const import PATH_ANI_KNIGHT

from pygame import Surface, MOUSEBUTTONDOWN
from math import sqrt

# Ported from shortbrim
# TODO - Rewrite with better code style

class HandlerShortbrimKnight(BaseQuestionObject):

    TIME_PER_SQUARE = 100
    COLOR_ALPHA = (240,0,0)

    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)

        self.__bankImages = getBottomScreenAnimFromPath(laytonState, PATH_ANI_KNIGHT)

        def setAnimationFromNameAndReturnInitialFrame(name):
            if self.__bankImages.setAnimationFromName(name):
                return self.__bankImages.getActiveFrame()
            return None

        self.tileBoardDimensions = (0,0)
        self.posCorner = (0,0)
        self.tileDimensions = (24,24)
        self.overlaySurface = Surface(RESOLUTION_NINTENDO_DS)
        self.overlaySurface.set_colorkey(HandlerShortbrimKnight.COLOR_ALPHA)
        self.overlaySurface.fill(HandlerShortbrimKnight.COLOR_ALPHA)

        self.imageKnight        = setAnimationFromNameAndReturnInitialFrame("o")
        self.imageKnightVisited = setAnimationFromNameAndReturnInitialFrame("red")
        self.imageTileAvailable = setAnimationFromNameAndReturnInitialFrame("ki")
        if self.imageKnight == None or self.imageKnightVisited == None or self.imageTileAvailable == None:
            self.imageKnight        = Surface((22,22))
            self.imageKnightVisited = Surface((22,22))
            self.imageTileAvailable = Surface((22,22))

        self.tilesAvailable = []
        self.tilesVisited   = []
        self.posKnight      = (0,0)
        self.initialPosKnight = (0,0)

        self.movementFader = Fader(HandlerShortbrimKnight.TIME_PER_SQUARE, initialActiveState=False)
        self.movementFaderDuration = 1
        self.movementDelta = (0,0)
        self.movementFaderElapsed = 0

    def _generateOverlaySurface(self):

        def tileToScreenPos(tilePos):
            return (self.posCorner[0] + tilePos[0] * self.tileDimensions[0],
                    self.posCorner[1] + tilePos[1] * self.tileDimensions[1])
            
        self.overlaySurface.fill(self.overlaySurface.get_colorkey())

        for pos in self.tilesAvailable:
            self.overlaySurface.blit(self.imageTileAvailable, tileToScreenPos(pos))
        for pos in self.tilesVisited:
            self.overlaySurface.blit(self.imageKnightVisited, tileToScreenPos(pos))

    def _behaviourWhenSpacePressed(self, pos):
        if pos not in self.tilesVisited:
            self._addElement(pos)
        self._generateOverlaySurface()

    def drawPuzzleElements(self, gameDisplay):

        def tileToScreenPos(tilePos):
            return (self.posCorner[0] + tilePos[0] * self.tileDimensions[0],
                    self.posCorner[1] + RESOLUTION_NINTENDO_DS[1] + tilePos[1] * self.tileDimensions[1])

        gameDisplay.blit(self.overlaySurface, (0, RESOLUTION_NINTENDO_DS[1]))
        if self.movementFader.getActiveState():
            xFactor = self.movementFaderElapsed / self.movementFaderDuration / 2
            yFactor = self.movementFader.getStrength()
            tempPlace = (self.tilesVisited[-1][0] + self.movementDelta[0] * xFactor,
                         self.tilesVisited[-1][1] + self.movementDelta[1] * xFactor - yFactor)
            tempScreenPos = tileToScreenPos(tempPlace)
            if tempScreenPos[1] < RESOLUTION_NINTENDO_DS[1]:    # Moving onto top screen
                if tempScreenPos[1] + self.imageKnight.get_height() >= RESOLUTION_NINTENDO_DS[1]:
                    tempImageLength = self.imageKnight.get_height() - (RESOLUTION_NINTENDO_DS[1] - tempScreenPos[1])
                    cutoff = (0, self.imageKnight.get_height() - tempImageLength, self.imageKnight.get_width(), tempImageLength)
                    gameDisplay.blit(self.imageKnight, (tempScreenPos[0], RESOLUTION_NINTENDO_DS[1]), cutoff)
            else:
                gameDisplay.blit(self.imageKnight, tempScreenPos)

        else:
            gameDisplay.blit(self.imageKnightVisited, tileToScreenPos(self.posKnight))
            gameDisplay.blit(self.imageKnight, tileToScreenPos(self.posKnight))

    def doOnComplete(self):
        self._getAvailableSpaces()
        return super().doOnComplete()
    
    def _doReset(self):
        self.movementFader.setActiveState(False)
        self.posKnight = self.initialPosKnight
        self.tilesVisited = []
        self._getAvailableSpaces()
        return super()._doReset()

    def _movementFaderInvert(self):
        self.movementFader.setInvertedState(True)
        self.movementFader.reset()

    def _addElement(self, pos):
        self.movementDelta = (pos[0] - self.posKnight[0], pos[1] - self.posKnight[1])
        tempTileDelta = sqrt(self.movementDelta[0] ** 2 + self.movementDelta[1] ** 2)

        self.movementFaderDuration = tempTileDelta * HandlerShortbrimKnight.TIME_PER_SQUARE // 2
        self.movementFader.setDuration(self.movementFaderDuration)
        self.movementFader.setInvertedState(False)
        self.movementFader.setCallback(self._movementFaderInvert)

        self.movementFaderElapsed = 0
        self.tilesVisited.append(self.posKnight)
        self.posKnight = pos
        self._getAvailableSpaces()

    def hasSubmitButton(self):
        return False

    def _wasAnswerSolution(self):
        return True

    def updatePuzzleElements(self, gameClockDelta):
        if self.movementFader.getActiveState():
            self.movementFader.update(gameClockDelta)
            self.movementFaderElapsed += gameClockDelta
        
        elif len(self.tilesVisited) + 1 == self.tileBoardDimensions[0] * self.tileBoardDimensions[1]:
            self._startJudgement()

    def _getAvailableSpaces(self):
        self.tilesAvailable = []
        if self.tileBoardDimensions == (0,0):
            self._startJudgement()
        else:
            deltaPos = [(2, 1), (1, -2), (-2, -1), (-1, 2),
                        (2,-1), (-1,-2), (-2,  1), (1, 2)]
            for pos in deltaPos:
                tempPosKnight = (self.posKnight[0] + pos[0],
                                self.posKnight[1] + pos[1])
                if ((tempPosKnight[0] >= 0 and tempPosKnight[1] >= 0) and
                    (tempPosKnight[0] < self.tileBoardDimensions[0] and tempPosKnight[1] < self.tileBoardDimensions[1])):
                    self.tilesAvailable.append(tempPosKnight)
            self._generateOverlaySurface()

    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.SetKnightInfo.value:
            self.posCorner = (operands[0].value, operands[1].value)
            self.tileDimensions = (operands[2].value, operands[2].value)
            self.tileBoardDimensions = (operands[3].value, operands[4].value)
            self.posKnight = (operands[5].value, operands[6].value)
            self.initialPosKnight = self.posKnight
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True
    
    def handleTouchEventPuzzleElements(self, event):
        if not(self.movementFader.getActiveState()):
            if event.type == MOUSEBUTTONDOWN:
                if event.pos[0] >= self.posCorner[0] and event.pos[1] >= self.posCorner[1] + RESOLUTION_NINTENDO_DS[1]:
                    if (event.pos[0] < self.posCorner[0] + self.tileDimensions[0] * self.tileBoardDimensions[0] and
                        event.pos[1] < self.posCorner[1] + RESOLUTION_NINTENDO_DS[1] + self.tileDimensions[1] * self.tileBoardDimensions[1]):   # Clicked on grid
                        deltaTilesX = (event.pos[0] - self.posCorner[0]) // self.tileDimensions[0]
                        deltaTilesY = (event.pos[1] - RESOLUTION_NINTENDO_DS[1] - self.posCorner[1]) // self.tileDimensions[1]
                        tempPos = (deltaTilesX, deltaTilesY)
                        if tempPos in self.tilesAvailable:
                            self._behaviourWhenSpacePressed(tempPos)
                            return True
        return False