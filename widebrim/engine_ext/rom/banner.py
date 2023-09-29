from ...engine.config import PATH_ROM
from ...madhatter.hat_io.binary import BinaryReader
from ...madhatter.hat_io.asset_image import colour, tiler
from ...engine.const import LANGUAGES

# Credit: GBATEK

TILE_RES = 8
TILE_PER_ROW = int(32/TILE_RES)
COUNT_TILES = int((32 / TILE_RES) ** 2)

def getBannerImageFromRom(rom):
    bannerReader = BinaryReader(data=rom.iconBanner)
    bannerReader.seek(0x0020)
    image = tiler.TiledImageHandler()
    for indexTile in range(COUNT_TILES):
        image.addTileFromReader(bannerReader, prolongDecoding=True, offset=((indexTile % TILE_PER_ROW) * TILE_RES, (indexTile // TILE_PER_ROW) * TILE_RES), overrideBpp=4)
    image.setPaletteFromList(colour.getPaletteAsListFromReader(bannerReader, 16))
    image.decodeProlongedTiles()
    return image.tilesToImage((32,32), useOffset=True)

def getNameStringFromRom(rom, language):
    bannerReader = BinaryReader(data=rom.iconBanner)
    version = bannerReader.readUInt(2)
    try:
        languageEnum = LANGUAGES(language)
        if languageEnum == LANGUAGES.Japanese:
            bannerReader.seek(0x240)
        elif languageEnum == LANGUAGES.English:
            bannerReader.seek(0x340)
        elif languageEnum == LANGUAGES.French:
            bannerReader.seek(0x440)
        elif languageEnum == LANGUAGES.German:
            bannerReader.seek(0x540)
        elif languageEnum == LANGUAGES.Italian:
            bannerReader.seek(0x640)
        elif languageEnum == LANGUAGES.Spanish:
            bannerReader.seek(0x740)
        elif languageEnum == LANGUAGES.Chinese:
            if version < 2:
                return ""
            bannerReader.seek(0x840)
        elif languageEnum == LANGUAGES.Korean:
            if version < 3:
                return ""
            bannerReader.seek(0x940)
        else:
            # Dutch not implemented?
            return ""
        return bannerReader.readPaddedString(0x100, "utf-16")
    except ValueError:
        return ""

def getCodenameFromRom(rom):
    name = rom.name.decode("ascii")
    if "\0" in name:
        return name.split("\0")[0]
    return name