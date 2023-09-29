from widebrim.engine_ext.utils import getBottomScreenAnimFromPath
from widebrim.engine.anim.fader import Fader
from widebrim.engine.const import RESOLUTION_NINTENDO_DS
from widebrim.madhatter.typewriter.strings_lt2 import OPCODES_LT2

from .base import BaseQuestionObject
from .const import PATH_ANI_LAMP

from pygame import Surface, MOUSEBUTTONDOWN
from pygame.draw import line
from .rose_short import RoseWall

from typing import List

# Ported from shortbrim
# TODO - Rewrite this altogether - so many problems, not accurate, missing end graphics showing all lines, etc...

class HandlerShortbrimLamp(BaseQuestionObject):

    TILE_SIZE_LAMP = (16,16)
    COLOR_ALPHA = (240,0,0)

    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)

        self.bankImages = getBottomScreenAnimFromPath(laytonState, PATH_ANI_LAMP)

        def setAnimationFromNameAndReturnInitialFrame(name):
            if self.bankImages.setAnimationFromName(name):
                return self.bankImages.getActiveFrame()
            return None

        self.posCorner = (16,16)        # Hard-coded data for the lamp handler, since the tiles are actually smaller than the grid
        self.tileBoardDimensions = (7,7)
        self.tileDimensions = (24,24)
        self.overlaySurface = Surface(RESOLUTION_NINTENDO_DS)
        self.overlaySurface.set_colorkey(HandlerShortbrimLamp.COLOR_ALPHA)
        self.overlaySurface.fill(HandlerShortbrimLamp.COLOR_ALPHA)

        self.overlayColour = (0,0,0)
        self.tilesUnavailable = []
        self.tilesPopulated = []
        self.tilesSolution = []

        self.movesMinimum = 0
        self.tileToLightLines = {}

        self.lightLines = []
        self.lightLinesFader : List[Fader] = []

        self.overlayTransparentLightShaftSurface = Surface(RESOLUTION_NINTENDO_DS).convert_alpha()
        self.overlayTransparentLightShaftSurface.fill((0,0,0,0))
        self.imageLamp = setAnimationFromNameAndReturnInitialFrame("lamp")
        if self.imageLamp == None:
            self.imageLamp = Surface(HandlerShortbrimLamp.TILE_SIZE_LAMP)

    def isSpaceAvailable(self, pos):
        if pos in self.tilesUnavailable:
            return False
        return True

    def isSpacePopulated(self, pos):
        return pos in self.tilesPopulated

    def behaviourWhenSpacePressed(self, pos):
        if self.isSpacePopulated(pos):
            self.removeElement(pos)
        else:
            self.addElement(pos)
        self.generateOverlaySurface()
    
    def generateOverlaySurface(self):
        
        def tileToScreenPos(tilePos):
            return (self.posCorner[0] + tilePos[0] * self.tileDimensions[0],
                    self.posCorner[1] + tilePos[1] * self.tileDimensions[1])

        self.overlaySurface.fill(self.overlaySurface.get_colorkey())   
        for tilePos in self.tilesPopulated:
            self.overlaySurface.blit(self.imageLamp, tileToScreenPos(tilePos))

    def _wasAnswerSolution(self):
        if len(self.tilesPopulated) <= self.movesMinimum:
            illuminatedLines = []
            for tile in self.tilesPopulated:
                for indexLine in self.tileToLightLines[tile]:
                    if indexLine not in illuminatedLines:
                        illuminatedLines.append(indexLine)
            if len(illuminatedLines) == len(self.lightLines):
                return True
        return False
    
    def drawPuzzleElements(self, gameDisplay):
        gameDisplay.blit(self.overlayTransparentLightShaftSurface, (0, RESOLUTION_NINTENDO_DS[1]))
        gameDisplay.blit(self.overlaySurface, (0, RESOLUTION_NINTENDO_DS[1]))
        return super().drawPuzzleElements(gameDisplay)

    def addElement(self, pos):
        self.tilesPopulated.append(pos)
        if pos not in self.tileToLightLines.keys():
            self.tileToLightLines[pos] = []
            for indexLine in range(len(self.lightLines)):
                if self.lightLines[indexLine].isOnWall(pos):
                    self.tileToLightLines[pos].append(indexLine)

        for indexLine in self.tileToLightLines[pos]:
            self.lightLinesFader[indexLine].reset()
    
    def updatePuzzleElements(self, gameClockDelta):

        def tileToScreenPos(tilePos):
            return ((self.posCorner[0] + 8) + tilePos[0] * self.tileDimensions[0],
                    (self.posCorner[1] + 8) + tilePos[1] * self.tileDimensions[1])

        self.overlayTransparentLightShaftSurface.fill((0,0,0,0))
        for indexLine, lineFader in enumerate(self.lightLinesFader):
            if lineFader.getActiveState():
                lineFader.update(gameClockDelta)
                tempShaftSurface = Surface(RESOLUTION_NINTENDO_DS)
                tempShaftSurface.set_colorkey((0,0,0))
                tempShaftSurface.set_alpha(round(lineFader.getStrength() * 255))
                line(tempShaftSurface, self.overlayColour, tileToScreenPos(self.lightLines[indexLine].posCornerStart),
                        tileToScreenPos(self.lightLines[indexLine].posCornerEnd), width=4)
                self.overlayTransparentLightShaftSurface.blit(tempShaftSurface, (0,0))
        
        return super().updatePuzzleElements(gameClockDelta)

    def removeElement(self, pos):
        for indexLine in self.tileToLightLines[pos]:
            self.lightLinesFader[indexLine].setActiveState(False)
        self.tilesPopulated.pop(self.tilesPopulated.index(pos))

    def _doReset(self):
        for fader in self.lightLinesFader:
            fader.reset()
            fader.setActiveState(False)
        self.tileToLightLines = {}
        self.tilesPopulated = []
        self.generateOverlaySurface()
        self.overlayTransparentLightShaftSurface.fill((0,0,0,0))

    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.Lamp_SetInfo.value:
            self.overlayColour = (operands[1].value << 3, operands[2].value << 3, operands[3].value << 3)
            self.movesMinimum = operands[0].value
        elif opcode == OPCODES_LT2.Lamp_AddLine.value:
            self.lightLines.append(RoseWall((operands[0].value, operands[1].value), (operands[2].value, operands[3].value)))
            self.lightLinesFader.append(Fader(2000, initialActiveState=False, invertOutput=True))
        elif opcode == OPCODES_LT2.Lamp_AddDisable.value:
            for avoidX in range(operands[2].value):
                for avoidY in range(operands[3].value):
                    self.tilesUnavailable.append((operands[0].value + avoidX, operands[1].value + avoidY))
        else:
            return super()._doUnpackedCommand(opcode, operands)
        return True
    
    def handleTouchEventPuzzleElements(self, event):
        if event.type == MOUSEBUTTONDOWN:
            if event.pos[0] >= self.posCorner[0] and event.pos[1] >= self.posCorner[1] + RESOLUTION_NINTENDO_DS[1]:
                if (event.pos[0] < self.posCorner[0] + self.tileDimensions[0] * self.tileBoardDimensions[0] and
                    event.pos[1] < self.posCorner[1] + RESOLUTION_NINTENDO_DS[1] + self.tileDimensions[1] * self.tileBoardDimensions[1]):   # Clicked on grid
                    deltaTilesX = (event.pos[0] - self.posCorner[0]) // self.tileDimensions[0]
                    deltaTilesY = (event.pos[1] - RESOLUTION_NINTENDO_DS[1] - self.posCorner[1]) // self.tileDimensions[1]
                    tempPos = (deltaTilesX, deltaTilesY)
                    if self.isSpaceAvailable(tempPos):
                        self.behaviourWhenSpacePressed(tempPos)
                        return True
        return super().handleTouchEventPuzzleElements(event)