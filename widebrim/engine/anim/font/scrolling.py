from typing import Callable, List, Optional, Tuple
from widebrim.engine.string.cmp import strCmp
from pygame import Surface, BLEND_RGB_MULT

from widebrim.madhatter.common import logSevere
from ...const import RESOLUTION_NINTENDO_DS, TIME_FRAMECOUNT_TO_MILLISECONDS
from .const import BLEND_MAP
from ...string import getSubstitutedString

from ...convenience import initDisplay

initDisplay()

class ScrollingFontHelper():
    def __init__(self, font, yBias = 4, durationPerCharacter=TIME_FRAMECOUNT_TO_MILLISECONDS):
        self._font = font
        self._yBias = font.dimensions[1] + yBias
        self._xMax = font.dimensions[0]

        self._outputLineSurfaces = []
        self._workingLineSurfaceIndex = 0
        self._workingLineXOffset = 0

        self._pos = (0,0)
        self._color = (0,0,0)
        self._tintSurface = Surface(font.dimensions)

        self._text = ""
        self._offsetText = 0
        self._hasCharsRemaining = False

        self._durationPerChar = TIME_FRAMECOUNT_TO_MILLISECONDS
        self._durationCarried = 0
        self._durationWaiting = 0

        self.setDurationPerCharacter(durationPerCharacter)
        self._isWaitingForTap = False

        self._funcModifyVoice : Optional[Callable[[int], None]]         = None
        self._funcSetAnimation : Optional[Callable[[int, str], None]]   = None
    
    def setFunctionModifyVoice(self, funcModifyVoice : Optional[Callable[[int], None]]):
        self._funcModifyVoice = funcModifyVoice
    
    def setFunctionSetAnimation(self, funcSetAnimation : Optional[Callable[[int, str], None]]):
        self._funcSetAnimation = funcSetAnimation

    def setDurationPerCharacter(self, duration : float):
        if self._durationPerChar >= 0:
            self._durationPerChar = duration

    def setPos(self, pos):
        self._pos = pos

    def setColor(self, triplet):
        self._color = triplet
        self._tintSurface.fill(triplet)

    def _reset(self):
        self._outputLineSurfaces = []
        self._workingLineSurfaceIndex = 0
        self._workingLineXOffset = 0
        self._offsetText = 0
        self._hasCharsRemaining = False
        self._durationCarried = 0
        self._durationWaiting = 0
        self._isWaitingForTap = False

    def setText(self, text, substitute=True):
        # Clear current stored text
        self._reset()
        if substitute:
            self._text = getSubstitutedString(text)
        else:
            self._text = text
        self._hasCharsRemaining = True

        lineWidths = []

        # Remove any sequences to do with changing anims, etc
        removedControlledCharString = []
        for indexLine, line in enumerate(self._text.split("&")):
            if not(indexLine % 2):
                removedControlledCharString.append(line)
        removedControlledCharString = ''.join(removedControlledCharString)

        # Account for control characters, line breaks and text clearing to calculate the maximum length of each line
        for clearParagraph in removedControlledCharString.split("@c"):
            indexLine = 0
            for line in clearParagraph.split("@B"):
                for subLine in line.split("\n"):
                    controlChars = subLine.count("@") + subLine.count("#")
                    if len(lineWidths) > indexLine:
                        lineWidths[indexLine] = max(lineWidths[indexLine], len(subLine) - (controlChars * 2))
                    else:
                        lineWidths.append(len(subLine) - (controlChars * 2))
                    indexLine += 1
            
        # Finally create the blank buffer surfaces for text to be written to
        for indexLine, width in enumerate(lineWidths):
            self._outputLineSurfaces.append(Surface((int(self._font.dimensions[0] * width), int(self._font.dimensions[1]))).convert_alpha())
            self._outputLineSurfaces[indexLine].fill((0,0,0,0))

    def _getNextChar(self):
        # Returns next character (control included) from input string
        # If no character is available, None is returned
        # Control characters are given in full, including their identifiers.

        if self._offsetText >= len(self._text):
            self._hasCharsRemaining = False
            return None
        else:
            # TODO - Check error hasn't occured
            if self._text[self._offsetText] == "@":
                commandSize = 2
                if self._text[self._offsetText + 1] == "v" or self._text[self._offsetText + 1] == "V":
                    commandSize = 3
                self._offsetText += commandSize
                return self._text[self._offsetText - commandSize:self._offsetText]
            if self._text[self._offsetText] == "#":
                self._offsetText += 2
                return self._text[self._offsetText - 2:self._offsetText]
            elif self._text[self._offsetText] == "&":
                output = "&"
                while self._text[self._offsetText + 1] != "&":
                    output += self._text[self._offsetText + 1]
                    self._offsetText += 1
                self._offsetText += 2
                return output + "&"
            else:
                self._offsetText += 1
                return self._text[self._offsetText - 1]

    def _addCharacterToDrawBuffer(self, character):
        if character in self._font.glyphMap:
            glyph = self._font.glyphMap[character]
            self._outputLineSurfaces[self._workingLineSurfaceIndex].blit(glyph.image, (self._workingLineXOffset, 0))
            self._outputLineSurfaces[self._workingLineSurfaceIndex].blit(self._tintSurface, (self._workingLineXOffset, 0), special_flags=BLEND_RGB_MULT)
            self._workingLineXOffset += glyph.getWidth()

    def _clearBufferAndResetLineCounter(self):
        for buffer in self._outputLineSurfaces:
            buffer.fill((0,0,0,0))
        self._workingLineSurfaceIndex = 0
        self._workingLineXOffset = 0

    def _updateTextChar(self):

        def getNextCommandPacket(command : str) -> Tuple[str, str]:

            def isCharInvalid(char : str):
                return char == '\x20' or char == '\x09' or char == '\x0a' or char == '\x0d' or char == '\x00'

            outParam = ""
            segment = ""
            idxStartChar = 0
            while idxStartChar < len(command):
                if isCharInvalid(command[idxStartChar]):
                    idxStartChar += 1
                else:
                    break
            if idxStartChar != len(command):
                # Found segment
                while idxStartChar < len(command):
                    if isCharInvalid(command[idxStartChar]):
                        break
                    else:
                        if command[idxStartChar] == "_":
                            segment += " "
                        else:
                            segment += command[idxStartChar]
                        idxStartChar += 1
                outParam = command[idxStartChar:]
            return (segment, outParam)

        # Returns True if the character contributed graphically
        nextChar = self._getNextChar()
        while nextChar != None and self._hasCharsRemaining and not(self.isWaiting()):
            # Newline character added for puzzles - cannot be used in events
            if nextChar == "\n":
                self._workingLineSurfaceIndex += 1
                self._workingLineXOffset = 0
            elif len(nextChar) == 1:
                self._addCharacterToDrawBuffer(nextChar)
                return True 
            else:
                if nextChar[0] == "@":
                    # Control character
                    # TODO - s,S
                    if nextChar[1] == "p" or nextChar[1] == "P":    # Wait until touch
                        self._isWaitingForTap = True

                    elif nextChar[1] == "w" or nextChar[1] == "W":  # Wait during text
                        self._durationCarried -= 500

                    elif nextChar[1] == "c" or nextChar[1] == "C":  # Clear the screen
                        self._clearBufferAndResetLineCounter()

                    elif nextChar[1] == "B":                        # Line break
                        self._workingLineSurfaceIndex += 1
                        self._workingLineXOffset = 0
                    
                    elif nextChar[1] == "v" or nextChar[1] == "V":  # Set voice effect
                        try:
                            if self._funcModifyVoice != None:
                                self._funcModifyVoice(int(nextChar[2]))
                        except Exception as e:
                            logSevere("Pitch modification failed!\n", e, name="ScrollRend")
                
                elif nextChar[0] == "#":
                    # Color character
                    if nextChar[1] in BLEND_MAP:
                        self.setColor(BLEND_MAP[nextChar[1]])

                else:
                    # HACK - Works around some length limits that could cause crashes. SetAni has a hard limit of 256 for string total, and the animation must be under 32 chars.
                    commandString = nextChar[1:-1]
                    commandName, commandString = getNextCommandPacket(commandString)
                    idChar, commandString = getNextCommandPacket(commandString)
                    nameAnim, commandString = getNextCommandPacket(commandString)
                    if strCmp(commandName, "SetAni"):
                        if idChar.isdigit():
                            idChar = int(idChar)
                        else:
                            idChar = 0
                        try:
                            if self._funcSetAnimation != None:
                                self._funcSetAnimation(idChar, nameAnim)
                        except Exception as e:
                            logSevere("Set animation failed!\n", e, name="ScrollRend")

            return False

    def isWaiting(self):
        return self._isWaitingForTap
    
    def setTap(self):
        self._isWaitingForTap = False
    
    def getActiveState(self):
        return self._hasCharsRemaining
    
    def skip(self):
        while self._hasCharsRemaining and not(self.isWaiting()):
            self._updateTextChar()

    def update(self, gameClockDelta):
        if self._hasCharsRemaining and not(self.isWaiting()):
            self._durationCarried += gameClockDelta
            while self._durationCarried >= self._durationPerChar and self._hasCharsRemaining and not(self.isWaiting()):
                if self._updateTextChar():
                    self._durationCarried -= self._durationPerChar

    def draw(self, gameDisplay):
        yBias = self._pos[1]
        for buffer in self._outputLineSurfaces[0:self._workingLineSurfaceIndex + 1]:
            gameDisplay.blit(buffer, (self._pos[0], yBias))
            yBias += self._yBias
    
    def drawCentered(self, gameDisplay):
        # Bugfix - Will not draw centered as width is not aligned with buffer. Fixed in static, see to check tracking actual width
        yBias = self._pos[1]
        for buffer in self._outputLineSurfaces[0:self._workingLineSurfaceIndex + 1]:
            gameDisplay.blit(buffer, ((RESOLUTION_NINTENDO_DS[0] - buffer.get_width()) // 2, yBias))
            yBias += self._yBias