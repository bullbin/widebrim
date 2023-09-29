from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath
from .const import PATH_ANI_PANCAKE, PATH_ANI_SLIDE2_NUMBERS
from pygame import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, Rect
from .base import BaseQuestionObject
from widebrim.madhatter.typewriter.strings_lt2 import OPCODES_LT2

# Ported from shortbrim
# TODO - Rewrite this altogether - so many problems, not accurate, missing end graphics showing all lines, etc...
# TODO - Clip sprites properly on edges

# TODO - Image class
class Pancake():
    def __init__(self, surface, weight):
        self.surface = surface
        self.pos = (0,0)
        self.weight = weight
    
    def draw(self, gameDisplay):
        if self.surface != None:
            gameDisplay.blit(self.surface, self.pos)
    
    def getDimensions(self):
        if self.surface != None:
            return (self.surface.get_width(), self.surface.get_height())
        return (0,0)

    def wasClicked(self, pos):
        dimX, dimY = self.getDimensions()
        posX, posY = self.pos
        maxBounds = (posX + dimX, posY + dimY)
        if self.pos[0] <= pos[0] < maxBounds[0]:
            return self.pos[1] <= pos[1] < maxBounds[1]
        return False

class HandlerShortbrimPancake(BaseQuestionObject):

    PANCAKE_THICKNESS = 8
    PANCAKE_WIDTH = 48
    PANCAKE_X = [31, 96, 159]
    PANCAKE_Y = 146
    PANCAKE_X_LIMIT = 187
    MOVE_COUNTER_POS = (112, 11 + RESOLUTION_NINTENDO_DS[1])

    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)

        self.bankImages = getBottomScreenAnimFromPath(laytonState, PATH_ANI_PANCAKE)
        self.platesTargetHeight = 0
        self.plates = [[],[],[]]
        self.platesColliders = [None, None, None]
        self.activePancakePlateIndex = None
        self.activePancakeMouseButtonOffset = (0,0)
        self.activePancakePos = (0,0)

        self.countMoveFont = getBottomScreenAnimFromPath(laytonState, PATH_ANI_SLIDE2_NUMBERS)
        self.countMoves = 0

    def hasSubmitButton(self):
        return False

    def _getFrameFromBank(self, nameImage):
        # TODO - unify this 
        if self.bankImages != None and self.bankImages.setAnimationFromName(nameImage):
            return self.bankImages.getActiveFrame()
        return None

    def drawPuzzleElements(self, gameDisplay):
        # TODO - Number font renderer
        def setAnimationFromNameReadyToDraw(name, gameDisplay):
            if self.countMoveFont.setAnimationFromName(name):
                self.countMoveFont.draw(gameDisplay)
        
        if self.countMoveFont != None:
            self.countMoveFont.setPos(HandlerShortbrimPancake.MOVE_COUNTER_POS)
            for char in str('%04d' % self.countMoves):
                setAnimationFromNameReadyToDraw(char, gameDisplay)
                self.countMoveFont.setPos((self.countMoveFont.getPos()[0] + self.countMoveFont.getDimensions()[0] - 1, HandlerShortbrimPancake.MOVE_COUNTER_POS[1]))

        for indexPlate, plate in enumerate(self.plates):
            if indexPlate == self.activePancakePlateIndex:
                for pancake in plate[:-1]:
                    pancake.draw(gameDisplay)
            else:
                for pancake in plate:
                    pancake.draw(gameDisplay)
        if self.activePancakePlateIndex != None:
            self.plates[self.activePancakePlateIndex][-1].pos = self.activePancakePos
            self.plates[self.activePancakePlateIndex][-1].draw(gameDisplay)
        
        return super().drawPuzzleElements(gameDisplay)
    
    def _wasAnswerSolution(self):
        if len(self.plates) > 0:
            return len(self.plates[-1]) == self.platesTargetHeight
        return False

    def generatePositions(self):
        for indexPlate, plate in enumerate(self.plates):
            x = HandlerShortbrimPancake.PANCAKE_X[indexPlate]
            y = HandlerShortbrimPancake.PANCAKE_Y
            for pancake in plate:
                pancake.pos = (x - pancake.getDimensions()[0] // 2, y + RESOLUTION_NINTENDO_DS[1])
                y -= HandlerShortbrimPancake.PANCAKE_THICKNESS
            self.platesColliders[indexPlate] = Rect(x - HandlerShortbrimPancake.PANCAKE_WIDTH // 2, y + RESOLUTION_NINTENDO_DS[1] - HandlerShortbrimPancake.PANCAKE_THICKNESS,
                                                    HandlerShortbrimPancake.PANCAKE_WIDTH, HandlerShortbrimPancake.PANCAKE_THICKNESS * 4)

    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.SetPancakeNum.value and len(operands) == 1:
            self.platesTargetHeight = operands[0].value
            for pancakeAnimIndex in range(operands[0].value, 0, -1):
                self.plates[0].append(Pancake(self._getFrameFromBank(str(pancakeAnimIndex)), pancakeAnimIndex))
            self.generatePositions()
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True

    def handleTouchEventPuzzleElements(self, event):
        if event.type == MOUSEBUTTONDOWN:
            for indexPlate, plate in enumerate(self.plates):
                if len(plate) > 0:
                    if plate[-1].wasClicked(event.pos):
                        self.activePancakePlateIndex = indexPlate
                        self.activePancakeMouseButtonOffset = (event.pos[0] - plate[-1].pos[0],
                                                               event.pos[1] - plate[-1].pos[1])
                        self.activePancakePos = plate[-1].pos
                        return True

        elif event.type == MOUSEMOTION and self.activePancakePlateIndex != None:
            self.activePancakePos = (event.pos[0] - self.activePancakeMouseButtonOffset[0],
                                     event.pos[1] - self.activePancakeMouseButtonOffset[1])
            if self.activePancakePos[1] < RESOLUTION_NINTENDO_DS[1]:
                self.activePancakePos = (self.activePancakePos[0], RESOLUTION_NINTENDO_DS[1])
            if self.activePancakePos[0] + self.plates[self.activePancakePlateIndex][-1].getDimensions()[0] > HandlerShortbrimPancake.PANCAKE_X_LIMIT:
                self.activePancakePos = (HandlerShortbrimPancake.PANCAKE_X_LIMIT - self.plates[self.activePancakePlateIndex][-1].getDimensions()[0], self.activePancakePos[1])
            return True

        elif event.type == MOUSEBUTTONUP:
            if self.activePancakePlateIndex != None:
                for indexPlate, collider in enumerate(self.platesColliders):
                    if indexPlate != self.activePancakePlateIndex:
                        if collider.collidepoint(event.pos):
                            if len(self.plates[indexPlate]) > 0:
                                if self.plates[indexPlate][-1].weight > self.plates[self.activePancakePlateIndex][-1].weight:
                                    self.plates[indexPlate].append(self.plates[self.activePancakePlateIndex].pop())
                                    self.countMoves += 1
                            else:
                                self.plates[indexPlate].append(self.plates[self.activePancakePlateIndex].pop())
                                self.countMoves += 1
                self.generatePositions()
            self.activePancakePlateIndex = None
            if self._wasAnswerSolution():
                self._startJudgement()
            return True

        return super().handleTouchEventPuzzleElements(event)