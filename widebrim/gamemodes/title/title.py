from widebrim.engine.const import TIME_FRAMECOUNT_TO_MILLISECONDS
from widebrim.engine_ext.utils import getTopScreenAnimFromPath
from ...engine.state.layer import ScreenLayerNonBlocking
from ...madhatter.hat_io.asset_sav import Layton2SaveFile
from ...engine.anim.fader import Fader
from ...engine.state.enum_mode import GAMEMODES
from .const import PATH_ANIM_TITLE, PATH_BG_TITLE_SUB
from ...engine.config import PATH_SAVE
from .main_title import MenuScreen
from ...gamemodes.core_popup.save import SaveLoadScreenPopup

# Here to expose for quick launchers to be able to immediately launch a slot
def behaviourOnContinue(laytonState):
    # TODO - Does time increase while in secret mode as well?
    chapterEntry = laytonState.getChapterInfEntry()
    if chapterEntry != None:
        laytonState.setGameMode(GAMEMODES.DramaEvent)
        if chapterEntry.idEventAlt != 0:
            if laytonState.saveSlot.eventViewed.getSlot(chapterEntry.indexEventViewedFlag):
                laytonState.setEventId(chapterEntry.idEventAlt)
                return
        laytonState.setEventId(chapterEntry.idEvent)
    else:
        laytonState.setGameMode(GAMEMODES.Room)
    return

class TitlePlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState, screenController):
        ScreenLayerNonBlocking.__init__(self)

        saveBytes = None
        saveData = Layton2SaveFile()
        # TODO - Only active check required, nothing more
        try:
            with open(PATH_SAVE, 'rb') as saveIn:
                saveBytes = saveIn.read()
            if not(saveData.load(saveBytes)):
                saveData = Layton2SaveFile()
        except FileNotFoundError:
            pass

        self.__animTitleScreen = getTopScreenAnimFromPath(laytonState, PATH_ANIM_TITLE)
        self.popup = None

        # Callbacks for exiting title screen
        def callbackTriggerGameContinue():
            screenController.fadeOut(callback=callbackContinueGame)
        
        def callbackContinueGame():
            laytonState.loadChapterInfoDb()
            behaviourOnContinue(laytonState)
            laytonState.unloadChapterInfoDb()
            self._canBeKilled = True

        def callbackTriggerSecretScreen():
            screenController.fadeOut(callback=callbackStartSecret)
        
        def callbackStartSecret():
            laytonState.setGameMode(GAMEMODES.SecretMenu)
            self._canBeKilled = True

        # Callbacks for UI buttons
        def callbackTerminate():
            self._canBeKilled = True

        def callbackSpawnTitle():
            screenController.fadeOutMain(callback=callbackStartMainScreenAnim)
        
        def callbackSpawnContinue():
            screenController.fadeOutMain(callback=callbackStartContinueScreen)
        
        def callbackSpawnBonus():
            screenController.fadeOutMain(callback=callbackStartBonusScreen)

        def callbackStartMainScreenAnim():
            self.popup = MenuScreen(laytonState, screenController, saveData,
                                    callbackSpawnTitle, callbackSpawnContinue, callbackSpawnBonus, callbackTerminate)
        
        def callbackStartContinueScreen():
            self.popup = SaveLoadScreenPopup(laytonState, screenController, SaveLoadScreenPopup.MODE_LOAD, 0, callbackSpawnTitle, callbackTriggerGameContinue)
        
        def callbackStartBonusScreen():
            self.popup = SaveLoadScreenPopup(laytonState, screenController, SaveLoadScreenPopup.MODE_LOAD, 1, callbackSpawnTitle, callbackTriggerSecretScreen)

        self.screenController = screenController
        self.laytonState = laytonState
        self.logoAlphaFader = Fader(TIME_FRAMECOUNT_TO_MILLISECONDS * 45, initialActiveState=False, callbackOnDone=callbackStartMainScreenAnim)

        def callbackStartLogoAnim():
            self.logoAlphaFader.setActiveState(True)
        
        def callbackStartTitleScreen():
            self.screenController.setBgSub(PATH_BG_TITLE_SUB)
            self.screenController.fadeInSub(duration=TIME_FRAMECOUNT_TO_MILLISECONDS * 30, callback=callbackStartLogoAnim)
        
        # TODO - Save corrupt screen
        callbackStartTitleScreen()

    def update(self, gameClockDelta):
        self.logoAlphaFader.update(gameClockDelta)
        if self.__animTitleScreen != None and self.__animTitleScreen.getActiveFrame() != None:
            self.__animTitleScreen.setAlpha(round(255 * self.logoAlphaFader.getStrength()))
        if self.popup != None:
            self.popup.update(gameClockDelta)
    
    def draw(self, gameDisplay):
        if self.__animTitleScreen != None:
            self.__animTitleScreen.draw(gameDisplay)
        if self.popup != None:
            self.popup.draw(gameDisplay)
        
    def handleTouchEvent(self, event):
        if self.popup != None and not(self.screenController.getFadingStatus()):
            self.popup.handleTouchEvent(event)
        else:
            return super().handleTouchEvent(event)