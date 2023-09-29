from widebrim.engine_ext.utils import getBottomScreenAnimFromPath
from widebrim.engine.anim.fader import Fader
from widebrim.engine.anim.button import StaticButton
from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.madhatter.common import logSevere
from widebrim.madhatter.typewriter.strings_lt2 import OPCODES_LT2

from .rose_short import RoseWall

from .base import BaseQuestionObject
from .const import PATH_ANI_ICESKATE

# TODO - Remove class images, they add slowdown as all will be loaded at boot

# Ported from shortbrim
# TODO - Rewrite with better code style

class HandlerShortbrimSkate(BaseQuestionObject):

    TIME_PER_TILE = 400

    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)

        self.__bankImages = getBottomScreenAnimFromPath(laytonState, PATH_ANI_ICESKATE)

        def setAnimationFromNameAndReturnInitialFrame(name):
            if self.__bankImages.setAnimationFromName(name):
                return self.__bankImages.getActiveFrame()
            return None

        self.posCorner = (0,0)
        self.tileBoardDimensions = (0,0)
        self.tileDimensions = (16,16)
        self.posSpawn = (0,0)
        self.posExit = (0,0)

        self.sourceAnimPosCharacter = (0,0)
        self.posCharacter = (0,0)
        self.isCharacterAnimating = False

        self.wallsHorizontal = []
        self.wallsVertical = []

        self.arrowLeft = StaticButton((0,0), setAnimationFromNameAndReturnInitialFrame("left"), callback=self.startMovementLeft)
        self.arrowRight = StaticButton((0,0), setAnimationFromNameAndReturnInitialFrame("right"), callback=self.startMovementRight)
        self.arrowUp = StaticButton((0,0), setAnimationFromNameAndReturnInitialFrame("up"), callback=self.startMovementUp)
        self.arrowDown = StaticButton((0,0), setAnimationFromNameAndReturnInitialFrame("down"), callback=self.startMovementDown)
        self.__bankImages.setAnimationFromName("layton")

        self.movementFader = None
        self.movementPossibilities = [0,0,0,0]
    
    def hasSubmitButton(self):
        return False

    def _doReset(self):
        self.posCharacter = self.sourceAnimPosCharacter
        self.isCharacterAnimating = False
        self.movementFader = None
        self.movementPossibilities = self.getMovementOpportunities()
        self.generateGraphicsPositions()
        return super()._doReset()

    def isOccluded(self, tilePos, isVertical, isHorizontal, movingInPositiveDirection):
        # TODO - Find a way to bend the rules and get this inherited from the Rose handler instead
        # TODO - Can the wall collision be used here?
        if isHorizontal and (tilePos[1] < 0 or tilePos[1] >= self.tileBoardDimensions[1]):
            return True
        if isVertical and (tilePos[0] < 0 or tilePos[0] >= self.tileBoardDimensions[0]):
            return True

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
    
    def getMovementOpportunities(self):
        output = [0,0,0,0]

        for upMovement in range(self.posCharacter[1]):
            tempPos = (self.posCharacter[0], self.posCharacter[1] - upMovement)
            if self.isOccluded(tempPos, True, False, True):
                break
            else:
                output[2] += 1
        for downMovement in range(self.tileBoardDimensions[1] - self.posCharacter[1] - 1):
            tempPos = (self.posCharacter[0], self.posCharacter[1] + downMovement)
            if self.isOccluded(tempPos, True, False, False):
                break
            else:
                output[3] += 1
        for leftMovement in range(self.posCharacter[0]):
            tempPos = (self.posCharacter[0] - leftMovement, self.posCharacter[1])
            if self.isOccluded(tempPos, False, True, False):
                break
            else:
                output[0] += 1
        for rightMovement in range(self.tileBoardDimensions[0] - self.posCharacter[0] - 1):
            tempPos = (self.posCharacter[0] + rightMovement, self.posCharacter[1])
            if self.isOccluded(tempPos, False, True, True):
                break
            else:
                output[1] += 1
        
        # Correct for misaligned exit
        if (self.posCharacter[0] - output[0] - 1, self.posCharacter[1]) == self.posExit:
            output[0] += 1
        if (self.posCharacter[0] + output[1] + 1, self.posCharacter[1]) == self.posExit:
            output[1] += 1
        if (self.posCharacter[0], self.posCharacter[1] - output[2] - 1) == self.posExit:
            output[2] += 1
        if (self.posCharacter[0], self.posCharacter[1] + output[3] + 1) == self.posExit:
            output[3] += 1
        
        return output

    def drawPuzzleElements(self, gameDisplay):
        if not(self.isCharacterAnimating):
            if self.movementPossibilities[0] > 0:
                self.arrowLeft.draw(gameDisplay)
            if self.movementPossibilities[1] > 0:
                self.arrowRight.draw(gameDisplay)
            if self.movementPossibilities[2] > 0:
                self.arrowUp.draw(gameDisplay)
            if self.movementPossibilities[3] > 0:
                self.arrowDown.draw(gameDisplay)

        self.__bankImages.draw(gameDisplay)

    def _wasAnswerSolution(self):
        return True

    def doOnComplete(self):
        self.movementPossibilities = self.getMovementOpportunities()
        self.generateGraphicsPositions()
        return super().doOnComplete()

    def updatePuzzleElements(self, gameClockDelta):

        if self.isCharacterAnimating:

            self.movementFader.update(gameClockDelta)
            
            if not(self.movementFader.getActiveState()):
                self.isCharacterAnimating = False
                if self.posCharacter == self.posExit:
                    self.movementPossibilities = [0,0,0,0]
                    self._startJudgement()
                else:
                    self.movementPossibilities = self.getMovementOpportunities()
            
            self.generateGraphicsPositions()

        self.__bankImages.update(gameClockDelta)

    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.Skate_SetInfo.value:
            self.posCorner = (operands[0].value, operands[1].value)
            self.tileBoardDimensions = (operands[2].value, operands[3].value)
            self.posSpawn = (operands[4].value, operands[5].value)
            self.posCharacter = self.posSpawn
            self.posExit = (operands[6].value, operands[7].value)  # This can be negative to signal that the player exits off the grid.
        elif opcode == OPCODES_LT2.Skate_AddWall.value:
            if operands[0].value == operands[2].value:
                self.wallsVertical.append(RoseWall((operands[0].value, operands[1].value), (operands[2].value, operands[3].value)))
            elif operands[1].value == operands[3].value:
                self.wallsHorizontal.append(RoseWall((operands[0].value, operands[1].value), (operands[2].value, operands[3].value)))
            else:
                logSevere("Unsupported line: Wall from", (operands[0].value, operands[1].value), "to", (operands[2].value, operands[3].value), "isn't vertical or horizontal!", name="NazoIceSkate")
                return False
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True

    def generateGraphicsPositions(self):

        def tileToScreenPos(tilePos):
            return (self.posCorner[0] + tilePos[0] * self.tileDimensions[0],
                    self.posCorner[1] + tilePos[1] * self.tileDimensions[1])

        tempScreenPos = tileToScreenPos(self.posCharacter)
        tempScreenPos = (tempScreenPos[0], tempScreenPos[1] + RESOLUTION_NINTENDO_DS[1])

        if self.isCharacterAnimating:
            initTempScreenPos = tileToScreenPos(self.sourceAnimPosCharacter)
            initTempScreenPos = (initTempScreenPos[0], initTempScreenPos[1] + RESOLUTION_NINTENDO_DS[1])
            deltaPos = ((tempScreenPos[0] - initTempScreenPos[0]),
                        (tempScreenPos[1] - initTempScreenPos[1]))
            tempScreenPos = (round(initTempScreenPos[0] + deltaPos[0] * self.movementFader.getStrength()),
                            round(initTempScreenPos[1] + deltaPos[1] * self.movementFader.getStrength()))
        else:
            self.__bankImages.setAnimationFromName("layton")
            self.arrowLeft.setPos((tempScreenPos[0] - self.tileDimensions[0], tempScreenPos[1]))
            self.arrowRight.setPos((tempScreenPos[0] + self.tileDimensions[0], tempScreenPos[1]))
            self.arrowUp.setPos((tempScreenPos[0], tempScreenPos[1] - self.tileDimensions[1]))
            self.arrowDown.setPos((tempScreenPos[0], tempScreenPos[1] + self.tileDimensions[1]))
        
        self.__bankImages.setPos(tempScreenPos)

    def startMovement(self, animName, newPos, distance):
        self.sourceAnimPosCharacter = self.posCharacter
        self.__bankImages.setAnimationFromName(animName)
        self.isCharacterAnimating = True
        self.posCharacter = newPos
        self.movementFader = Fader(HandlerShortbrimSkate.TIME_PER_TILE * distance)

    def startMovementLeft(self):
        self.startMovement("move_left", (self.posCharacter[0] - self.movementPossibilities[0], self.posCharacter[1]), self.movementPossibilities[0])
    
    def startMovementRight(self):
        self.startMovement("move_right", (self.posCharacter[0] + self.movementPossibilities[1], self.posCharacter[1]), self.movementPossibilities[1])
    
    def startMovementUp(self):
        self.startMovement("move_up", (self.posCharacter[0], self.posCharacter[1] - self.movementPossibilities[2]), self.movementPossibilities[2])
    
    def startMovementDown(self):
        self.startMovement("move_down", (self.posCharacter[0], self.posCharacter[1] + self.movementPossibilities[3]), self.movementPossibilities[3])

    def handleTouchEventPuzzleElements(self, event):
        if not(self.isCharacterAnimating):
            return self.arrowLeft.handleTouchEvent(event) or self.arrowRight.handleTouchEvent(event) or self.arrowUp.handleTouchEvent(event) or self.arrowDown.handleTouchEvent(event)