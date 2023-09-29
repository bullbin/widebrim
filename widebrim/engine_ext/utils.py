from __future__ import annotations
from typing import Callable, Optional, TYPE_CHECKING, Tuple, Union

from widebrim.madhatter.common import logSevere
from widebrim.madhatter.hat_io.asset import LaytonPack
from widebrim.madhatter.hat_io.const import ENCODING_DEFAULT_STRING
if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from PIL.Image import Image as ImageType

from widebrim.engine.anim.button import AnimatedButton, AnimatedClickableButton, StaticButton
from ..madhatter.hat_io.asset_image import StaticImage
from ..engine.const import PATH_BG_ROOT, PATH_ANI, PATH_FACE_ROOT, RESOLUTION_NINTENDO_DS
from ..madhatter.hat_io.asset_image import AnimatedImage
from ..engine.anim.image_anim import AnimatedImageObject, AnimatedImageObjectWithSubAnimation
from ..engine.const import PATH_PACK_TXT2, PATH_PACK_TXT
from .const import PATH_TEMP

from os import makedirs
from shutil import rmtree

from pygame import image, Surface

def substituteLanguageString(laytonState : Layton2GameState, string : str) -> str:
    """Get substituted strings for a given path. Will substitute language if there is one missing string or a "?" symbol.

    Args:
        laytonState (Layton2GameState): Game state used for language substitution
        string (str): Any path

    Returns:
        str: Path with language substituted or original if substitution not possible
    """
    if "?" in string:
        string = string.replace("?", laytonState.language.value)
    elif string.count("%s") == 1:
        string = string.replace("%s", laytonState.language.value)
    return string

def getFormatString(path : str, extension : str) -> str:
    if len(path) >= len(extension):
        return path[0:- len(extension)] + extension
    return path

def doesAnimExist(laytonState : Layton2GameState, pathAnim : str) -> bool:
    """Check for presence of file with anim extension in animation folder. Will substitute language if there is one missing string or a "?" symbol. Does not guarentee file is of anim type or can be read.

    Args:
        laytonState (Layton2GameState): Game state used for language substitution
        pathAnim (str): Path to animation. Extension included but root anim path excluded

    Returns:
        bool: True if file exists, may not be anim
    """
    if ".spr" in pathAnim:
        pathAnim = getFormatString(pathAnim, "arc")
    elif ".sbj" in pathAnim:
        pathAnim = getFormatString(pathAnim, "arj")
    else: # yes this will maybe cause bugs but the game really doesn't care about last 3 digits
        pathAnim = getFormatString(pathAnim, "arc")
    
    return laytonState.getFileAccessor().doesFileExist(substituteLanguageString(laytonState, PATH_ANI % pathAnim))

def doesImageExist(laytonState : Layton2GameState, pathBg : str) -> bool:
    """Check for presence of file with image extension in background folder. Will substitute language if there is one missing string or a "?" symbol. Does not guarentee file is of image type or can be read.

    Args:
        laytonState (Layton2GameState): Game state used for language substitution
        pathBg (str): Path to background. Extension included but root background path excluded

    Returns:
        bool: True if file exists, may not be image
    """
    return laytonState.getFileAccessor().doesFileExist(substituteLanguageString(laytonState, PATH_BG_ROOT % getFormatString(pathBg, "arc")))

def getImageFromPath(laytonState : Layton2GameState, pathBg : str) -> Optional[Surface]:
    """Get Surface representing some background image at the given path. Will substitute language if there is one missing string or a "?" symbol.

    Args:
        laytonState (Layton2GameState): Game state used for language substitution
        pathBg (str): Path to background. Extension included but root background path excluded

    Returns:
        Optional[Surface]: Surface if image was readable, else None
    """
    def fetchBgxImage(path) -> Optional[ImageType]:
        # TODO - Fix unwanted behaviour with reading null-terminated strings, where a null character is left at the end
        imageFile = laytonState.getFileAccessor().getData(PATH_BG_ROOT % substituteLanguageString(laytonState, getFormatString(path, "arc")))
        if imageFile != None:
            try:
                imageFile = StaticImage.fromBytesArc(imageFile)
                return imageFile.getImage(0)
            except:
                return None
        return imageFile

    if (bg := fetchBgxImage(pathBg)) != None:
        # HACK - Reword transparencies to support colormasking
        output = image.fromstring(bg.convert("RGB").tobytes("raw", "RGB"), bg.size, "RGB").convert()
        if bg.mode == "P":
            output.set_colorkey(bg.getpalette()[0:3])
        return output

def getTxtString(laytonState, nameString, reportFailure=False) -> Optional[str]:
    output = laytonState.getFileAccessor().getPackedString(PATH_PACK_TXT % laytonState.language.value, nameString)
    if output == None:
        if reportFailure:
            return None
        else:
            return ""
    return output

def getTxt2String(laytonState, nameString, reportFailure=False) -> Optional[str]:
    output = laytonState.getFileAccessor().getPackedString(PATH_PACK_TXT2 % laytonState.language.value, nameString)
    if output == None:
        if reportFailure:
            return None
        else:
            return ""
    return output

def getButtonFromPath(laytonState : Layton2GameState, inPath : str, callback : Optional[Callable] = None, animOff : str="off", animOn : str="on", pos=(0,0), customDimensions=None, namePosVariable="pos") -> Optional[AnimatedButton]:
    """Returns an image-based button from path. Note that by default, this button will be offset onto the bottom screen already. Language strings will be substituted where possible.

    Args:
        laytonState (Layton2GameState): Game state
        inPath (str): Path to image asset, relative from master animation path
        callback (Optional[Callable], optional): Callback when button is pressed. Defaults to None.
        animOff (str, optional): Name of animation when button is idle. Defaults to "off".
        animOn (str, optional): Name of animation when button is targetted. Defaults to "on".
        pos (tuple, optional): Position. Defaults to (0,0) and overriden by variable.
        customDimensions (tuple, optional): Size of interactable area. Defaults to None, which means the maximum dimensions of the animation is used.
        namePosVariable ([type], optional): Name of variable storing position. Defaults to "pos".

    Returns:
        AnimatedButton: Image-based button
    """

    anim = getBottomScreenAnimFromPath(laytonState, inPath, pos=pos, namePosVar=namePosVariable)
    if customDimensions != None:
        anim.setDimensions(customDimensions)
    return AnimatedButton(anim, animOn, animOff, callback=callback)

def getStaticButtonFromAnim(anim : Optional[AnimatedImage], spawnAnimName : str, callback : Optional[Callable] = None, pos=(0,0), namePosVariable=None, clickOffset=(0,0)) -> Optional[StaticButton]:
    if anim != None:
        anim : AnimatedImageObject
        anim.setPos((pos[0], pos[1] + RESOLUTION_NINTENDO_DS[1]))
        if namePosVariable == None:
            namePosVariable = "pos"

        if anim.getVariable(namePosVariable) != None:
            anim.setPos((anim.getVariable(namePosVariable)[0],
                         anim.getVariable(namePosVariable)[1] + RESOLUTION_NINTENDO_DS[1]))
        
        if anim.setAnimationFromName(spawnAnimName):
            return StaticButton(anim.getPos(), anim.getActiveFrame(), callback=callback, targettedOffset=clickOffset)
    return None

def getStaticButtonFromPath(laytonState : Layton2GameState, inPath : str, spawnAnimName : str, callback : Optional[Callable] = None, pos=(0,0), namePosVariable=None, clickOffset=(0,0)) -> Optional[StaticButton]:
    """Returns a surface-based button from path. Note that by default, this button will be offset onto the bottom screen already.

    Args:
        laytonState (Layton2GameState): Game state
        inPath (str): Path to image asset, relative from master animation path
        spawnAnimName (str): Name of animation
        callback (Optional[Callable], optional): Callback when button is pressed. Defaults to None.
        pos (tuple, optional): Position. Defaults to (0,0) and overriden by variable.
        namePosVariable ([type], optional): Name of variable storing position. Defaults to None, 'pos' will be used instead.
        clickOffset (tuple, optional): Position offset when button is targetted. Defaults to (0,0).

    Returns:
        Optional[StaticButton]: Surface-based button
    """

    # TODO - Replace calls to static button to this constructor instead
    if (button := getButtonFromPath(laytonState, inPath, callback=callback, animOff=spawnAnimName, animOn=spawnAnimName, pos=pos, namePosVariable=namePosVariable)) != None:
        if button.image.getActiveFrame() != None:
            return StaticButton(button.image.getPos(), button.image.getActiveFrame(), callback=callback, targettedOffset=clickOffset)
    return None

def getClickableButtonFromPath(laytonState : Layton2GameState, inPath : str, callback : Optional[Callable], animOff : str = "off", animOn : str = "on", animClick : str = "click", pos=(0,0), customDimensions=None, namePosVariable="pos", unclickOnCallback=True) -> Optional[AnimatedClickableButton]:
    button = getButtonFromPath(laytonState, inPath, callback, animOff, animOn, pos, customDimensions, namePosVariable)
    if button != None:
        button = button.asClickable(animClick, unclickOnCallback)
    return button

def _getAnimFromPath(laytonState : Layton2GameState, inPath : str, spawnAnimIndex : Optional[int] = 1, spawnAnimName : Optional[str] = None, pos : Tuple[int,int] = (0,0), namePosVar : str = "pos", enableSubAnimation : bool = False, doOffset : bool = False):

    if doOffset:
        extension = "arc"
    else:
        extension = "arj"

    def functionGetAnimationFromName(name):
        name = name.split(".")[0] + "." + extension
        resolvedPath = PATH_FACE_ROOT % name
        return laytonState.getFileAccessor().getData(resolvedPath)

    inPath = substituteLanguageString(laytonState, getFormatString(inPath, extension))

    if (tempAsset := laytonState.getFileAccessor().getData(PATH_ANI % inPath)) != None:
        try:
            if doOffset:
                tempImage = AnimatedImage.fromBytesArc(tempAsset, functionGetFileByName=functionGetAnimationFromName)
            else:
                tempImage = AnimatedImage.fromBytesArj(tempAsset, functionGetFileByName=functionGetAnimationFromName)
        except:
            logSevere("Failed to parse image at", inPath, name="UtilAnimDec")
            return AnimatedImageObject()

        if enableSubAnimation:
            tempImage = AnimatedImageObjectWithSubAnimation.fromMadhatter(tempImage)
        else:
            tempImage = AnimatedImageObject.fromMadhatter(tempImage)
        
        if pos == (0,0) and namePosVar != None:
            if (posData := tempImage.getVariable(namePosVar)) != None:
                tempImage.setPos((posData[0], posData[1]))
        else:
            tempImage.setPos(pos)
        
        if doOffset:
            tempImage.setPos(offsetVectorToSecondScreen(tempImage.getPos()))

        if spawnAnimName != None:
            tempImage.setAnimationFromName(spawnAnimName)
        elif spawnAnimIndex != None:
            tempImage.setAnimationFromIndex(spawnAnimIndex)
        
        return tempImage
    
    logSevere("Could not fetch image for", inPath, name="UtilAnimMiss")
    return AnimatedImageObject()

def decodeStringFromPack(pack : LaytonPack, filename : str) -> str:
    """Decodes a packed string.

    Args:
        pack (LaytonPack): Pack containing encoded strings.
        filename (str): Filename for string inside pack. Should not include pack path.

    Returns:
        str: Decoded string. May be empty if file was empty, failed to decode or doesn't exist.
    """
    if (data := pack.getFile(filename)) != None:
        try:
            return data.decode(ENCODING_DEFAULT_STRING)
        except UnicodeDecodeError:
            pass
    return ""

# Accurate behaviour for game assets - divided into bottom and top screen (ARC and ARJ) and follow the given rules. If an animation is not found a void one is returned instead
def getBottomScreenAnimFromPath(laytonState : Layton2GameState, inPath : str, spawnAnimIndex : Optional[int] = 1, spawnAnimName : Optional[str] = None, pos : Tuple[int,int] = (0,0), namePosVar : str = "pos", enableSubAnimation : bool = False) -> Optional[Union[AnimatedImageObject, AnimatedImageObjectWithSubAnimation]]:
    """Gets animation located in the given path. Where possible, language substitution and format correction will be applied to the string. Animations returned are aligned to the bottom screen.

    Args:
        laytonState (Layton2GameState): Game state used for language substitution.
        inPath (str): Path relative to animation root leading to animation. Should include 3-digit some extension, by default arc or spr.
        spawnAnimIndex (Optional[int], optional): Index to set animation on spawn. Set to None to ignore this feature. Defaults to 1.
        spawnAnimName (Optional[str], optional): Name to set animation on spawn. Set to None to ignore this feature. Defaults to None.
        pos (Tuple[int,int], optional): Initial position for drawing. Offset onto bottom screen by default. Set to (0,0) to fallback to stored variable position. Defaults to (0,0).
        namePosVar (str, optional): Variable name used for automatic positioning. Ignored if position is specified. Defaults to "pos".
        enableSubAnimation (bool, optional): Allows the animation to load an additional animation. Rarely used. Defaults to False.

    Returns:
        Union[AnimatedImageObject, AnimatedImageObjectWithSubAnimation]: Animation object. Empty animation if no animation could be loaded at the given path.
    """

    return _getAnimFromPath(laytonState, inPath, spawnAnimIndex, spawnAnimName, pos, namePosVar, enableSubAnimation, doOffset = True)

# Accurate behaviour for game assets - divided into bottom and top screen (ARC and ARJ) and follow the given rules. If an animation is not found a void one is returned instead
def getTopScreenAnimFromPath(laytonState : Layton2GameState, inPath : str, spawnAnimIndex : Optional[int] = 1, spawnAnimName : Optional[str] = None, pos : Tuple[int,int] = (0,0), namePosVar : str = "pos", enableSubAnimation : bool = False) -> Optional[Union[AnimatedImageObject, AnimatedImageObjectWithSubAnimation]]:
    """Gets animation located in the given path. Where possible, language substitution and format correction will be applied to the string. Animations returned are aligned to the bottom screen.

    Args:
        laytonState (Layton2GameState): Game state used for language substitution.
        inPath (str): Path relative to animation root leading to animation. Should include 3-digit some extension, by default arc or spr.
        spawnAnimIndex (Optional[int], optional): Index to set animation on spawn. Set to None to ignore this feature. Defaults to 1.
        spawnAnimName (Optional[str], optional): Name to set animation on spawn. Set to None to ignore this feature. Defaults to None.
        pos (Tuple[int,int], optional): Initial position for drawing. Offset onto bottom screen by default. Set to (0,0) to fallback to stored variable position. Defaults to (0,0).
        namePosVar (str, optional): Variable name used for automatic positioning. Ignored if position is specified. Defaults to "pos".
        enableSubAnimation (bool, optional): Allows the animation to load an additional animation. Rarely used. Defaults to False.

    Returns:
        Union[AnimatedImageObject, AnimatedImageObjectWithSubAnimation]: Animation object. Empty animation if no animation could be loaded at the given path.
    """
    # TODO - Subanimation?
    return _getAnimFromPath(laytonState, inPath, spawnAnimIndex, spawnAnimName, pos, namePosVar, enableSubAnimation, doOffset = False)

# TODO - Remove this HACK (and use it wherever possible)
def offsetVectorToSecondScreen(inPos : Tuple[int,int]):
    return (inPos[0], inPos[1] + RESOLUTION_NINTENDO_DS[1])

def ensureTempFolder():
    try:
        makedirs(PATH_TEMP, exist_ok=True)
    except OSError:
        return False
    return True

def cleanTempFolder():
    try:
        rmtree(PATH_TEMP)
    except:
        return False
    return True