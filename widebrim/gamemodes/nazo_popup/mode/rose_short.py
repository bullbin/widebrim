from widebrim.engine_ext.utils import getBottomScreenAnimFromPath
from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.madhatter.common import logSevere
from widebrim.madhatter.typewriter.strings_lt2 import OPCODES_LT2

from .base import BaseQuestionObject
from .const import PATH_ANI_ROSE

from pygame import Surface, MOUSEBUTTONDOWN

class RoseWall():
    def __init__(self, start, end):
        # TODO - Rearrange points to make them move positively, the rose wall logic only checks under these cases
        # TODO - These are unsigned anyway, right?
        self.posCornerStart = start
        self.posCornerEnd = end
    
    def isOnWall(self, pos):
        
        def testInBounds(pos):
            minX = [self.posCornerStart[0], self.posCornerEnd[0]]
            minY = [self.posCornerEnd[1], self.posCornerStart[1]]
            minX.sort()
            minY.sort()
            if (pos[0] >= minX[0] and pos[0] <= minX[1] and
                pos[1] >= minY[0] and pos[1] <= minY[1]):
                return True
            return False

        if testInBounds(pos):
            if pos == self.posCornerStart or pos == self.posCornerEnd:
                return True
            elif self.posCornerStart[0] == self.posCornerEnd[0]:
                # Vertical line
                return pos[0] == self.posCornerStart[0]
            elif self.posCornerStart[1] == self.posCornerEnd[1]:
                # Horizontal line
                return pos[1] == self.posCornerStart[1]
            else:
                gradWall = (self.posCornerEnd[1] - self.posCornerStart[1]) / (self.posCornerEnd[0] - self.posCornerStart[0])
                if pos[0] - self.posCornerStart[0] > 0:
                    gradPoint = (pos[1] - self.posCornerStart[1]) / (pos[0] - self.posCornerStart[0])
                    return gradWall == gradPoint or gradWall == -gradPoint
        return False

class HandlerShortbrimRose(BaseQuestionObject):

    COLOR_ALPHA = (240,0,0)

    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)

        self.tileBoardDimensions = (0,0)
        self.posCorner = (0,0)
        self.tileDimensions = (24,24)
        self.overlaySurface = Surface(RESOLUTION_NINTENDO_DS)
        self.overlaySurface.set_colorkey(HandlerShortbrimRose.COLOR_ALPHA)
        self.overlaySurface.fill(HandlerShortbrimRose.COLOR_ALPHA)

        self.wallsVertical = []
        self.wallsHorizontal = []

        resource = getBottomScreenAnimFromPath(laytonState, PATH_ANI_ROSE)

        def setAnimationFromNameAndReturnInitialFrame(name):
            if resource != None and resource.setAnimationFromName(name):
                return resource.getActiveFrame()
            return None
        
        # Interface as surfaces rather than static images just for any speedup
        self.imageRose = setAnimationFromNameAndReturnInitialFrame("rose")
        self.imageTile = setAnimationFromNameAndReturnInitialFrame("one")
        self.imageOcclude = setAnimationFromNameAndReturnInitialFrame("two")
        if self.imageRose == None or self.imageTile == None or self.imageOcclude == None:
            self.imageRose = Surface(self.tileDimensions)
            self.imageTile = Surface(self.tileDimensions)
            self.imageOcclude = Surface(self.tileDimensions)

        self.activeRoses = {}
        self.activeTileMap = {}
    
    def isOccluded(self, tilePos, isVertical, isHorizontal, movingInPositiveDirection):
        wallsToConsider = []
        if isVertical:
            if movingInPositiveDirection:   # If moving in positive direction, don't subtract from original co-ordinate
                targetAxis = tilePos[1]
            else:
                targetAxis = tilePos[1] + 1
            for wall in self.wallsHorizontal:   # Preprocess walls
                if wall.posCornerStart[1] == targetAxis:
                    wallsToConsider.append(wall)
            for wall in wallsToConsider:    # Test simple one-axis collision
                if wall.posCornerStart[0] <= tilePos[0] and wall.posCornerEnd[0] > tilePos[0]:
                    return True

        elif isHorizontal:
            if movingInPositiveDirection:
                targetAxis = tilePos[0] + 1
            else:
                targetAxis = tilePos[0]
            for wall in self.wallsVertical:   # Preprocess walls
                if wall.posCornerStart[0] == targetAxis:
                    wallsToConsider.append(wall)
            for wall in wallsToConsider:
                if wall.posCornerStart[1] <= tilePos[1] and wall.posCornerEnd[1] > tilePos[1]:
                    return True
        return False   

    def isOnMap(self, rosePos):
        if rosePos[0] >= 0 and rosePos[0] < self.tileBoardDimensions[0]:
            if rosePos[1] >= 0 and rosePos[1] < self.tileBoardDimensions[1]:
                return True
        return False

    def generateRoseMask(self, rosePos):

        def checkAroundQuadrant(quadrant):
            unocclusions = []
            if self.isOnMap((quadrant[0], quadrant[1] - 1)) and not(self.isOccluded(quadrant, True, False, True)):    # up
                unocclusions.append((quadrant[0], quadrant[1] - 1))
            if self.isOnMap((quadrant[0], quadrant[1] + 1)) and not(self.isOccluded(quadrant, True, False, False)):   # down
                unocclusions.append((quadrant[0], quadrant[1] + 1))
            if self.isOnMap((quadrant[0] + 1, quadrant[1])) and not(self.isOccluded(quadrant, False, True, True)):    # right
                unocclusions.append((quadrant[0] + 1, quadrant[1]))
            if self.isOnMap((quadrant[0] - 1, quadrant[1])) and not(self.isOccluded(quadrant, False, True, False)):   # left
                unocclusions.append((quadrant[0] - 1, quadrant[1]))
            return unocclusions

        lightMask = []
        tempBuffer = []
        unoccludedQuadrants = checkAroundQuadrant(rosePos)
        tempBuffer.extend(unoccludedQuadrants)
        for quadrant in unoccludedQuadrants:
            tempBuffer.extend(checkAroundQuadrant(quadrant))
        for item in tempBuffer:
            if item not in lightMask:
                lightMask.append(item)
                
        return lightMask

    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.SetRoseInfo.value:
            self.tileBoardDimensions = (operands[2].value, operands[3].value)
            self.posCorner = (operands[0].value, operands[1].value)
        elif opcode == OPCODES_LT2.AddRoseWall.value:
            if operands[0].value == operands[2].value:
                self.wallsVertical.append(RoseWall((operands[0].value, operands[1].value), (operands[2].value, operands[3].value)))
            elif operands[1].value == operands[3].value:
                self.wallsHorizontal.append(RoseWall((operands[0].value, operands[1].value), (operands[2].value, operands[3].value)))
            else:
                logSevere("Unsupported line: Wall from", (operands[0].value, operands[1].value), "to", (operands[2].value, operands[3].value), "isn't vertical or horizontal!", name="NazoRoseWall")
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True
    
    def hasSubmitButton(self):
        return False

    def _wasAnswerSolution(self):
        return True

    def _doReset(self):
        self.activeRoses = {}
        self.activeTileMap = {}
        self.generateOverlaySurface()

    def addElement(self, tilePos):
        tilesUnoccluded = self.generateRoseMask(tilePos)
        self.activeRoses[tilePos] = tilesUnoccluded
        for tile in tilesUnoccluded:
            if tile in self.activeTileMap.keys():
                self.activeTileMap[tile] += 1
            else:
                self.activeTileMap[tile] = 1

    def removeElement(self, tilePos):
        for tile in self.activeRoses[tilePos]:
            if self.activeTileMap[tile] < 2:
                del self.activeTileMap[tile]
            else:
                self.activeTileMap[tile] -= 1
        del self.activeRoses[tilePos]

    def generateOverlaySurface(self):

        def tileToScreenPos(tilePos):
            return (self.posCorner[0] + tilePos[0] * self.tileDimensions[0],
                    self.posCorner[1] + tilePos[1] * self.tileDimensions[1])

        self.overlaySurface.fill(self.overlaySurface.get_colorkey())

        countPos = 0
        solved = True
        for tilePos in self.activeTileMap.keys():
            if self.activeTileMap[tilePos] > 1:
                self.overlaySurface.blit(self.imageOcclude, tileToScreenPos(tilePos))
                solved = False
            else:
                self.overlaySurface.blit(self.imageTile, tileToScreenPos(tilePos))
            countPos += 1

        for tilePos in self.activeRoses.keys():
            self.overlaySurface.blit(self.imageRose, tileToScreenPos(tilePos))
        
        if countPos == (self.tileBoardDimensions[0] * self.tileBoardDimensions[1]) and solved:
            self._startJudgement()
    
    def isSpacePopulated(self, pos):
        return pos in self.activeRoses.keys()
    
    def drawPuzzleElements(self, gameDisplay):
        gameDisplay.blit(self.overlaySurface, (0, RESOLUTION_NINTENDO_DS[1]))

    def behaviourWhenSpacePressed(self, pos):
        if self.isSpacePopulated(pos):
            self.removeElement(pos)
        else:
            self.addElement(pos)
        self.generateOverlaySurface()

    def handleTouchEventPuzzleElements(self, event):
        if event.type == MOUSEBUTTONDOWN:
            if event.pos[0] >= self.posCorner[0] and event.pos[1] >= self.posCorner[1] + RESOLUTION_NINTENDO_DS[1]:
                if (event.pos[0] < self.posCorner[0] + self.tileDimensions[0] * self.tileBoardDimensions[0] and
                    event.pos[1] < self.posCorner[1] + RESOLUTION_NINTENDO_DS[1] + self.tileDimensions[1] * self.tileBoardDimensions[1]):   # Clicked on grid
                    deltaTilesX = (event.pos[0] - self.posCorner[0]) // self.tileDimensions[0]
                    deltaTilesY = (event.pos[1] - RESOLUTION_NINTENDO_DS[1] - self.posCorner[1]) // self.tileDimensions[1]
                    tempPos = (deltaTilesX, deltaTilesY)
                    self.behaviourWhenSpacePressed(tempPos)
                    return True
        return False