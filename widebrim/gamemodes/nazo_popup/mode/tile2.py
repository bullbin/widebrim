from pygame.constants import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION
from .base import BaseQuestionObject
from ....engine_ext.utils import getBottomScreenAnimFromPath
from ....engine.const import RESOLUTION_NINTENDO_DS
from ....madhatter.typewriter.strings_lt2 import OPCODES_LT2
from .const import PATH_ANI_TILE2, PATH_ANI_TILE

from pygame import Rect, draw
from pygame.transform import rotate

# Tile2_AddCheckRotate
# IndexTile, IndexPoint, Direction (0-3)

# Tile2_AddCheckNormal
# IndexTile, IndexPoint

class Tile():
    def __init__(self, resource, offsetX, offsetY, animNameSpawn, animNameTouch, animNameIdle, indexTile, indexSpawnPoint, allowRotation, spawnRot=0):
        self.allowRotation = allowRotation == True
        self.indexTile = indexTile

        self.indexPoint = indexSpawnPoint
        self.indexSpawnPoint = indexSpawnPoint
        self.targetPoint = None
        self.targetRot = None
        self.resource = resource

        self.indexRotation = 0
        self.frame = None

        # custom center point
        # When the tile is grabbed, tile teleports to this location.
        self.offset = (offsetX, offsetY)
        if resource != None:
            self.resource.setAnimationFromName(animNameSpawn)
            self.frame = self.resource.getActiveFrame()
        
        self.rectsMovement = []
        self.rectsRotation = []

        if self.allowRotation:
            spawnRot = spawnRot % 4
            while self.indexRotation != spawnRot:
                self.rotateClockwise90Deg()
            self.indexSpawnRot = spawnRot
        else:
            self.indexSpawnRot = 0

    def setMovementRegion(self, cornerBottomLeft, dimensions):
        self.rectsMovement.append(Rect(cornerBottomLeft, dimensions))

    def setRotationRegion(self, cornerBottomLeft, dimensions):
        self.rectsRotation.append(Rect(cornerBottomLeft, dimensions))

    def reset(self):
        self.indexPoint = self.indexSpawnPoint
        while self.indexRotation != self.indexSpawnRot:
            self.rotateClockwise90Deg()
    
    def isPointCorrect(self):
        if self.targetPoint == None:
            return True
        return self.targetPoint == self.indexPoint
    
    def isRotCorrect(self):
        if self.allowRotation:
            if self.targetRot != None:
                # TODO - Is normal check allowed in rotation mode?
                return (self.indexRotation == self.targetRot) or (self.targetRot < 0)
        return True
    
    def _wasClicked(self, rectList, shapePoint, pos):
        x, y = shapePoint
        y += RESOLUTION_NINTENDO_DS[1]

        for tileRect in rectList:
            moveRect = tileRect.copy()
            moveRect.move_ip((x,y))
            if moveRect.collidepoint(pos):
                return True
        return False

    def debugDraw(self, shapePoint, gameDisplay):
        x, y = shapePoint
        y += RESOLUTION_NINTENDO_DS[1]

        for tileRect in self.rectsRotation:
            moveRect = tileRect.copy()
            moveRect.move_ip((x,y))
            draw.rect(gameDisplay, (255,0,0), moveRect)
        return False

    def wasClickedMove(self, shapePoint, pos):
        return self._wasClicked(self.rectsMovement, shapePoint, pos)
    
    def wasClickedRot(self, shapePoint, pos):
        return self._wasClicked(self.rectsRotation, shapePoint, pos)
    
    def getFrame(self):
        return self.frame
    
    def rotateClockwise90Deg(self):
        # TODO - How do pieces rotate??

        def getRotatedRect(rect : Rect):

            def rotatePoint(point):
                return (point[1], -point[0])

            somePoint = rotatePoint(rect.bottomleft)
            somePoint2 = rotatePoint(rect.topright)

            height = rect.width
            width = rect.height

            x = min(somePoint[0], somePoint2[0])
            y = min(somePoint[1], somePoint2[1])

            return Rect(x, y, width, height)

        frame = self.getFrame()
        if frame != None:
            for indexRect, rect in enumerate(self.rectsMovement):
                self.rectsMovement[indexRect] = getRotatedRect(rect)
            for indexRect, rect in enumerate(self.rectsRotation):
                self.rectsRotation[indexRect] = getRotatedRect(rect)
            self.frame = rotate(frame, 90)
        
        self.indexRotation = (self.indexRotation + 1) % 4
    
    def getFloatingPosition(self, pos):
        # TODO - Rotatable pieces from center, maybe
        x,y = pos

        frame = self.getFrame()
        x -= self.offset[0]
        y -= self.offset[1]

        if frame != None and self.allowRotation:
            # TODO - For rotatable pieces, the position outputted isn't as useful
            x -= frame.get_width() // 2
            y -= frame.get_height() // 2

        if x <= 0:
            x = 0
        if y <= RESOLUTION_NINTENDO_DS[1]:
            y = RESOLUTION_NINTENDO_DS[1]
        
        if frame != None:
            boundX = x + frame.get_width()
            boundY = y + frame.get_height()
            # 192x192 square interactable area
            if boundX >= RESOLUTION_NINTENDO_DS[1]:
                x = RESOLUTION_NINTENDO_DS[1] - frame.get_width()
            if boundY >= RESOLUTION_NINTENDO_DS[1] * 2:
                y = (RESOLUTION_NINTENDO_DS[1] * 2) - frame.get_height()

        return (x,y)

    def getRotateLandingPosition(self, pos):
        x,y = self.getFloatingPosition(pos)
        frame = self.getFrame()
        if frame != None:
            # TODO - For rotatable pieces, the position outputted isn't as useful
            x += frame.get_width() // 2
            y += frame.get_height() // 2
        return (x,y)

class HandlerTile2(BaseQuestionObject):
    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)

        self._canTilesBeSwapped = False

        if laytonState.getNazoData().idHandler == 18:
            self._canTilesBeRotated = True
        else:
            self._canTilesBeRotated = False

        self._resources = {}
        self._resourcesLastIndex = 0
        self._points = []
        self._tiles : Tile = []

        self._tileSelected = None
        self._tileSelectedDrawPos = (0,0)
        self._tileSelectedMoving = False

        self._checkPos = {}
        self._checkRot = {}
    
    def hasMemoButton(self):
        return self.laytonState.getCurrentNazoListEntry().idInternal != 203
    
    def hasQuitButton(self):
        if self.laytonState.getCurrentNazoListEntry().idInternal != 203:
            return True
        else:
            # Has checks for 2 gamemodes
            return False

    def hasSubmitButton(self):
        return self.laytonState.getCurrentNazoListEntry().idInternal != 2 and self.laytonState.getCurrentNazoListEntry().idInternal != 203

    def hasRestartButton(self):
        return self.laytonState.getCurrentNazoListEntry().idInternal != 203

    def _doReset(self):
        for tile in self._tiles:
            tile.reset()
        return super()._doReset()
    
    def _wasAnswerSolution(self):
        for tile in self._tiles:
            if not(tile.isPointCorrect()) or not(tile.isRotCorrect()):
                return False
        return True

    def doOnComplete(self):
        for indexTile, tile in enumerate(self._tiles):
            if indexTile in self._checkPos:
                tile.targetPoint = self._checkPos[indexTile]
            if indexTile in self._checkRot:
                tile.targetRot = self._checkRot[indexTile]
        return super().doOnComplete()

    def drawPuzzleElements(self, gameDisplay):
        # reverse the list, as used objects are put first so they are checked on top first
        for tile in reversed(self._tiles):
            if tile != self._tileSelected and tile.resource != None:
                frame = tile.getFrame()
                indexPoint = tile.indexPoint
                if 0 <= indexPoint < len(self._points):
                    x, y = self._points[indexPoint]
                    y += RESOLUTION_NINTENDO_DS[1]

                    # TODO - Why is the center point behaviour changed for this variant?
                    if self._canTilesBeRotated:
                        x -= (frame.get_width()) // 2
                        y -= (frame.get_height()) // 2

                    gameDisplay.blit(frame, (x,y))
                    # tile.debugDraw(self._points[indexPoint], gameDisplay)

        if self._tileSelected != None and self._tileSelected.getFrame() != None:
            if self._tileSelectedMoving:
                gameDisplay.blit(self._tileSelected.getFrame(), self._tileSelected.getFloatingPosition(self._tileSelectedDrawPos))
            else:
                frame = self._tileSelected.getFrame()
                indexPoint = self._tileSelected.indexPoint
                if 0 <= indexPoint < len(self._points):
                    x, y = self._points[indexPoint]
                    y += RESOLUTION_NINTENDO_DS[1]

                    # TODO - Why is the center point behaviour changed for this variant?
                    if self._canTilesBeRotated:
                        x -= (frame.get_width()) // 2
                        y -= (frame.get_height()) // 2

                    gameDisplay.blit(frame, (x,y))

        return super().drawPuzzleElements(gameDisplay)
        
    def _doUnpackedCommand(self, opcode, operands):
        # TODO - Check if order of operands matters - it probably very much does
        # TODO - Actually reverse some of this, most was intuition
        if opcode == OPCODES_LT2.Tile2_AddSprite.value and len(operands) == 1:
            if self._canTilesBeRotated:
                animResource = PATH_ANI_TILE2 % operands[0].value
            else:
                animResource = PATH_ANI_TILE % operands[0].value
            if len(animResource) > 64:
                animResource = animResource[:64]
            if "?" in animResource:
                animResource = animResource.replace("?", self.laytonState.language.value)

            self._resources[self._resourcesLastIndex] = animResource
            self._resourcesLastIndex += 1
        elif opcode == OPCODES_LT2.Tile2_AddPoint.value and len(operands) == 2:
            if len(self._points) < 64:
                self._points.append((operands[0].value, operands[1].value))
        elif opcode == OPCODES_LT2.Tile2_AddPointGrid.value and len(operands) == 6:
            # Stubbed
            pass
        elif opcode == OPCODES_LT2.Tile2_AddObjectNormal.value and len(operands) == 7:
            if len(self._tiles) < 32:
                tile = Tile(self._getCopyOfResource(operands[0].value),
                            operands[1].value, operands[2].value,
                            operands[3].value, operands[5].value, operands[6].value, len(self._tiles),
                            operands[6].value, self._canTilesBeRotated)
                self._tiles.append(tile)
        elif opcode == OPCODES_LT2.Tile2_AddObjectRotate.value and len(operands) == 8:
            if len(self._tiles) < 32:
                # TODO - Add rotation param (last operand)
                tile = Tile(self._getCopyOfResource(operands[0].value),
                            operands[1].value, operands[2].value,
                            operands[3].value, operands[5].value, operands[6].value, len(self._tiles),
                            operands[6].value, self._canTilesBeRotated, spawnRot=operands[7].value)
                self._tiles.append(tile)
        elif opcode == OPCODES_LT2.Tile2_AddObjectRange.value and len(operands) == 4:
            if len(self._tiles) > 0:
                if self._canTilesBeRotated:
                    self._tiles[-1].setRotationRegion((operands[0].value, operands[1].value),
                                                      (operands[2].value, operands[3].value))
                else:
                    self._tiles[-1].setMovementRegion((operands[0].value, operands[1].value),
                                                      (operands[2].value, operands[3].value))
        elif opcode == OPCODES_LT2.Tile2_AddCheckNormal.value and len(operands) == 2:
            self._checkPos[operands[0].value] = operands[1].value
        elif opcode == OPCODES_LT2.Tile2_AddCheckRotate.value and len(operands) == 3:
            self._checkPos[operands[0].value] = operands[1].value
            self._checkRot[operands[0].value] = operands[2].value
        elif opcode == OPCODES_LT2.Tile2_AddObjectRange2.value and len(operands) == 4:
            if len(self._tiles) > 0:
                if self._canTilesBeRotated:
                    self._tiles[-1].setMovementRegion((operands[0].value, operands[1].value),
                                                      (operands[2].value, operands[3].value))

        elif opcode == OPCODES_LT2.Tile2_SwapOn.value and len(operands) == 0:
            self._canTilesBeSwapped = True
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True

    def _getCopyOfResource(self, indexResource):
        # Duplicate resource for tile
        # TODO - Create a way to copy anim or have duplicates playing to reduce memory usage
        if indexResource in self._resources:
            return getBottomScreenAnimFromPath(self.laytonState, self._resources[indexResource])
        return None

    def _updateTilePoint(self, tile, pos):
        if self._canTilesBeRotated:
            x,y = tile.getRotateLandingPosition(pos)
        else:
            x,y = tile.getFloatingPosition(pos)
        y -= RESOLUTION_NINTENDO_DS[1]
        
        minDistance = None
        minPoint = None

        for indexPoint, point in enumerate(self._points):
            pointX, pointY = point

            # sqrt not needed really...
            distance = (pointX - x) ** 2 + (pointY - y) ** 2
            if minDistance == None or (distance <= minDistance):
                if not(self._canTilesBeSwapped):

                    isOccupied = False
                    for checkTile in self._tiles:
                        if checkTile != tile:
                            if checkTile.indexPoint == indexPoint:
                                isOccupied = True
                                break
                    
                    if not(isOccupied):
                        minDistance = distance
                        minPoint = indexPoint
                else:
                    # TODO - remember to swap in this case - find occupying tiles if needed
                    minDistance = distance
                    minPoint = indexPoint

        # TODO - sorting objects to ensure not drawn over one another - pop and readd to list...
        if self._canTilesBeSwapped:
            for checkTile in self._tiles:
                if checkTile.indexPoint == minPoint:
                    checkTile.indexPoint = tile.indexPoint
                    break
        tile.indexPoint = minPoint

        # TODO - This will need to change once animations are added to avoid removing used objects
        self._tiles.remove(tile)
        self._tiles.insert(0, tile)

    def _doOnTileFinishedInteracting(self):
        if not(self.hasSubmitButton()):
            # If the user found the solution, stop
            if self._wasAnswerSolution():
                self._startJudgement()

    def handleTouchEventPuzzleElements(self, event):
        # TODO - Animation to fade picking up and dropping down
        if event.type == MOUSEBUTTONDOWN:
            # Find if mouse cursor has collided with any event bounding boxes
            for tile in self._tiles:
                indexPoint = tile.indexPoint
                if 0 <= indexPoint < len(self._points):
                    wasClickedMove = tile.wasClickedMove(self._points[indexPoint], event.pos)
                    wasClickedRot = tile.wasClickedRot(self._points[indexPoint], event.pos)
                    if wasClickedMove or wasClickedRot:
                        self._tileSelected = tile
                        self._tileSelectedDrawPos = event.pos

                        if (wasClickedMove and not wasClickedRot) or (wasClickedRot and wasClickedMove):
                            # wasClickedMove behaviour
                            self._tileSelectedMoving = True
                        else:
                            self._tileSelectedMoving = False
                        return True

        if self._tileSelected != None:
            if self._tileSelectedMoving:
                if event.type == MOUSEMOTION:
                    self._tileSelectedDrawPos = event.pos
                if event.type == MOUSEBUTTONUP:
                    # event is offset by the center point, calculate position
                    self._updateTilePoint(self._tileSelected, event.pos)
                    self._doOnTileFinishedInteracting()
                    self._tileSelected = None
            else:
                if event.type == MOUSEBUTTONUP:
                    self._tileSelected.rotateClockwise90Deg()
                    self._doOnTileFinishedInteracting()
                    self._tileSelected = None
        
        return super().handleTouchEventPuzzleElements(event)