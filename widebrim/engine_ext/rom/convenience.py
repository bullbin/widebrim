from .banner import getBannerImageFromRom, getCodenameFromRom, getNameStringFromRom
from ...engine.config import ROM_LOAD_BANNER
from ...engine.convenience import initDisplay
import pygame

def applyPygameBannerTweaks(fileInterface):

    def cleanupNameString(name : str):
        nameSplit = name.split("\n")
        if len(nameSplit) > 1:
            return " ".join(nameSplit[:-1])
        else:
            return getCodenameFromRom(fileInterface.getRom())

    if ROM_LOAD_BANNER and fileInterface.isRunningFromRom():

        initDisplay()

        bannerImage = getBannerImageFromRom(fileInterface.getRom())
        bannerSurface = pygame.image.fromstring(bannerImage.convert("RGB").tobytes("raw", "RGB"), bannerImage.size, "RGB").convert()
        try:
            transparency = bannerImage.getpalette()[:3]
            transparency = (transparency[0], transparency[1], transparency[2])
            bannerSurface.set_colorkey(transparency)
        except IndexError:
            pass

        pygame.display.set_icon(bannerSurface)
        nameString = ""
        if (language := fileInterface.getLanguage()) != None:
            nameString = getNameStringFromRom(fileInterface.getRom(), language)
        else:
            nameString = getCodenameFromRom(fileInterface.getRom())
        pygame.display.set_caption(cleanupNameString(nameString))
        return True
    return False