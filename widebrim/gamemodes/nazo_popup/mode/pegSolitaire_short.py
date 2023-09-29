from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath
from widebrim.madhatter.typewriter.strings_lt2 import OPCODES_LT2
from .base import BaseQuestionObject
from .const import PATH_ANI_PEGSOLITAIRE
from pygame import MOUSEBUTTONUP, MOUSEBUTTONDOWN, MOUSEMOTION, Surface

# Ported from shortbrim
# TODO - Rewrite with better code style

class HandlerShortbrimPegSolitaire(BaseQuestionObject):

    # TODO - (old) Pull out class to support these types of puzzles which are like TapToAnswer but fixed on grid
    BALL_X_LIMIT = 187

    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)

        self.__bankImages = getBottomScreenAnimFromPath(laytonState, PATH_ANI_PEGSOLITAIRE)

        self.tileBoardDimensions = (7, 7)
        self.posCorner = (12, 12)
        self.tileDimensions = (24,24)
        self.tilesPopulated = []
        self.tilesInitial = []

        def setAnimationFromNameAndReturnInitialFrame(name):
            if self.__bankImages.setAnimationFromName(name):
                return self.__bankImages.getActiveFrame()
            return None

        self.imageBall = setAnimationFromNameAndReturnInitialFrame("ball")
        if self.imageBall == None:
            self.imageBall = Surface(self.tileDimensions)

        self.activeTile = None
        self.activeTilePos = (0,0)
        self.activeTileMouseOffset = (0,0)

    def hasSubmitButton(self):
        return False

    def updatePuzzleElements(self, gameClockDelta):
        if len(self.tilesPopulated) < 2:
            self._startJudgement()

    def drawPuzzleElements(self, gameDisplay):

        def tileToScreenPos(tilePos):
            return (self.posCorner[0] + tilePos[0] * self.tileDimensions[0],
                    self.posCorner[1] + tilePos[1] * self.tileDimensions[1] + RESOLUTION_NINTENDO_DS[1])

        for tileIndex, tilePos in enumerate(self.tilesPopulated):
            if tileIndex != self.activeTile:
                gameDisplay.blit(self.imageBall, tileToScreenPos(tilePos))
        if self.activeTile != None:
            gameDisplay.blit(self.imageBall, self.activeTilePos)

    def isSpaceAvailable(self, pos):
        if pos[0] < 2 and pos[1] < 2:
            return False
        if pos[0] > 4 and pos[1] < 2:
            return False
        if pos[0] < 2 and pos[1] > 4:
            return False
        if pos[0] > 4 and pos[1] > 4:
            return False
        if pos[0] < 0 or pos[0] >= self.tileBoardDimensions[0] or pos[1] < 0 or pos[1] >= self.tileBoardDimensions[1]:
            return False
        return True

    def isSpacePopulated(self, pos):
        if pos in self.tilesPopulated:
            return True
        return False

    def _wasAnswerSolution(self):
        return True

    def _doReset(self):
        self.tilesPopulated = list(self.tilesInitial)
        return super()._doReset()

    def doOnComplete(self):
        self.tilesInitial = list(self.tilesPopulated)
        return super().doOnComplete()

    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.PegSol_AddObject.value and len(operands) == 5:
            for x in range(operands[2].value):
                for y in range(operands[3].value):
                    tempPos = (operands[0].value + x, operands[1].value + y)
                    if operands[4].value == 0:    # Remove
                        if tempPos in self.tilesPopulated:
                            del self.tilesPopulated[self.tilesPopulated.index(tempPos)]
                    else:                           # Add
                        if not(self.isSpacePopulated(tempPos)) and self.isSpaceAvailable(tempPos):
                            self.tilesPopulated.append(tempPos)
            return True
        return super()._doUnpackedCommand(opcode, operands)

    def updateMouseOffset(self, pos):
        self.activeTilePos = (pos[0] - self.activeTileMouseOffset[0],
                              pos[1] - self.activeTileMouseOffset[1])
        if self.activeTilePos[1] < RESOLUTION_NINTENDO_DS[1]:
            self.activeTilePos = (pos[0] - self.activeTileMouseOffset[0],
                                  RESOLUTION_NINTENDO_DS[1])
        if self.activeTilePos[1] > (RESOLUTION_NINTENDO_DS[1] * 2) - self.imageBall.get_height():
            self.activeTilePos = (self.activeTilePos[0],
                                  (RESOLUTION_NINTENDO_DS[1] * 2) - self.imageBall.get_height())
        if self.activeTilePos[0] + self.imageBall.get_width() > HandlerShortbrimPegSolitaire.BALL_X_LIMIT:
            self.activeTilePos = (HandlerShortbrimPegSolitaire.BALL_X_LIMIT - self.imageBall.get_width(),
                                  self.activeTilePos[1])
        if self.activeTilePos[0] < 0:
            self.activeTilePos = (0, self.activeTilePos[1])

    def handleTouchEventPuzzleElements(self, event):

        def tileToScreenPos(tilePos):
            return (self.posCorner[0] + tilePos[0] * self.tileDimensions[0],
                    self.posCorner[1] + tilePos[1] * self.tileDimensions[1] + RESOLUTION_NINTENDO_DS[1])
        def screenPosToTile(screenPos):
            screenPos = ((screenPos[0] - self.posCorner[0]) // self.tileDimensions[0],
                         (screenPos[1] - RESOLUTION_NINTENDO_DS[1] - self.posCorner[1]) // self.tileDimensions[1])
            return screenPos

        if event.type == MOUSEBUTTONDOWN:
            if event.pos[0] >= self.posCorner[0] and event.pos[1] >= self.posCorner[1] + RESOLUTION_NINTENDO_DS[1]:
                if (event.pos[0] < self.posCorner[0] + self.tileDimensions[0] * self.tileBoardDimensions[0] and
                    event.pos[1] < self.posCorner[1] + RESOLUTION_NINTENDO_DS[1] + self.tileDimensions[1] * self.tileBoardDimensions[1]):   # Clicked on grid
                    deltaTilesX = (event.pos[0] - self.posCorner[0]) // self.tileDimensions[0]
                    deltaTilesY = (event.pos[1] - RESOLUTION_NINTENDO_DS[1] - self.posCorner[1]) // self.tileDimensions[1]
                    tempPos = (deltaTilesX, deltaTilesY)
                    if self.isSpacePopulated(tempPos):
                        tilePos = tileToScreenPos(tempPos)
                        self.activeTile = self.tilesPopulated.index(tempPos)
                        self.activeTileMouseOffset = (event.pos[0] - tilePos[0],
                                                      event.pos[1] - tilePos[1])
                        self.updateMouseOffset(event.pos)
                        return True

        elif event.type == MOUSEMOTION:
            if self.activeTile != None:
                self.updateMouseOffset(event.pos)
                return True
        elif event.type == MOUSEBUTTONUP:
            if self.activeTile != None:
                self.updateMouseOffset(event.pos)
                tempPos = screenPosToTile(event.pos)
                if self.isSpaceAvailable(tempPos) and not self.isSpacePopulated(tempPos):
                    deltaPos = (tempPos[0] - self.tilesPopulated[self.activeTile][0], tempPos[1] - self.tilesPopulated[self.activeTile][1])
                    deltaAbsPos = (abs(deltaPos[0]), abs(deltaPos[1]))
                    if deltaAbsPos == (2,0) or deltaAbsPos == (0,2):  # Check if moving 2 spaces
                        tempObsPos = (self.tilesPopulated[self.activeTile][0] + deltaPos[0] // 2, self.tilesPopulated[self.activeTile][1] + deltaPos[1] // 2)
                        if self.isSpacePopulated(tempObsPos):
                            self.tilesPopulated[self.activeTile] = tempPos
                            del (self.tilesPopulated[self.tilesPopulated.index(tempObsPos)])
                self.activeTile = None
                return True
        return False