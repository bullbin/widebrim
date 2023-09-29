from __future__ import annotations
from typing import Callable, Optional, TYPE_CHECKING
from pygame import MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION

if TYPE_CHECKING:
    from widebrim.engine.anim.image_anim.image import AnimatedImageObject

class TargettedButton():
    def __init__(self, callbackOnPressed, callbackOnTargetted, callbackOnUntargetted):
        self._isTargetted  : bool = False
        self._callbackOnPressed = callbackOnPressed
        self._callbackOnTargetted = callbackOnTargetted
        self._callbackOnUntargetted = callbackOnUntargetted
    
    def _setCallback(self, callback : Optional[Callable]):
        self._callbackOnPressed = callback

    def setCallbackOnPressed(self, callback : Optional[Callable]):
        if callable(callback):
            self._setCallback(callback)
        else:
            self._setCallback(None)
    
    def _doCallback(self):
        if callable(self._callbackOnPressed):
            self._callbackOnPressed()

    def setTargettedState(self, newState : bool):
        if self._isTargetted != newState:
            if newState:
                if callable(self._callbackOnTargetted):
                    self._callbackOnTargetted()
                self.doOnMouseTargetting()
            else:
                if callable(self._callbackOnUntargetted):
                    self._callbackOnUntargetted()
                self.doOnMouseAwayFromTarget()

        self._isTargetted = newState

    def doOnMouseTargetting(self):
        pass

    def doOnMouseAwayFromTarget(self):
        pass

    def doBeforePressedCallback(self):
        pass

    def getTargettedState(self):
        return self._isTargetted

    def wasPressed(self, pos):
        return False

    def handleTouchEvent(self, event):
        if event.type == MOUSEBUTTONDOWN:
            if self.wasPressed(event.pos):
                self.setTargettedState(True)
                return True
            else:
                self.setTargettedState(False)

        elif event.type == MOUSEMOTION:
            if self.getTargettedState():
                if self.wasPressed(event.pos):
                    self.doOnMouseTargetting()
                else:
                    self.doOnMouseAwayFromTarget()
                return True

        elif event.type == MOUSEBUTTONUP:
            if self.getTargettedState() and self.wasPressed(event.pos):
                self.doBeforePressedCallback()
                self._doCallback()

                self.setTargettedState(False)
                return True

            self.setTargettedState(False)
        
        return False

class NullButton(TargettedButton):
    def __init__(self, pos, posEnd, callback=None):
        TargettedButton.__init__(self, callback, None, None)
        self._posTl = pos
        self._posBr = posEnd
        self.setPos(pos)
    
    def getPos(self):
        return self._posTl

    def setPos(self, newPos):
        length = (self._posBr[0] - self._posTl[0], self._posBr[1] - self._posTl[1])
        self._posTl = newPos
        self._posBr = (newPos[0] + length[0], newPos[1] + length[1])

    def wasPressed(self, pos):
        if pos[0] >= self._posTl[0] and pos[1] >= self._posTl[1]:
            if pos[0] <= self._posBr[0] and pos[1] <= self._posBr[1]:
                return True
        return False

class StaticButton(NullButton):
    def __init__(self, pos, surfaceButton, callback=None, targettedOffset=(0,0)):
        self._image = surfaceButton
        self._offset = targettedOffset
        self._imageBlitPos = (0,0)
        self._offsetBlitPos = (0,0)
        NullButton.__init__(self, pos, (pos[0] + surfaceButton.get_width(), pos[1] + surfaceButton.get_height()), callback=callback)
    
    def setPos(self, newPos):
        super().setPos(newPos)
        self._imageBlitPos = self._posTl
        self._offsetBlitPos = (self._imageBlitPos[0] + self._offset[0], self._imageBlitPos[1] + self._offset[1])

    def doOnMouseTargetting(self):
        self._imageBlitPos = self._offsetBlitPos

    def doOnMouseAwayFromTarget(self):
        self._imageBlitPos = self._posTl
    
    def draw(self, gameDisplay):
        gameDisplay.blit(self._image, self._imageBlitPos)

class AnimatedButton(TargettedButton):

    # TODO - Unify drawables to have a draw method
    def __init__(self, image : AnimatedImageObject, animNamePressed, animNameUnpressed, callback=None):
        super().__init__(callback, None, None)
        self._animNamePressed = animNamePressed
        self._animNameUnpressed = animNameUnpressed
        self.image = image
        self.image.setAnimationFromName(self._animNameUnpressed)
        self.__customDimensions = None
    
    def setAnimNamePressed(self, name):
        if self._animNamePressed != name:
            if self.getTargettedState():
                self.image.setAnimationFromName(name)
            self._animNamePressed = name
    
    def setAnimNameUnpressed(self, name):
        if self._animNameUnpressed != name:
            if not(self.getTargettedState()):
                self.image.setAnimationFromName(name)
            self._animNameUnpressed = name
    
    def asClickable(self, animNameClicked : str, unclickAfterPress : bool = True) -> AnimatedClickableButton:
        # HACK - haha ugly
        return AnimatedClickableButton(self.image, self._animNamePressed, self._animNameUnpressed, animNameClicked, unclickAfterPress, self._callbackOnPressed)
    
    def update(self, gameClockDelta):
        self.image.update(gameClockDelta)
    
    def setDimensions(self, dimensions):
        # TODO - Check and add to targetted button.
        self.__customDimensions = dimensions

    def draw(self, gameDisplay):
        self.image.draw(gameDisplay)

    def doOnMouseTargetting(self):
        if self.image.animActive != None and self.image.animActive.name != self._animNamePressed:
            self.image.setAnimationFromName(self._animNamePressed)
    
    def doOnMouseAwayFromTarget(self):
        if self.image.animActive != None and self.image.animActive.name != self._animNameUnpressed:
            self.image.setAnimationFromName(self._animNameUnpressed)
    
    def wasPressed(self, pos):
        if self.__customDimensions != None:
            if pos[0] >= self.image.getPos()[0] and pos[1] >= self.image.getPos()[1]:
                if pos[0] <= (self.image.getPos()[0] + self.__customDimensions[0]) and pos[1] <= (self.image.getPos()[1] + self.__customDimensions[1]):
                    return True
            return False
        return self.image.wasPressed(pos)

class AnimatedClickableButton(AnimatedButton):
    def __init__(self, image : AnimatedImageObject, animNamePressed : str, animNameUnpressed : str, animNameClicked : str, doUnclickAfterCallback=True, callback:Optional[Callable]=None):
        """Variant of AnimatedButton which supports the usage of "click" anim states. Note that it is possible to softlock this button
        if you do not handle unclick methodology correctly.
        By default, after the callback is complete the button will "unclick" and reset back to standard behaviour. For buttons that
        may need to continue to be in the clicked state (eg, a button that is clicked to end a gamemode), this can be disabled. Unclicking
        will then need to be entirely manual. If the button is stuck in the clicked state, make sure the usage of the function is present.

        Args:
            image (AnimatedImageObject): Image to use as button root
            animNamePressed (str): Name of animation when button is pressed
            animNameUnpressed (str): Name of animation when button is resting
            animNameClicked (str): Name of animation when button is clicked
            doUnclickAfterCallback (bool, optional): Unclick by default after the callback is complete. Defaults to True.
            callback (Callable, optional): Callback when button is pressed. Defaults to None.
        """
        super().__init__(image, animNamePressed, animNameUnpressed, callback)
        self._animNameClicked = animNameClicked
        self.__awaitingCallback : bool                  = False
        self.__deferredCallback : Optional[Callable]    = None
        self.__drawnClickImage : bool                   = False
        self._unclickAfterPress : bool                  = doUnclickAfterCallback
        self._wasClickCallbackDone : bool               = False
    
    def setAnimNameClicked(self, name):
        # Don't do checks like other anim name setters since we want to preserve click anim (disguise click anim change)
        self._animNameClicked = name

    def _setCallback(self, callback: Optional[Callable]):
        # Prevent any issues with old callbacks by giving up held callback and preventing unclick softlock
        self.__deferredCallback = None
        self.unclickButton()
        super()._setCallback(callback)

    def _doCallback(self):
        if self.__drawnClickImage:
            super()._doCallback()
            self._wasClickCallbackDone = True

    def _canUnclick(self):
        return True

    def setTargettedState(self, newState : bool):
        if not(self.__awaitingCallback):
            super().setTargettedState(newState)

    def unclickButton(self):
        """By default, once the button is pressed it will be locked and absorb all future events. It is assumed a callback will cleanup the button afterwards.
        To return the button back to normal, call this method. Alternatively, this method can be called after callback by setting the flag on init.
        """
        self.__drawnClickImage = False
        self.__awaitingCallback = False
        self._wasClickCallbackDone = False
        self.setTargettedState(False)

    def doBeforePressedCallback(self):
        
        def modifiedCallback():
            self._doCallback()
            if self._unclickAfterPress:
                self.unclickButton()

        if callable(self._callbackOnPressed):
            self.__deferredCallback = modifiedCallback
            self.__awaitingCallback = True
            self._isTargetted = True
            self.image.setAnimationFromName(self._animNameClicked)
    
    def draw(self, gameDisplay):
        if self.__awaitingCallback:
            if self.__drawnClickImage:
                if not(self._wasClickCallbackDone):
                    self.__deferredCallback()
            elif (self.image.animActive != None and self.image.animActive.name == self._animNameClicked and self._canUnclick()) or (self.image.animActive == None and self._canUnclick()):
                self.__drawnClickImage = True

        return super().draw(gameDisplay)

    def handleTouchEvent(self, event):
        if self.__awaitingCallback:
            return True
        return super().handleTouchEvent(event)