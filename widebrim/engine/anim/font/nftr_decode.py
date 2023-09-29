from widebrim.madhatter.common import logSevere
from ....madhatter.hat_io.binary import BinaryReader
from ....engine.convenience import initDisplay

from pygame import Surface
initDisplay()

# TODO - Restructure to load CWDH first

CHAR_BIAS = 1

class Glyph():
    def __init__(self, image):
        self.image = image
        self.char = None
        self.charDisableAddedOffset = False
    
    def getWidth(self):
        if self.charDisableAddedOffset:
            return self.image.get_width()
        return self.image.get_width() + CHAR_BIAS

    def applyCharacterWidth(self, start, width, length):
        output = Surface((length, self.image.get_height())).convert()
        output.set_colorkey((0,0,0))
        output.blit(self.image, (start,0))
        if width != 0:
            if start != 0 and width != start:
                self.charDisableAddedOffset = True
        self.image = output

    def setChar(self, char):
        self.char = char

class NftrTiles():

    ENCODING_MAP = {0:"utf-8",
                    1:"utf-16",
                    2:"shift-jis",
                    3:"cp1252"}

    def __init__(self, data):

        def loadGlyphs(data):
            reader = BinaryReader(data=data)
            reader.seek(8,1)
            filesize = reader.readU32()
            lengthHeader = reader.readU16()
            countBlocks = reader.readU16()

            # Read font info
            reader.seek(lengthHeader + 4)
            lengthFontInfo = reader.readU32()
            reader.seek(1,1)
            fontInfoHeight = reader.readUInt(1)
            reader.seek(3,1)
            fontInfoWidth = reader.readUInt(1)
            reader.seek(1,1)
            fontInfoDecodeMode = reader.readUInt(1)
            offsetPlgc = reader.readU32() - 8
            offsetHdwc = reader.readU32() - 8
            offsetPamc = reader.readU32() - 8

            # Read glyph data
            reader.seek(offsetPlgc + 4)
            lengthPlgc = reader.readU32()
            tileDimensions = (reader.readUInt(1), reader.readUInt(1))
            lengthTile = reader.readU16()
            reader.seek(2,1)
            
            depth = reader.readUInt(1)
            rotate = reader.readUInt(1)

            countTiles = (lengthPlgc - 16) // lengthTile
            countPixels = tileDimensions[0] * tileDimensions[1]

            for indexTile in range(countTiles):
                tile = Surface(tileDimensions).convert()

                indexPixel = 0
                for indexData in range(lengthTile):
                    data = reader.readUInt(1)
                    for indexBit in range(8):
                        bitEnabled = (data & (2 ** (7 - indexBit))) != 0
                        if indexPixel < countPixels:
                            strength = int(bitEnabled * 255)
                            tile.set_at((indexPixel % tileDimensions[0], indexPixel // tileDimensions[0]), (strength, strength, strength))
                        indexPixel += 1
                
                self.glyphs.append(Glyph(tile))
            
            self.dimensions = tileDimensions

            # Read character width data
            reader.seek(offsetHdwc + 8)
            charFirstIndex = reader.readU16()
            charLastIndex = reader.readU16()
            reader.seek(4,1)
            for indexGlpyh in range(charFirstIndex, charLastIndex + 1):
                self.glyphs[indexGlpyh].applyCharacterWidth(reader.readInt(1), reader.readUInt(1), reader.readUInt(1))
            
            # Read character map
            offsetNextPamc = offsetPamc
            while offsetNextPamc != 0:
                reader.seek(offsetNextPamc + 4)
                lengthPamc = reader.readU32()
                codeFirstIndex = reader.readU16()
                codeLastIndex = reader.readU16()
                typePamc = reader.readU32()
                offsetNextPamc = reader.readU32()
                if offsetNextPamc != 0:
                    offsetNextPamc -= 8

                if typePamc == 0:
                    indexGlpyh = reader.readU16()
                    for codeIndex in range(codeFirstIndex, codeLastIndex + 1):
                        self.glyphs[indexGlpyh].setChar((codeIndex.to_bytes(2, byteorder = 'big')).decode(NftrTiles.ENCODING_MAP[fontInfoDecodeMode]))
                        indexGlpyh += 1

                elif typePamc == 1:
                    for codeIndex in range(codeFirstIndex, codeLastIndex + 1):
                        indexGlpyh = reader.readS16()
                        if indexGlpyh != -1:
                            self.glyphs[indexGlpyh].setChar((codeIndex.to_bytes(2, byteorder = 'big')).decode(NftrTiles.ENCODING_MAP[fontInfoDecodeMode]))
                
                elif typePamc == 2:
                    countDefinitions = reader.readU16()
                    for indexDefinition in range(countDefinitions):
                        charGlyph = (reader.read(2)).decode(NftrTiles.ENCODING_MAP[fontInfoDecodeMode])
                        self.glyphs[reader.readU16()].setChar(charGlyph)
        
        def buildGlyphMap():
            # Workaround, string codecs are annoying
            for glyph in self.glyphs:
                strippedString = glyph.char.replace("\x00", "")
                self.glyphMap[strippedString.encode('utf-8').decode('utf-8')] = glyph

        self.dimensions = (0,0)
        self.glyphs = []
        self.glyphMap = {}
        
        try:
            if data != None and type(data) == bytearray:
                loadGlyphs(data)
        except:
            logSevere("NTFR decoding error!", name="NtfrTiles")
        
        buildGlyphMap()
