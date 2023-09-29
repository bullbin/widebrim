from pygame import Surface, BLEND_RGB_MULT
from ...const import RESOLUTION_NINTENDO_DS
from ...string import getSubstitutedString

from ...convenience import initDisplay

initDisplay()

class StaticTextHelper():
    def __init__(self, font, yBias = 4):
        self._font = font
        self._yBias = font.dimensions[1] + yBias
        self._xMax = font.dimensions[0]

        self._outputLineSurfaces = []
        self._outputLineSurfaceTrueWidths = []
        self._workingLineSurfaceIndex = 0
        self._workingLineXOffset = 0

        self._pos = (0,0)
        self._color = (0,0,0)
        self._tintSurface = Surface(font.dimensions)

        self._text = ""
        self._offsetText = 0

    def setPos(self, pos):
        self._pos = pos

    def setColor(self, triplet):
        self._color = triplet
        self._tintSurface.fill(triplet)

    def setText(self, text, substitute=True):
        # Clear current stored text
        self._outputLineSurfaces = []
        self._outputLineSurfaceTrueWidths = []
        self._workingLineSurfaceIndex = 0
        self._workingLineXOffset = 0
        self._offsetText = 0

        # TODO - Should unify this
        if substitute:
            self._text = getSubstitutedString(text)
        else:
            self._text = text

        lineWidths = []
        # Only account for line breaks
        for indexLine, line in enumerate(self._text.split("\n")):
            while len(lineWidths) <= indexLine:
                lineWidths.append(0)
            lineWidths[indexLine] = len(line)
        
        # Finally create the blank buffer surfaces for text to be written to
        for indexLine, width in enumerate(lineWidths):
            self._outputLineSurfaces.append(Surface((int(self._font.dimensions[0] * width), int(self._font.dimensions[1]))).convert_alpha())
            self._outputLineSurfaces[indexLine].fill((0,0,0,0))
            self._outputLineSurfaceTrueWidths.append(0)
        
        drawStatus = self._updateTextChar()
        while drawStatus:
            drawStatus = self._updateTextChar()

    def _getNextChar(self):
        # If no character is available, None is returned
        if self._offsetText >= len(self._text):
            return None
        else:
            self._offsetText += 1
            return self._text[self._offsetText - 1]

    def _addCharacterToDrawBuffer(self, character):
        if character in self._font.glyphMap:
            glyph = self._font.glyphMap[character]
            self._outputLineSurfaces[self._workingLineSurfaceIndex].blit(glyph.image, (self._workingLineXOffset, 0))
            self._outputLineSurfaces[self._workingLineSurfaceIndex].blit(self._tintSurface, (self._workingLineXOffset, 0), special_flags=BLEND_RGB_MULT)
            self._workingLineXOffset += glyph.getWidth()

    def _updateTextChar(self):
        # Returns True if the character contributed graphically
        nextChar = self._getNextChar()
        while nextChar != None:
            if nextChar == "\n":
                self._outputLineSurfaceTrueWidths[self._workingLineSurfaceIndex] = self._workingLineXOffset
                self._workingLineSurfaceIndex += 1
                self._workingLineXOffset = 0
            else:
                self._addCharacterToDrawBuffer(nextChar)
            return True

        self._outputLineSurfaceTrueWidths[self._workingLineSurfaceIndex] = self._workingLineXOffset
        return False

    def draw(self, gameDisplay):
        yBias = self._pos[1]
        for buffer in self._outputLineSurfaces[0:self._workingLineSurfaceIndex + 1]:
            gameDisplay.blit(buffer, (self._pos[0], yBias))
            yBias += self._yBias
    
    def drawXCentered(self, gameDisplay):
        yBias = self._pos[1]
        for indexBuffer, buffer in enumerate(self._outputLineSurfaces[0:self._workingLineSurfaceIndex + 1]):
            gameDisplay.blit(buffer, ((RESOLUTION_NINTENDO_DS[0] - self._outputLineSurfaceTrueWidths[indexBuffer]) // 2, yBias))
            yBias += self._yBias
    
    def drawXYCenterPoint(self, gameDisplay):
        countLines = len(self._outputLineSurfaces[0:self._workingLineSurfaceIndex + 1])
        yActualLength = self._yBias * countLines
        if countLines % 2 != 0:
            yActualLength -= (self._yBias - self._font.dimensions[1])

        # I don't understand why the bias is re-added to the end, but its required to get the correct placement
        yBias = (self._pos[1] - (yActualLength // 2)) + (self._yBias - self._font.dimensions[1])
        
        for indexBuffer, buffer in enumerate(self._outputLineSurfaces[0:self._workingLineSurfaceIndex + 1]):
            gameDisplay.blit(buffer, ((self._pos[0] - (self._outputLineSurfaceTrueWidths[indexBuffer] // 2)), yBias))
            yBias += self._yBias
    
    # Movie uses a biasless variant. TODO - More research required
    def drawXYCenterPointNoBias(self, gameDisplay):
        countLines = len(self._outputLineSurfaces[0:self._workingLineSurfaceIndex + 1])
        yActualLength = self._yBias * countLines
        if countLines % 2 != 0:
            yActualLength -= (self._yBias - self._font.dimensions[1])

        yBias = (self._pos[1] - (yActualLength // 2))
        
        for indexBuffer, buffer in enumerate(self._outputLineSurfaces[0:self._workingLineSurfaceIndex + 1]):
            gameDisplay.blit(buffer, ((self._pos[0] - (self._outputLineSurfaceTrueWidths[indexBuffer] // 2)), yBias))
            yBias += self._yBias