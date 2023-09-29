from .script import ScriptPlayer
from .const import PATH_SCRIPT_LOGO
from ...madhatter.hat_io.asset_script import GdScript
from ...engine.state.enum_mode import GAMEMODES

from widebrim.madhatter.hat_io.asset_sav import Layton2SaveSlot
from widebrim.engine.state.manager.state import Layton2GameState

class ResetHelper(ScriptPlayer):
    def __init__(self, laytonState : Layton2GameState, screenController):

        # HACK - This fixes a bug where title reset spawns incorrectly
        laytonState.saveSlot = Layton2SaveSlot()
        laytonState.resetState()

        ScriptPlayer.__init__(self, laytonState, screenController, GdScript())
        self._script.load(laytonState.getFileAccessor().getData(PATH_SCRIPT_LOGO))
        self._isActive = False
        self.screenController.fadeOut(callback=self._makeActive)

    def doOnKill(self):
        self.laytonState.setGameMode(GAMEMODES.Title)
        return super().doOnKill()