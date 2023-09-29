from pygame import Surface
from ...string import getSubstitutedString

def generateImageFromString(font, inString):

    chars = []

    for letter in getSubstitutedString(inString):
        if letter in font.glyphMap:
            chars.append(font.glyphMap[letter])
            
    dimensions = (0,0)
    for glyph in chars:
        dimensions = (dimensions[0] + glyph.getWidth(), max(dimensions[1], glyph.image.get_height()))
    
    output = Surface(dimensions).convert()
    output.set_colorkey((0,0,0))
    xOffset = 0
    for glyph in chars:
        output.blit(glyph.image, (xOffset,0))
        xOffset += glyph.getWidth()

    return output

def generateImageFromStringStrided(font, inString, stride):

    chars = []

    for letter in getSubstitutedString(inString):
        if letter in font.glyphMap:
            chars.append(font.glyphMap[letter])
            
    dimensions = (0,0)
    for glyph in chars:
        dimensions = (dimensions[0] + stride, max(dimensions[1], glyph.image.get_height()))
    
    if len(chars) > 0:
        dimensions = (max(dimensions[0], (dimensions[0] - stride) + chars[-1].getWidth()), dimensions[1])
    
    output = Surface(dimensions).convert()
    output.set_colorkey((0,0,0))
    xOffset = 0
    for glyph in chars:
        output.blit(glyph.image, (xOffset,0))
        xOffset += stride

    return output