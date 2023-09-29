from widebrim.engine_ext.const import SHAKE_PIX
from widebrim.madhatter.common import logSevere
from ..engine.state.layer import ScreenCollection, ScreenLayerNonBlocking
from ..engine.state.enum_mode import GAMEMODES
from ..engine.const import RESOLUTION_NINTENDO_DS
from ..engine.anim.fader import Fader, FaderDeferredAssumedVBlank

from ..gamemodes import *
from ..gamemodes.core_popup.reset import ResetHelper

from ..engine.custom_events import ENGINE_SKIP_CLOCK
from .utils import getImageFromPath

from random import randint

from pygame.event import post, Event
from pygame import Surface, QUIT, MOUSEBUTTONUP

GAMEMODE_TO_HANDLER = {GAMEMODES.Reset:ResetHelper,
                       GAMEMODES.DramaEvent:EventPlayer,
                       GAMEMODES.Room:RoomPlayer,
                       GAMEMODES.Movie:MoviePlayer,
                       GAMEMODES.StartPuzzle:StartPuzzlePlayer,
                       GAMEMODES.EndPuzzle:EndPuzzlePlayer,
                       GAMEMODES.StayPuzzle:StayPuzzlePlayer,
                       GAMEMODES.Puzzle:PuzzlePlayer,
                       GAMEMODES.Title:TitlePlayer,
                       GAMEMODES.Narration:NarrationPlayer,
                       GAMEMODES.Bag:BagPlayer,
                       GAMEMODES.Name:NamePlayer,
                       GAMEMODES.JitenBag:JitenPlayer,
                       GAMEMODES.Mystery:MysteryPlayer,
                       GAMEMODES.JitenWiFi:JitenPlayer,
                       GAMEMODES.Memo:MemoPlayer,
                       GAMEMODES.EventTea:EventTeaPlayer,
                       GAMEMODES.SecretMenu:SecretMenuPlayer,
                       GAMEMODES.WiFiSecretMenu:WiFiSecretMenuPlayer,
                       GAMEMODES.TopSecretMenu:TopSecretMenuPlayer,
                       GAMEMODES.JitenSecret:JitenPlayer,
                       GAMEMODES.ArtMode:ArtModePlayer,
                       GAMEMODES.ChrViewMode:ChrViewModePlayer,
                       GAMEMODES.MovieViewMode:MovieViewModePlayer,
                       GAMEMODES.HamsterName:NamePlayer,
                       GAMEMODES.NintendoWfcSetup:NintendoWfcBypassPlayer,
                       GAMEMODES.WiFiDownloadPuzzle:WiFiDownloadPuzzleBypassPlayer,
                       GAMEMODES.Passcode:PasscodePlayer,
                       GAMEMODES.CodeInputPandora:CodeInputPlayer,
                       GAMEMODES.CodeInputFuture:CodeInputPlayer,
                       GAMEMODES.Diary:DiaryPlayer,
                       GAMEMODES.Nazoba:NazobaPlayer}

class BgLayer(ScreenLayerNonBlocking):

    # Holds background layers used in game
    # Only Layer 3 backgrounds should be applied to this layer

    def __init__(self, laytonState):
        ScreenLayerNonBlocking.__init__(self)
        self._laytonState = laytonState

        self._faderShakeMain    = Fader(0, initialActiveState=False)
        self._faderShakeSub     = Fader(0, initialActiveState=False)

        self._bgMain    = Surface(RESOLUTION_NINTENDO_DS)
        self._bgSub     = Surface(RESOLUTION_NINTENDO_DS)
        self._bgMainPal = Surface(RESOLUTION_NINTENDO_DS)
        self._bgSubPal  = Surface(RESOLUTION_NINTENDO_DS)

        self._palMain   = 0
        self._palSub    = 0
    
    def update(self, gameClockDelta):
        self._faderShakeMain.update(gameClockDelta)
        self._faderShakeSub.update(gameClockDelta)

    def _setBg(self, pathBg):
        if pathBg != None:
            bg = getImageFromPath(self._laytonState, pathBg)
            if bg != None:
                return bg
        return Surface(RESOLUTION_NINTENDO_DS)
    
    def _updatePal(self, inImage, darkness):
        tempImage = inImage.copy()
        darkener = Surface((inImage.get_width(), inImage.get_height()))
        darkener.set_alpha(darkness)
        tempImage.blit(darkener, (0,0))
        return tempImage

    def shakeBg(self, duration):
        self._faderShakeMain.setDuration(duration)
        self._faderShakeMain.setActiveState(True)

    def shakeBgSub(self, duration):
        self._faderShakeSub.setDuration(duration)
        self._faderShakeSub.setActiveState(True)

    def setBgMain(self, pathBg):
        # Should this be blitted instead?
        self._bgMain = self._setBg(pathBg)
        self._bgMainPal = self._updatePal(self._bgMain, self._palMain)

    def setBgSub(self, pathBg):
        self._bgSub = self._setBg(pathBg)
        self._bgSubPal = self._updatePal(self._bgSub, self._palSub)
    
    def modifyPaletteMain(self, darkness):
        self._palMain = darkness
        self._bgMainPal = self._updatePal(self._bgMain, self._palMain)
    
    def modifyPaletteSub(self, darkness):
        self._palSub = darkness
        self._bgSubPal = self._updatePal(self._bgSub, self._palSub)

    def draw(self, gameDisplay):

        def drawBg(surface, originalPos, shakeFader):
            if shakeFader.getActiveState():
                # HACK - Screen isn't clipped for speed sake
                gameDisplay.blit(surface, (originalPos[0] + randint(-SHAKE_PIX,SHAKE_PIX), originalPos[1] + randint(-SHAKE_PIX,SHAKE_PIX)))
            else:
                gameDisplay.blit(surface, originalPos)

        drawBg(self._bgMainPal, (0,RESOLUTION_NINTENDO_DS[1]), self._faderShakeMain)
        drawBg(self._bgSubPal, (0,0), self._faderShakeSub)

class FaderLayer(ScreenLayerNonBlocking):

    DEFAULT_FADE_TIME = 250

    def __init__(self):
        ScreenLayerNonBlocking.__init__(self)
        self._faderSurfMain  = Surface(RESOLUTION_NINTENDO_DS)
        self._faderSurfSub   = Surface(RESOLUTION_NINTENDO_DS)

        self._faderMain     = FaderDeferredAssumedVBlank(0, initialActiveState=False)
        self._faderSub      = FaderDeferredAssumedVBlank(0, initialActiveState=False)
        self._faderWait         = Fader(0, initialActiveState=False)

        self._waitCanBeSkipped  = False
        self.isViewObscured = False

    def update(self, gameClockDelta):
        self._faderMain.update(gameClockDelta)
        self._faderSub.update(gameClockDelta)
        self._faderWait.update(gameClockDelta)

        if self._faderMain.getStrength() == 1 and self._faderSub.getStrength() == 1:
            self.isViewObscured = True
        else:
            self.isViewObscured = False

        self._faderSurfMain.set_alpha(round(self._faderMain.getStrength() * 255))
        self._faderSurfSub.set_alpha(round(self._faderSub.getStrength() * 255))
    
    def __ensureMainIsColor(self, color):
        if self._faderSurfMain.get_at((0,0)) != color:
            self._faderSurfMain.fill(color)

    def fadeInMain(self, duration=DEFAULT_FADE_TIME, callback=None):
        # TODO - Match callback model
        self.__ensureMainIsColor((0,0,0))
        if not(self._faderMain.getActiveState()) and self._faderMain.getStrength() == 0:
            if callable(callback):
                callback()
        else:
            post(Event(ENGINE_SKIP_CLOCK))
            self._faderMain.setDuration(duration)
            self._faderMain.setCallback(callback)
            self._faderMain.setInvertedState(True)
            return True
        return False
    
    def fadeOutMain(self, duration=DEFAULT_FADE_TIME, callback=None):
        # TODO - Add a method that intercepts callbacks to bring flags to blank out screen where necessary.
        # Maybe add a variation of callback which ensures the fader layer has been rendered before operating callback
        self.__ensureMainIsColor((0,0,0))
        if not(self._faderMain.getActiveState()) and self._faderMain.getStrength() == 1:
            if callable(callback):
                callback()
        else:
            post(Event(ENGINE_SKIP_CLOCK))
            self._faderMain.setDuration(duration)
            self._faderMain.setCallback(callback)
            self._faderMain.setInvertedState(False)
            return True
        return False
    
    def flashMain(self, duration=DEFAULT_FADE_TIME, callback=None):
        # TODO - Fix callbacks
        self.__ensureMainIsColor((255,255,255))
        self._faderMain.setDuration(duration)
        self._faderMain.setCallback(callback)
        self._faderMain.setInvertedState(True)
        return True
    
    def fadeInSub(self, duration=DEFAULT_FADE_TIME, callback=None):
        if not(self._faderSub.getActiveState()) and self._faderSub.getStrength() == 0:
            if callable(callback):
                callback()
        else:
            post(Event(ENGINE_SKIP_CLOCK))
            self._faderSub.setDuration(duration)
            self._faderSub.setCallback(callback)
            self._faderSub.setInvertedState(True)
            return True
        return False
    
    def fadeOutSub(self, duration=DEFAULT_FADE_TIME, callback=None):
        if not(self._faderSub.getActiveState()) and self._faderSub.getStrength() == 1:
            if callable(callback):
                callback()
        else:
            post(Event(ENGINE_SKIP_CLOCK))
            self._faderSub.setDuration(duration)
            self._faderSub.setCallback(callback)
            self._faderSub.setInvertedState(False)
            return True
        return False
    
    # TODO - Callback can only be called when both screens are ready, this will call when either are ready which is not the right behaviour
    # TODO - Remove wait fader
    def fadeIn(self, duration=DEFAULT_FADE_TIME, callback=None):
        post(Event(ENGINE_SKIP_CLOCK))
        self.fadeInSub(duration=duration)
        return self.fadeInMain(duration=duration, callback=callback)
        
    def fadeOut(self, duration=DEFAULT_FADE_TIME, callback=None):
        post(Event(ENGINE_SKIP_CLOCK))
        self.fadeOutSub(duration=duration)
        return self.fadeOutMain(duration=duration, callback=callback)
        
    def setWaitDuration(self, duration, canBeSkipped=False):
        self._faderWait.setDuration(duration)
        self._waitCanBeSkipped = canBeSkipped

    def getFaderStatus(self):
        return self._faderSub.getActiveState() or self._faderMain.getActiveState() or self._faderWait.getActiveState()

    def draw(self, gameDisplay):
        gameDisplay.blit(self._faderSurfSub, (0,0))
        gameDisplay.blit(self._faderSurfMain, (0,RESOLUTION_NINTENDO_DS[1]))

    def handleTouchEvent(self, event):
        if self._waitCanBeSkipped and event.type == MOUSEBUTTONUP:
            self._faderWait.setActiveState(False)
            self._waitCanBeSkipped = False
        return super().handleTouchEvent(event)

class ScreenController():
    def __init__(self, faderLayer, bgLayer):
        self._faderLayer = faderLayer
        self._bgLayer = bgLayer
        self._waitFader = Fader(0, initialActiveState=False)
        self._waitingForTap = False

    def getFadingStatus(self):
        return self._faderLayer.getFaderStatus()

    def getFaderIsViewObscured(self):
        return self._faderLayer.isViewObscured
    
    def flashMain(self, duration=FaderLayer.DEFAULT_FADE_TIME, callback=None):
        self._faderLayer.flashMain(duration=duration, callback=callback)

    def fadeInMain(self, duration=FaderLayer.DEFAULT_FADE_TIME, callback=None):
        self._faderLayer.fadeInMain(duration=duration, callback=callback)
    
    def fadeOutMain(self, duration=FaderLayer.DEFAULT_FADE_TIME, callback=None):
        self._faderLayer.fadeOutMain(duration=duration, callback=callback)
    
    def fadeInSub(self, duration=FaderLayer.DEFAULT_FADE_TIME, callback=None):
        self._faderLayer.fadeInSub(duration=duration, callback=callback)
    
    def fadeOutSub(self, duration=FaderLayer.DEFAULT_FADE_TIME, callback=None):
        self._faderLayer.fadeOutSub(duration=duration, callback=callback)
    
    def fadeIn(self, duration=FaderLayer.DEFAULT_FADE_TIME, callback=None):
        self._faderLayer.fadeIn(duration=duration, callback=callback)
        
    def fadeOut(self, duration=FaderLayer.DEFAULT_FADE_TIME, callback=None):
        self._faderLayer.fadeOut(duration=duration, callback=callback)

    def setWaitDuration(self, duration, canBeSkipped=False):
        self._faderLayer.setWaitDuration(duration, canBeSkipped=canBeSkipped)

    def setBgMain(self, path):
        self._bgLayer.setBgMain(path)
        self.modifyPaletteMain(0)

    def setBgSub(self, path):
        self._bgLayer.setBgSub(path)
        self.modifyPaletteSub(0)

    def modifyPaletteMain(self, darkness):
        self._bgLayer.modifyPaletteMain(darkness)

    def modifyPaletteSub(self, darkness):
        self._bgLayer.modifyPaletteSub(darkness)
    
    def shakeBg(self, duration):
        self._bgLayer.shakeBg(duration)
    
    def shakeBgSub(self, duration):
        self._bgLayer.shakeBgSub(duration)

class ScreenCollectionGameModeSpawner(ScreenCollection):
    def __init__(self, laytonState):
        ScreenCollection.__init__(self)

        self.laytonState = laytonState

        layerFader = FaderLayer()
        layerBg    = BgLayer(laytonState)

        self.screenControllerObject = ScreenController(layerFader, layerBg)
        self.addToCollection(layerBg)
        self.addToCollection(layerFader)

        self._currentActiveGameMode = 0
        self._currentActiveGameModeObject = None

        self._waitingForFadeOut = False

    def _loadGameMode(self, gameMode):
        # TODO - Fix support for unimplemented gamemode values
        self._currentActiveGameMode = gameMode
        self.laytonState.setGameMode(gameMode)

        layerFader = self._layers.pop()

        if gameMode in GAMEMODE_TO_HANDLER:
            self.addToCollection(GAMEMODE_TO_HANDLER[gameMode](self.laytonState, self.screenControllerObject))
        else:
            if gameMode == GAMEMODES.INVALID:
                self._voidGameMode()
            else:
                logSevere("Missing implementation for mode", gameMode.name, name="GamemodeErr")
                self._currentActiveGameModeObject = None

            self.addToCollection(layerFader)
            return False
        
        self._currentActiveGameModeObject = self._layers[-1]
        self.addToCollection(layerFader)
        return True
    
    def _voidGameMode(self):
        self._currentActiveGameMode = GAMEMODES.INVALID
        self._currentActiveGameModeObject = None

    def _triggerQuit(self):
        post(Event(QUIT))
    
    def update(self, gameClockDelta):
        # TODO - Remove obscure methods. Obselete due to new writing conventions
        # TODO - Fix callbacks that may overwrite each other, use a queue
        # TODO - Fix fade out callbacks, as callbacks are only assigned to main fader.

        def callbackFadeOutComplete():
            self._waitingForFadeOut = False

        def readyScreenFadeOut():
            self._waitingForFadeOut = True
            self.screenControllerObject.fadeOut(callback=callbackFadeOutComplete)
        
        def readyGameModeSwitch(nextGameMode):
            if self.screenControllerObject.getFaderIsViewObscured():
                self._voidGameMode()
                self._loadGameMode(nextGameMode)
            else:
                readyScreenFadeOut()

        if not(self._waitingForFadeOut):
            if self._currentActiveGameModeObject != None:
                if self._currentActiveGameModeObject.getContextState():
                    # If the current gamemode is finised (equivalent to code on exit in binary, works on stack), terminate and reload current gamemode (which should've changed)
                    readyGameModeSwitch(self.laytonState.getGameMode())
            else:
                if self._currentActiveGameMode != self.laytonState.getGameMode():
                    # If first run, spawn initial game mode
                    readyGameModeSwitch(self.laytonState.getGameMode())
                elif self.laytonState.getGameModeNext() != self.laytonState.getGameMode():
                    # Hack: If there is an unimplemented (or invalid) state loaded, attempt to load the next gamemode instead.
                    logSevere("Hack: Skip gamemode to", self.laytonState.getGameModeNext(), name="GamemodeErr")
                    readyGameModeSwitch(self.laytonState.getGameModeNext())
                else:
                    # If neither the current or next gamemode spawned a handler, terminate the game.
                    self._triggerQuit()
        
        # Override original update to ensure game mode object cannot be deleted, as logic above does that properly
        for indexLayer in range(len(self._layers) - 1, -1, -1):
            layer = self._layers[indexLayer]
            layer.update(gameClockDelta)
            if layer.getContextState() and layer != self._currentActiveGameModeObject:
                self.removeFromCollection(indexLayer)