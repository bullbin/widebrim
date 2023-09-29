from typing import Callable, Optional
from ..const import TIME_FRAMECOUNT_TO_MILLISECONDS

class Fader():

    def __init__(self, durationHighToLow : float, initialActiveState = True, invertOutput = False, callbackOnDone : Optional[Callable] = None, callbackClearOnDone = True):
        """Linear timing object that hooks into the update loop. Can trigger callbacks on completion of specified duration.
           Call getStrength() to see the current progress across its duration.
           The precision of timing is dependent on framerate - callbacks are executed on the next frame after the duration has completed.

        Args:
            durationHighToLow (float): Duration between start and end of timer (ms)
            initialActiveState (bool, optional): Initial state. True means timer should start immediately. Defaults to True.
            invertOutput (bool, optional): By default, range given from getStrength is 0 to 1 (inclusive). True inverts this to 1 to 0. Defaults to False.
            callbackOnDone (Callable, optional): Callback to execute when duration ends. Should have no arguments. Defaults to None.
            callbackClearOnDone (bool, optional): True will clear the callback after execution. Defaults to True.
        """
        self._duration : float              = durationHighToLow
        self._isActive : bool               = initialActiveState
        self._timeElapsed : float           = 0
        self._inverted : bool               = invertOutput
        self._callbackClearOnDone : bool    = callbackClearOnDone
        self._callback : Optional[Callable] = None
        self._isCallbackNew : bool          = False
        
        self.setCallback(callbackOnDone)
    
    def update(self, gameClockDelta : float):
        if self.getActiveState():
            self._timeElapsed += gameClockDelta
            if self._timeElapsed > self._duration:
                self.skip()
    
    def skip(self):
        """Jumps to actions at end of this fader, including disabling it and calling any attached callback.
        """
        if self.getActiveState():
            self._timeElapsed = self._duration
            self.setActiveState(False)
            self._doCallback()

    def setDuration(self, duration : float):
        """Set the duration for the phase of this fader. Will reset the timer and make it active.

        Args:
            duration (float): Duration in milliseconds
        """

        self._duration = duration
        self.reset()
    
    def setDurationInFrames(self, framecount : float):
        """Set the duration for the phase of this fader. Will reset the timer and make it active.

        Args:
            framecount (float): Duration in frames aligned to a 60fps blanking rate
        """
        self.setDuration(TIME_FRAMECOUNT_TO_MILLISECONDS * framecount)
    
    def setCallback(self, callback : Optional[Callable]):
        if self._isCallbackNew:
            self._doCallback()
        if callable(callback):
            self._isCallbackNew = True
            self._callback = callback

    def _doCallback(self):
        self._isCallbackNew = False
        if callable(self._callback):
            self._callback()
            if self._callbackClearOnDone and not(self._isCallbackNew):
                self._callback = None

    def setInvertedState(self, isInverted : bool):
        self._inverted = isInverted

    def getInvertedState(self) -> bool:
        return self._inverted

    def setActiveState(self, isActive : bool):
        self._isActive = isActive
    
    def getActiveState(self) -> bool:
        return self._isActive

    def reset(self):
        """Re-initialises this fader and re-activates it.
        """
        self._timeElapsed = 0
        self.setActiveState(True)
    
    def _calcStrength(self):
        try:
            return self._timeElapsed / self._duration
        except ZeroDivisionError:
            return 1
    
    def getStrength(self) -> float:
        """Returns the percentage of which this fader has completed its phase.

        Returns:
            float: Percentage of phase, from 0.0 to 1.0
        """
        strength = self._calcStrength()
        if self._inverted:
            return 1 - strength
        return strength

class FaderDeferredCallback(Fader):
    
    def __init__(self, durationHighToLow, initialActiveState=True, invertOutput = False, callbackOnDone=None, callbackClearOnDone=True):
        """Fader variant that delays callback execution to until the strength from the callback has been 'stabilised'.
           Strength values when being used for sensitive applications must be committed to the fader for the deferral check.
           A useful example is animating some graphic for example - it is possible for the original fader to complete
           and execute the callback before the results have been drawn, resulting in a sudden jump. By synchronising draws
           using the commit function, this can be avoided altogether.

        Args:
            durationHighToLow (float): Duration between start and end of timer (ms)
            initialActiveState (bool, optional): Initial state. True means timer should start immediately. Defaults to True.
            invertOutput (bool, optional): By default, range given from getStrength is 0 to 1 (inclusive). True inverts this to 1 to 0. Defaults to False.
            callbackOnDone (Callable, optional): Callback to execute when duration ends. Should have no arguments. Defaults to None.
            callbackClearOnDone (bool, optional): True will clear the callback after execution. Defaults to True.
        """
        super().__init__(durationHighToLow, initialActiveState, invertOutput, callbackOnDone, callbackClearOnDone)
        self.__lastGrabbedStrength = -1
    
    def reset(self):
        self.__lastGrabbedStrength = -1
        return super().reset()
    
    def commitStrength(self, value : float):
        """Commit the used strength for completion check.

        Args:
            value (float): Strength from call to getStrength(). Values outside of 0-1 bounds will cause fader to lockup
        """
        self.__lastGrabbedStrength = value
    
    def skip(self):
        if self.getActiveState():
            self._timeElapsed = self._duration
            if self.__lastGrabbedStrength == self.getStrength():
                self.setActiveState(False)
                self._doCallback()

class FaderDeferredAssumedVBlank(FaderDeferredCallback):

    def __init__(self, durationHighToLow, initialActiveState=True, invertOutput = False, callbackOnDone=None, callbackClearOnDone=True):
        """Simplified version of deferred fader which assumes fader results are only used for timing animations. This version
           removes the need to manually commit strength, and instead does so every time it is grabbed. This ensures the end frame of
           animation is drawn before any callback is executed or the state is set to False.

        Args:
            durationHighToLow (float): Duration between start and end of timer (ms)
            initialActiveState (bool, optional): Initial state. True means timer should start immediately. Defaults to True.
            invertOutput (bool, optional): By default, range given from getStrength is 0 to 1 (inclusive). True inverts this to 1 to 0. Defaults to False.
            callbackOnDone (Callable, optional): Callback to execute when duration ends. Should have no arguments. Defaults to None.
            callbackClearOnDone (bool, optional): True will clear the callback after execution. Defaults to True.
        """
        super().__init__(durationHighToLow, initialActiveState, invertOutput, callbackOnDone, callbackClearOnDone)

    def getStrength(self):
        output = super().getStrength()
        self.commitStrength(output)
        return output