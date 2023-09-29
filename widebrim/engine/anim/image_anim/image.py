from __future__ import annotations

from typing import Dict, List, Optional, Tuple, TYPE_CHECKING, Union
from widebrim.engine.string.cmp import strCmp
from ....madhatter.hat_io.asset_image import Animation, getTransparentLaytonPaletted
from ...const import TIME_FRAMECOUNT_TO_MILLISECONDS
from ...convenience import initDisplay

if TYPE_CHECKING:
    from widebrim.madhatter.hat_io.asset_image.image import AnimatedImage


# TODO - Fix imports for only image
import pygame
initDisplay()

class AnimationSequence(Animation):
    def __init__(self):
        Animation.__init__(self)
        self.isLooping  = True
        self.isActive   = True
        # TODO - This can be carried into AnimatedImageObject to reduce overlap between anims
        self._indexFrame = 0
        self._elapsedFrame = 0
    
    def reset(self):
        self._indexFrame = 0
        self._elapsedFrame = 0
        self.isActive   = True
    
    def getActiveKeyframe(self) -> Optional[int]:
        if self.isActive and self._indexFrame < len(self.keyframes):
            return self.keyframes[self._indexFrame].indexFrame
        return None

    def updateCurrentFrame(self, gameClockDelta) -> bool:
        if self.isActive:
            self._elapsedFrame += gameClockDelta
            previousFrame = self._indexFrame
            while self._indexFrame < len(self.keyframes) and self.keyframes[self._indexFrame].duration <= self._elapsedFrame and self.isActive:
                nextFrameIndex = (self._indexFrame + 1) % len(self.keyframes)
                if nextFrameIndex < self._indexFrame and not(self.isLooping):
                    self.isActive = False
                else:
                    self._elapsedFrame -= self.keyframes[self._indexFrame].duration
                    self._indexFrame = nextFrameIndex
            return previousFrame != self._indexFrame
        return False

    @staticmethod
    def fromMadhatter(inAnim : Animation) -> AnimationSequence:
        output = AnimationSequence()
        output.name = inAnim.name
        output.keyframes = inAnim.keyframes
        for keyframe in output.keyframes:
            keyframe.duration *= TIME_FRAMECOUNT_TO_MILLISECONDS
        output.subAnimationIndex = inAnim.subAnimationIndex
        output.subAnimationOffset = inAnim.subAnimationOffset
        return output

class AnimatedImageObject():
    def __init__(self, workaroundEnableHiddenAnim=False):
        self._variables : Dict[str, List[int]]                      = {}
        self._frames : List[pygame.Surface]                         = []
        self._animations : Dict[str, AnimationSequence]             = {}
        self._indexToAnimationMap : Dict[int, AnimationSequence]    = {}

        self.animActive : Optional[AnimationSequence]       = None

        self._pos : Tuple[int,int]          = (0,0)
        self._offset : Tuple[int,int]       = (0,0) # Offset. Only used when rendering subanimation, controls the distance between subanim and main frame
        self._dimensions : Tuple[int,int]   = (0,0) # Not guaranteed reliable, workaround for alignment techniques since measuring the surface would be annoying

        # Alpha support isn't accurate to the game but its good enough visually
        # TODO - Don't use composed frame since that preblends alpha which causes every surface to require alpha drawing instead of alpha mask
        self._alpha                         = 255
        self._lastAlpha                     = 255
        self._useAlphaDrawMethods           = False
        self._workaroundEnableHidden = workaroundEnableHiddenAnim

    def _setFromMadhatter(self, assetData : AnimatedImage):
        # TODO - Break dependencies on original file so it can be reused (or implement multi-animation support)

        def convertPilRgbaToPygame(imageIn):
            targetImage = imageIn
            if imageIn.mode == "P":
                targetImage = getTransparentLaytonPaletted(imageIn)
            else:
                targetImage = imageIn.convert("RGBA")
            return pygame.image.fromstring(targetImage.tobytes("raw", "RGBA"), imageIn.size, "RGBA").convert_alpha()

        self.setVariables(assetData.variables)
        tempDimensions = (0,0)
        for frame in assetData.frames:
            tempPygameFrame = convertPilRgbaToPygame(frame.getComposedFrame())
            self._frames.append(tempPygameFrame)
            tempDimensions = (max(tempPygameFrame.get_width(), tempDimensions[0]),
                              max(tempPygameFrame.get_height(), tempDimensions[1]))

        self.setDimensions(tempDimensions)

        for anim in assetData.animations:
            self._addAnimation(AnimationSequence.fromMadhatter(anim))

    @staticmethod
    def fromMadhatter(assetData : AnimatedImage, workaroundEnableHiddenAnim=False) -> AnimatedImageObject:
        output = AnimatedImageObject(workaroundEnableHiddenAnim)
        output._setFromMadhatter(assetData)
        return output

    def setVariables(self, variableDict : Dict[str, List[int]]) -> bool:
        if len(variableDict) == 16:
            self._variables = variableDict
            return True
        return False

    def getVariable(self, name) -> Optional[List[int]]:
        for key in self._variables:
            if strCmp(name, key):
                return self._variables[key]
        return None

    def _addAnimation(self, animation : AnimationSequence):
        self._indexToAnimationMap[len(self._animations)] = animation
        self._animations[animation.name] = animation

    def _setAnimationFromActive(self):
        if self.animActive != None:
            self.animActive.reset()

    def resetActiveAnim(self):
        if self.animActive != None:
            self.animActive.reset()

    def setAnimationFromIndex(self, index : int) -> bool:
        if index in self._indexToAnimationMap and (index > 0 or self._workaroundEnableHidden):
            if self.animActive != self._indexToAnimationMap[index]:
                self.animActive = self._indexToAnimationMap[index]
                self._setAnimationFromActive()
            return True
        return False

    def setAnimationFromName(self, name : str) -> bool:
        indexAnim = 0
        for idxAnim, key in enumerate(self._animations):
            if strCmp(name, key):
                indexAnim = idxAnim
                break
        return self.setAnimationFromIndex(indexAnim)

    def setCurrentAnimationLoopStatus(self, isLooping : bool) -> bool:
        if self.animActive != None:
            self.animActive.isLooping = isLooping
            return True
        return False

    def setDimensions(self, dimensions : Tuple[int,int]):
        """Set custom dimensions for this image. This affects the clickable area for this image.

        Args:
            dimensions (Tuple[int,int]): [description]
        """
        self._dimensions = dimensions
    
    def getDimensions(self) -> Tuple[int,int]:
        """Get bounding dimensions for this image. Note that if used for positioning, this is the maximal dimensions so may not be relevant for a particular animation.

        Returns:
            Tuple[int,int]: Dimensions in form (x,y)
        """
        return self._dimensions

    def setPos(self, pos : Tuple[int,int]):
        self._pos = pos
    
    def getPos(self) -> Tuple[int,int]:
        return self._pos

    def getOffset(self) -> Tuple[int,int]:  # TODO - Need third class to hide this. Only used for subanimation
        return self._offset

    def setAlpha(self, alpha : int):
        """Set the transparency factor for this image.

        Args:
            alpha (int): Clamped to 0-255. 255 will make the image opaque
        """
        self._alpha = min(max(alpha, 0), 255)
        if self._alpha != self._lastAlpha:
            if self._alpha != 255:
                self._useAlphaDrawMethods = True
            else:
                self._useAlphaDrawMethods = False
            self._lastAlpha = self._alpha
    
    def setAlpha5Bit(self, alpha : Union[float,int]):
        """Set the transparency factor for this image. The game uses 5-bit values, so these are scaled to 8-bit for convenience.

        Args:
            alpha (Union[float,int]): 5-bit unsigned alpha value. Can be a float, but should be in 5-bit range
        """
        self.setAlpha(round((alpha * 255) / 31))

    def getPosWithOffset(self) -> Tuple[int,int]:
        # TODO - Probably safe to replace getPos with this instead...
        return self._pos[0] + self._offset[0], self._pos[1] + self._offset[1]

    def getActiveFrame(self) -> Optional[pygame.Surface]:
        """Get the current surface prior to drawing for this image. This is the raw image, so does not include subanimations, positioning, etc

        Returns:
            Optional[pygame.Surface]: Raw surface relevant to the current animation. None if there are no frames to be drawn
        """
        if self.animActive != None:
            activeFrame = self.animActive.getActiveKeyframe()
            if activeFrame != None:
                if 0 <= activeFrame < len(self._frames):
                    return self._frames[activeFrame]
        return None
    
    def wasPressed(self, cursorPos : Tuple[int,int]) -> bool:
        if self._pos[0] <= cursorPos[0] and self._pos[1] <= cursorPos[1]:
            if (self._pos[0] + self._dimensions[0]) >= cursorPos[0] and (self._pos[1] + self._dimensions[1]) >= cursorPos[1]:
                return True
        return False

    def update(self, gameClockDelta):
        hasMainFrameChanged = False
        if self.animActive != None:
            hasMainFrameChanged = self.animActive.updateCurrentFrame(gameClockDelta)
        return hasMainFrameChanged

    def _drawWithAlpha(self, gameDisplay : pygame.Surface):
        # TODO - Depreciate methods to grab surfaces, have to ensure alpha is untouched...
        # TODO - Slight performance loss from using these methods. Strange
        surface = self.getActiveFrame()
        if surface != None:
            surface.set_alpha(self._alpha)
            gameDisplay.blit(surface, self.getPosWithOffset())
            surface.set_alpha(255)  # Reset the alpha to prevent getActiveFrame from catching a surface with transparency...

    def _drawNoAlpha(self, gameDisplay : pygame.Surface):
        self._drawWithAlpha(gameDisplay)

    def draw(self, gameDisplay : pygame.Surface):
        if self._useAlphaDrawMethods:
            if self._alpha != 0:
                self._drawWithAlpha(gameDisplay)
        else:
            self._drawNoAlpha(gameDisplay)

class AnimatedImageObjectWithSubAnimation(AnimatedImageObject):

    def __init__(self):
        """Variant of AnimatedImageObject with support for subanimations. Useful for accurate sprite rendering, as includes looser logic (eg can set void animations)
        """
        super().__init__()
        self._baseDimensions = (0,0)
        self.subAnimation : Optional[AnimatedImageObject]   = None
        self._alphaBufferSurfaceOffset                      = (0,0)
        self._alphaBufferSurfaceDimensions                  = (0,0)
        self._alphaBufferSurface : Optional[pygame.Surface] = None
    
    def _setFromMadhatter(self, assetData: AnimatedImage):
        super()._setFromMadhatter(assetData)
        if assetData.subAnimation != None:
            self.subAnimation = AnimatedImageObject.fromMadhatter(assetData.subAnimation, True)
            self._baseDimensions = self.getDimensions()
            dimensionsSubImage = self.subAnimation.getDimensions()
            tempDimensions = (0,0)

            # Generate accurate dimensions encompassing subanimation as well (required for alpha buffer surface dimensions)
            for idxAnim in self._indexToAnimationMap:
                if self.setAnimationFromIndex(idxAnim):
                    offsetSubImage = self.subAnimation.getOffset()
                    tempDimensions = (max(tempDimensions[0], self._baseDimensions[0], dimensionsSubImage[0] + offsetSubImage[0]), max(tempDimensions[1], self._baseDimensions[1], dimensionsSubImage[1] + offsetSubImage[1]))
            self.setDimensions(tempDimensions)
            self._alphaBufferSurfaceDimensions = tempDimensions

    @staticmethod
    def fromMadhatter(assetData : AnimatedImage) -> AnimatedImageObjectWithSubAnimation:
        output = AnimatedImageObjectWithSubAnimation()
        output._setFromMadhatter(assetData)
        return output
    
    def setAlpha(self, alpha: int):
        super().setAlpha(alpha)
        if self._useAlphaDrawMethods:
            if self._alphaBufferSurface == None and self._alphaBufferSurfaceDimensions != (0,0):
                self._alphaBufferSurface = pygame.Surface(self._alphaBufferSurfaceDimensions).convert_alpha()

    def _setAnimationFromActive(self):
        super()._setAnimationFromActive()
        if self.animActive == None:
            if self.subAnimation != None:
                self.subAnimation.setAnimationFromIndex(0)
                self.subAnimation._offset = (0,0)
        else:
            if self.subAnimation != None:
                self.subAnimation.setAnimationFromIndex(self.animActive.subAnimationIndex)
                self.subAnimation._offset = self.animActive.subAnimationOffset

        self._alphaBufferSurfaceOffset = (0, 0)
        if self.subAnimation != None:
            if self.subAnimation.getOffset()[0] < 0 or self.subAnimation.getOffset()[1] < 0:
                self._alphaBufferSurfaceOffset = (min(self.subAnimation.getOffset()[0], 0), min(self.subAnimation.getOffset()[1], 0))

    def setAnimationFromIndex(self, index : int) -> bool:
        if index in self._indexToAnimationMap:
            if self.animActive != self._indexToAnimationMap[index]:
                self.animActive = self._indexToAnimationMap[index]
                self._setAnimationFromActive()
            return True
        return False

    def getAnimationIndex(self) -> Optional[int]:
        if self.animActive != None:
            return list(self._animations.keys()).index(self.animActive.name)
        return None

    def getBaseImageDimensions(self) -> Tuple[int, int]:
        """Get dimensions for the base component of this image (without additional subimages).

        Returns:
            Tuple[int, int]: Dimensions in form (x,y)
        """
        return self._baseDimensions

    # HACK - Anim rendering is improved but still work on correct animation routines
    def isAnimationIndexValid(self, index : int) -> bool:
        return index in self._indexToAnimationMap
    
    def getAnimationIndexIfNameIsValid(self, name : str) -> Optional[int]:
        for idxAnim, key in enumerate(self._animations):
            if strCmp(name, key):
                return idxAnim
        return None
    
    def getAnimationName(self) -> Optional[str]:
        if self.animActive != None:
            return self.animActive.name
        return None

    def doesTalkAnimExistForCurrentAnim(self) -> bool:
        if self.animActive != None:
            indexAnim = self.getAnimationIndex() + 1
            if indexAnim in self._indexToAnimationMap:
                targetAnim = self._indexToAnimationMap[indexAnim]
                if len(targetAnim.name) > 0 and targetAnim.name[0] == "*":
                    return True
        return False

    def setPos(self, pos: Tuple[int, int]):
        super().setPos(pos)
        if self.subAnimation != None:
            self.subAnimation.setPos(pos)

    def update(self, gameClockDelta):
        hasSubFrameChanged = False
        if self.subAnimation != None:
            hasSubFrameChanged = self.subAnimation.update(gameClockDelta)
        return super().update(gameClockDelta) or hasSubFrameChanged

    def _drawWithAlpha(self, gameDisplay : pygame.Surface):
        if self._alphaBufferSurface != None:
            self._alphaBufferSurface.fill((0,0,0,0))
            self._alphaBufferSurface.set_alpha(self._alpha)

            if (surf := self.getActiveFrame()) != None:
                self._alphaBufferSurface.blit(surf, (-self._alphaBufferSurfaceOffset[0], -self._alphaBufferSurfaceOffset[1]))
            if self.subAnimation != None:
                if (surf := self.subAnimation.getActiveFrame()) != None:
                    self._alphaBufferSurface.blit(surf, (self._alphaBufferSurfaceOffset[0] + self.subAnimation.getOffset()[0], self._alphaBufferSurfaceOffset[1] + self.subAnimation.getOffset()[1]))
            
            gameDisplay.blit(self._alphaBufferSurface, (self.getPosWithOffset()[0] + self._alphaBufferSurfaceOffset[0], self.getPosWithOffset()[1] + self._alphaBufferSurfaceOffset[1]))
        else:
            self._drawNoAlpha(gameDisplay)

    def _drawNoAlpha(self, gameDisplay: pygame.Surface):
        if (surface := self.getActiveFrame()) != None:
            gameDisplay.blit(surface, self.getPosWithOffset())
        if self.subAnimation != None:
            self.subAnimation.draw(gameDisplay)