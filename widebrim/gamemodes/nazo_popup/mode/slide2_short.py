from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath
from widebrim.madhatter.typewriter.strings_lt2 import OPCODES_LT2
from .base import BaseQuestionObject
from .const import PATH_ANI_SLIDE2_NUMBERS, PATH_ANI_SLIDE2
from pygame import MOUSEBUTTONUP, MOUSEBUTTONDOWN, MOUSEMOTION, Rect
from math import pi, atan2

# Ported from shortbrim
# TODO - Rewrite with better code style
# TODO - number font renderer

class SlidingShape():

    def __init__(self, cornerPos, isLocked):
        self.isLocked = isLocked
        self.isBound = False
        self.rects = []
        self.bound = Rect(0,0,0,0)
        self.initialPos = cornerPos
        self.cornerTilePos = cornerPos
        self.image = None
    
    def reset(self):
        self.cornerTilePos = self.initialPos

    def addCollisionRect(self, corner, length, tileSize):
        self.rects.append(Rect(corner[0] * tileSize[0], corner[1] * tileSize[1],
                               length[0] * tileSize[0], length[1] * tileSize[1]))
        self.bound = self.bound.union(Rect(corner[0], corner[1],
                                           length[0], length[1]))

    def resolveCollisionRects(self, tileSize):
        output = []
        for rect in self.rects:
            tempCornerPos = (self.cornerTilePos[0] * tileSize[0],
                            self.cornerTilePos[1] * tileSize[1])
            output.append(rect.move(tempCornerPos))
        return output

    def doesIntersect(self, additionalShape, tileSize):
        for rect in self.resolveCollisionRects(tileSize):
            for addRect in additionalShape.resolveCollisionRects(tileSize):
                if rect.colliderect(addRect):
                    return True
        return False
    
    def wasClicked(self, pos, posCorner, tileSize):
        for rect in self.resolveCollisionRects(tileSize):
            rect = rect.move(posCorner)
            if rect.collidepoint(pos):
                return True
        return False

class HandlerShortbrimSlide2(BaseQuestionObject):

    DIRECTION_UP = 0
    DIRECTION_DOWN = 1
    DIRECTION_LEFT = 2
    DIRECTION_RIGHT = 3

    MOVE_COUNTER_POS = (112, 11 + RESOLUTION_NINTENDO_DS[1])

    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)
        self.posCorner = (0,0)
        self.tileBoardDimensions = (0,0)
        self.tileSize = (0,0)
        self.tileMap = None

        self.countMoveFont = getBottomScreenAnimFromPath(laytonState, PATH_ANI_SLIDE2_NUMBERS)
        self.countMoves = 0

        self.shapes = []

        self.tileSolution = {}   # index: (tileX, tileY)
        self.tileInternalToMoveableIndexMap = {}    # Locked shapes can bloat the map, causing answers to stop aligning
        self.tileMoveableIndex = 0

        self.activeTile = None
        self.activeTileMouseGrabOffset = (0,0)
        self.activeTileLastMousePos = None

        self.activeTileCurrentMouseDirection = None
        self.directionRequiresChanging = False
        self.directionNextDirection = None
        
        self.activeTileTempPlace = (0,0)
        self.activeTileTempOffset = (0,0)
        self.activeTileMovementPossibilities = None # L,R,U,D

    def hasSubmitButton(self):
        return False

    def shapeSpaceToScreenSpace(self, shape):
        return (self.posCorner[0] + shape.cornerTilePos[0] * self.tileSize[0],
                self.posCorner[1] + RESOLUTION_NINTENDO_DS[1] + shape.cornerTilePos[1] * self.tileSize[1])

    def drawPuzzleElements(self, gameDisplay):

        def setAnimationFromNameReadyToDraw(name, gameDisplay):
            if self.countMoveFont.setAnimationFromName(name):
                self.countMoveFont.draw(gameDisplay)
        
        # TODO - Use new font handling object
        if self.countMoveFont != None:
            self.countMoveFont.setPos(HandlerShortbrimSlide2.MOVE_COUNTER_POS)
            for char in str('%04d' % self.countMoves):
                setAnimationFromNameReadyToDraw(char, gameDisplay)
                self.countMoveFont.setPos((self.countMoveFont.getPos()[0] + self.countMoveFont.getDimensions()[0] - 1, self.countMoveFont.getPos()[1]))

        if self.activeTileTempPlace != (0,0):
            for shapeIndex, shape in enumerate(self.shapes):
                if shape.image != None and shapeIndex != self.activeTile:
                    gameDisplay.blit(shape.image, self.shapeSpaceToScreenSpace(shape))

            if self.activeTile != None and self.shapes[self.activeTile].image != None:
                gameDisplay.blit(self.shapes[self.activeTile].image, self.activeTileTempPlace)
        else:
            for shapeIndex, shape in enumerate(self.shapes):
                if shape.image != None:
                    gameDisplay.blit(shape.image, self.shapeSpaceToScreenSpace(shape))

    def _doReset(self):
        self.countMoves = 0
        for shape in self.shapes:
            shape.reset()

    def updatePuzzleElements(self, gameClockDelta):

        def snapTileWherePossible():
            if self.activeTileCurrentMouseDirection == HandlerShortbrimSlide2.DIRECTION_UP and self.activeTileMovementPossibilities[2] > 0:
                deltaYPixels =  self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1] + self.activeTileMouseGrabOffset[1] - self.activeTileLastMousePos[1]
                deltaYTiles = round(deltaYPixels / self.tileSize[1])
                if deltaYPixels > 0:
                    if deltaYPixels > self.activeTileMovementPossibilities[2] * self.tileSize[1]: # Beyond screen space
                        deltaYTiles = self.activeTileMovementPossibilities[2]
                        self.activeTileTempPlace = (self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0],
                                                    self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1] - deltaYTiles * self.tileSize[1])
                    else:
                        self.activeTileTempPlace = (self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0],
                                                    self.activeTileLastMousePos[1] - self.activeTileMouseGrabOffset[1])
                    self.activeTileTempOffset = (0, - deltaYTiles)

            elif self.activeTileCurrentMouseDirection == HandlerShortbrimSlide2.DIRECTION_DOWN and self.activeTileMovementPossibilities[3] > 0:
                deltaYPixels = self.activeTileLastMousePos[1] - self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1]
                deltaYTiles = round(deltaYPixels / self.tileSize[1])
                if deltaYPixels > 0:
                    if deltaYPixels > self.activeTileMovementPossibilities[3] * self.tileSize[1]:
                        deltaYTiles = self.activeTileMovementPossibilities[3]
                        self.activeTileTempPlace = (self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0],
                                                    self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1] + deltaYTiles * self.tileSize[1])
                    else:
                        self.activeTileTempPlace = (self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0],
                                                    self.activeTileLastMousePos[1] - self.activeTileMouseGrabOffset[1])
                    self.activeTileTempOffset = (0, deltaYTiles)

            elif self.activeTileCurrentMouseDirection == HandlerShortbrimSlide2.DIRECTION_LEFT and self.activeTileMovementPossibilities[0] > 0:
                deltaXPixels = self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0] - self.activeTileLastMousePos[0] + self.activeTileMouseGrabOffset[0]
                deltaXTiles = round(deltaXPixels / self.tileSize[0])
                if deltaXPixels > 0:
                    if deltaXPixels > self.activeTileMovementPossibilities[0] * self.tileSize[0]:
                        deltaXTiles = self.activeTileMovementPossibilities[0]
                        self.activeTileTempPlace = (self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0] - deltaXTiles * self.tileSize[0],
                                                    self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1])
                    else:
                        self.activeTileTempPlace = (self.activeTileLastMousePos[0] - self.activeTileMouseGrabOffset[0],
                                                    self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1])
                    self.activeTileTempOffset = (- deltaXTiles, 0)

            elif self.activeTileCurrentMouseDirection == HandlerShortbrimSlide2.DIRECTION_RIGHT and self.activeTileMovementPossibilities[1] > 0:
                deltaXPixels = self.activeTileLastMousePos[0] - self.activeTileMouseGrabOffset[0] - self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0]
                deltaXTiles = round(deltaXPixels / self.tileSize[0])
                if deltaXPixels > 0:
                    if deltaXPixels > self.activeTileMovementPossibilities[1] * self.tileSize[0]:
                        deltaXTiles = self.activeTileMovementPossibilities[1]
                        self.activeTileTempPlace = (self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0] + deltaXTiles * self.tileSize[0],
                                                    self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1])
                    else:
                        self.activeTileTempPlace = (self.activeTileLastMousePos[0] - self.activeTileMouseGrabOffset[0],
                                                    self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1])
                    self.activeTileTempOffset = (deltaXTiles, 0)
                
        if self.activeTileCurrentMouseDirection == None:
            self.activeTileCurrentMouseDirection = self.directionNextDirection

        if self.activeTile != None and self.activeTileCurrentMouseDirection != None: # Tile currently being held and has direction
            # First, attempt to move towards new solution
            snapTileWherePossible()
            
            if self.directionRequiresChanging and self.activeTileCurrentMouseDirection != self.directionNextDirection:
                self.applyShapeOffset(self.shapes[self.activeTile])
                self.activeTileMovementPossibilities = self.getMovementOpportunities(self.shapes[self.activeTile])
                self.activeTileCurrentMouseDirection = self.directionNextDirection
                self.directionRequiresChanging = False
            
            # Attempt to move towards new solution
            snapTileWherePossible()

    def applyShapeOffset(self, shape):
        shape.cornerTilePos = (shape.cornerTilePos[0] + self.activeTileTempOffset[0], shape.cornerTilePos[1] + self.activeTileTempOffset[1])
        self.activeTileTempOffset = (0,0)

    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.SetSlide2Info.value:
            self.posCorner = (operands[0].value, operands[1].value)
            self.tileBoardDimensions = (operands[2].value, operands[3].value)
            self.tileSize = (operands[4].value, operands[5].value)
        elif opcode == OPCODES_LT2.AddSlide2Range.value: # Add occlusion
            self.shapes.append(SlidingShape((operands[0].value, operands[1].value), True))
            self.shapes[-1].addCollisionRect((0,0), (operands[2].value, operands[3].value), self.tileSize)
        elif opcode == OPCODES_LT2.AddSlide2Check.value: # Set solution
            self.tileSolution[operands[0].value] = (operands[1].value, operands[2].value)
        elif opcode == OPCODES_LT2.AddSlide2Sprite.value: # Add tilemap
            # TODO - doOnComplete to ensure tile map being a late command doesn't impact future commands
            self.tileMap = getBottomScreenAnimFromPath(self.laytonState, PATH_ANI_SLIDE2 % operands[0].value)
        elif opcode == OPCODES_LT2.AddSlide2Object.value: # Add tile
            # Unk, (animName, animName), (tileX, tileY)
            # TODO - What does operand 0 do?
            # TODO - I think its the index for sprites. Not included in shortbrim, either way.
            self.tileInternalToMoveableIndexMap[self.tileMoveableIndex] = len(self.shapes)
            self.shapes.append(SlidingShape((operands[3].value, operands[4].value), False))
            if self.tileMap != None and self.tileMap.setAnimationFromName(operands[1].value):
                self.shapes[-1].image = self.tileMap.getActiveFrame()
            self.tileMoveableIndex += 1
        elif opcode == OPCODES_LT2.AddSlide2ObjectRange.value: # Add dynamic occlusion data
            self.shapes[-1].addCollisionRect((operands[0].value, operands[1].value), (operands[2].value, operands[3].value), self.tileSize)
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True
    
    def _wasAnswerSolution(self):
        for tileIndex in self.tileSolution.keys():
            if self.shapes[self.tileInternalToMoveableIndexMap[tileIndex]].cornerTilePos != self.tileSolution[tileIndex]:
                return False
        return True

    def getMovementOpportunities(self, shape):
        def hasIntersectedAfterMovement():
            canStop = False
            for checkShape in self.shapes:
                if checkShape != shape:
                    if shape.doesIntersect(checkShape, self.tileSize):
                        canStop = True
                        break
                    if canStop:
                        break
            return canStop

        originalShapeCorner = shape.cornerTilePos
        possibleMovement = [0,0,0,0]

        if shape.cornerTilePos[0] > 0:
            offset = 0
            for _xLeftIndex in range(shape.cornerTilePos[0]):
                shape.cornerTilePos = (shape.cornerTilePos[0] - 1,
                                    shape.cornerTilePos[1])
                if hasIntersectedAfterMovement():
                    offset = 1
                    break
            possibleMovement[0] = originalShapeCorner[0] - shape.cornerTilePos[0] - offset
            shape.cornerTilePos = originalShapeCorner
        
        if shape.cornerTilePos[0] < self.tileBoardDimensions[0] - 1:
            offset = 0
            for _xRightIndex in range(self.tileBoardDimensions[0] - shape.bound.width - shape.cornerTilePos[0]):
                shape.cornerTilePos = (shape.cornerTilePos[0] + 1,
                                    shape.cornerTilePos[1])
                if hasIntersectedAfterMovement():
                    offset = 1
                    break
            possibleMovement[1] = shape.cornerTilePos[0] - originalShapeCorner[0] - offset
            shape.cornerTilePos = originalShapeCorner

        if shape.cornerTilePos[1] > 0:
            offset = 0
            for _yUpIndex in range(shape.cornerTilePos[1]):
                shape.cornerTilePos = (shape.cornerTilePos[0],
                                    shape.cornerTilePos[1] - 1)
                if hasIntersectedAfterMovement():
                    offset = 1
                    break
            possibleMovement[2] = originalShapeCorner[1] - shape.cornerTilePos[1] - offset
            shape.cornerTilePos = originalShapeCorner

        if shape.cornerTilePos[1] < self.tileBoardDimensions[1] - 1:
            offset = 0
            for _yDownIndex in range(self.tileBoardDimensions[1] - shape.bound.height - shape.cornerTilePos[1]):
                shape.cornerTilePos = (shape.cornerTilePos[0],
                                    shape.cornerTilePos[1] + 1)
                if hasIntersectedAfterMovement():
                    offset = 1
                    break
            possibleMovement[3] = shape.cornerTilePos[1] - originalShapeCorner[1] - offset
            shape.cornerTilePos = originalShapeCorner
        
        return possibleMovement

    def flagIfRequiresChanging(self, newDirection):
        if self.activeTileCurrentMouseDirection != newDirection:
            self.directionRequiresChanging = True
            self.directionNextDirection = newDirection

    def handleTouchEventPuzzleElements(self, event):
        if event.type == MOUSEBUTTONDOWN:
            for indexShape, shape in enumerate(self.shapes):
                if not(shape.isLocked):
                    tempPosCorner = (self.posCorner[0], self.posCorner[1] + RESOLUTION_NINTENDO_DS[1])
                    if shape.wasClicked(event.pos, tempPosCorner, self.tileSize):
                        self.activeTileMovementPossibilities = self.getMovementOpportunities(shape)
                        if max(self.activeTileMovementPossibilities) > 0:
                            self.activeTile = indexShape
                            self.activeTileLastMousePos = event.pos
                            self.activeTileMouseGrabOffset = self.shapeSpaceToScreenSpace(shape)
                            self.activeTileMouseGrabOffset = (event.pos[0] - self.activeTileMouseGrabOffset[0],
                                                              event.pos[1] - self.activeTileMouseGrabOffset[1])
                        else:
                            self.activeTile = None
                        break

        elif event.type == MOUSEMOTION:
            if self.activeTile != None:
                if event.pos[1] >= RESOLUTION_NINTENDO_DS[1]:
                    # Recalculate direction of mouse travel
                    tempMouseAngle = atan2(event.pos[1] - self.activeTileLastMousePos[1], event.pos[0] - self.activeTileLastMousePos[0])
                    self.activeTileLastMousePos = event.pos
                    if tempMouseAngle >= pi / 4 and tempMouseAngle < 3 * pi / 4:        # DOWN
                        self.flagIfRequiresChanging(HandlerShortbrimSlide2.DIRECTION_DOWN)
                    elif tempMouseAngle >= 3 * pi / 4 or tempMouseAngle < - 3 * pi / 4: # LEFT
                        self.flagIfRequiresChanging(HandlerShortbrimSlide2.DIRECTION_LEFT)
                    elif tempMouseAngle >= - 3 * pi / 4 and tempMouseAngle < - pi / 4:  # UP
                        self.flagIfRequiresChanging(HandlerShortbrimSlide2.DIRECTION_UP)
                    else:                                                               # RIGHT
                        self.flagIfRequiresChanging(HandlerShortbrimSlide2.DIRECTION_RIGHT)

        elif event.type == MOUSEBUTTONUP:
            if self.activeTile != None and self.activeTileTempPlace != (0,0):
                if self.activeTileTempOffset != (0,0):
                    self.countMoves += 1
                # Apply shape place!
                self.applyShapeOffset(self.shapes[self.activeTile])
                self.activeTileCurrentMouseDirection = None
                self.directionNextDirection = None
                self.directionRequiresChanging = False
                self.activeTileTempPlace = (0,0)
            self.activeTile = None

            if self._wasAnswerSolution():
                self._startJudgement()
