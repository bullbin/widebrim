# Try to bypass DPI scaling on Windows to preserve pixel-perfect scaling
# Switching displays with different scales may cause Windows to scale this anyway
try:
    import ctypes
    ctypes.windll.user32.SetProcessDPIAware()
except ImportError:
    pass

# Configure debug logging
from widebrim.madhatter.common import NamedLogger

NamedLogger.SHOW_CRITICAL       = True
NamedLogger.SHOW_IMPORTANT      = True
NamedLogger.SHOW_UNIMPORTANT    = False

import pygame
from widebrim.engine.state.manager.collective import Layton2CollectiveState
from widebrim.engine.state.clock import AltClock
from widebrim.engine.state.enum_mode import GAMEMODES
from widebrim.engine.const import LANGUAGES
from widebrim.engine.config import TIME_FRAMERATE
from widebrim.engine_ext.state_game import ScreenCollectionGameModeSpawner

from widebrim.engine.convenience import initDisplay
from widebrim.engine.custom_events import ENGINE_SKIP_CLOCK
from widebrim.engine_ext.rom import applyPygameBannerTweaks
from widebrim.engine_ext.utils import cleanTempFolder

from traceback import print_exc

def play(rootHandler : ScreenCollectionGameModeSpawner, state : Layton2CollectiveState):

    applyPygameBannerTweaks(state.getFileAccessor())

    isActive = True
    gameDisplay = initDisplay()
    gameClockDelta = 0
    gameClock = AltClock()
    gameClockInterval = 1 / TIME_FRAMERATE
    timeClockInterval = gameClockInterval * 1000

    enableSpeedModifier = False

    while isActive:
        
        rootHandler.update(gameClockDelta)
        rootHandler.draw(gameDisplay)
        pygame.display.update()

        bypassClock = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                isActive = False
                rootHandler.doOnPygameQuit()
            elif event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP or event.type == pygame.MOUSEMOTION:
                rootHandler.handleTouchEvent(event)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                enableSpeedModifier = True
            elif event.type == pygame.KEYUP and event.key == pygame.K_TAB:
                enableSpeedModifier = False
            elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                rootHandler.handleKeyboardEvent(event)
            elif event.type == ENGINE_SKIP_CLOCK:
                bypassClock = True

        gameClockDelta = gameClock.tick(gameClockInterval)
        if bypassClock:
            gameClockDelta = timeClockInterval
        
        if gameClockDelta / timeClockInterval > 1.25:
            gameClockDelta = timeClockInterval
        
        if enableSpeedModifier:
            gameClockDelta *= 4
    
    pygame.display.quit()
    pygame.quit()

debugState      = Layton2CollectiveState(language=LANGUAGES.English)
debugHandler    = ScreenCollectionGameModeSpawner(debugState)

# Enter the game under Reset state, as if booting up for first time
debugState.setGameMode(GAMEMODES.Reset)

try:
    play(debugHandler, debugState)
except Exception as e:
    pygame.display.quit()
    pygame.quit()

    print("widebrim has crashed!")
    print(debugState.getGameMode(), debugState.getEventId(), debugState.getMovieNum(), debugState.saveSlot.roomIndex)
    print("\nStack Trace:")
    print_exc()
    print("\nPlease report this information to the widebrim project at https://github.com/bullbin/widebrim.")

    try:
        debugHandler.doOnPygameQuit()
    except Exception as f:
        print_exc()
    input("\nExecution will now end, close the terminal or press ENTER to stop...")

cleanTempFolder()