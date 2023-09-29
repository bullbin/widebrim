from __future__ import annotations
from typing import TYPE_CHECKING, Callable, Optional
from widebrim.engine.anim.button import AnimatedButton

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController

from widebrim.engine_ext.utils import doesImageExist, getButtonFromPath
from widebrim.gamemodes.core_popup.utils import MainScreenPopup
from widebrim.gamemodes.nazo_popup.mode.base.const import NAME_ANIM_TUTORIAL_BACK_OFF, NAME_ANIM_TUTORIAL_BACK_ON, NAME_ANIM_TUTORIAL_NEXT_OFF, NAME_ANIM_TUTORIAL_NEXT_ON, NAME_ANIM_VAR_POS_TUT_BACK, NAME_ANIM_VAR_POS_TUT_NEXT, PATH_ANIM_BTN_TUTORIAL, PATH_BG_TUTORIAL

from pygame.constants import MOUSEBUTTONUP

def shouldTutorialSpawn(laytonState) -> bool:
    if (nzDat := laytonState.getNazoData()) != None:
        if laytonState.saveSlot.tutorialFlag.getSlot(nzDat.idTutorial) == True:
            return False
    return doesImageExist(laytonState, PATH_BG_TUTORIAL % (laytonState.language.value, nzDat.idTutorial, 0))

class BottomScreenOverlayTutorial(MainScreenPopup):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController, callbackOnTerminate : Optional[Callable]):
        super().__init__(callbackOnTerminate)
        self.__laytonState = laytonState
        self.__screenController = screenController

        self.__callbackOnTerminate  = callbackOnTerminate
        self.__countTutorialPages   = 0
        self.__indexCurrentPage     = 0
        self.__btnForward : Optional[AnimatedButton]    = None
        self.__btnBackward : Optional[AnimatedButton]   = None

        canQuitEarly = False
        self.__idTutorial : Optional[int] = None
        if (nzDat := laytonState.getNazoData()) != None:
            # TODO - Abstract tutorial flags
            self.__idTutorial = nzDat.idTutorial
            if laytonState.saveSlot.tutorialFlag.getSlot(self.__idTutorial) != True:
                laytonState.saveSlot.tutorialFlag.setSlot(True, self.__idTutorial)
            else:
                canQuitEarly = True

        if not(canQuitEarly):
            while doesImageExist(laytonState, PATH_BG_TUTORIAL % (laytonState.language.value, self.__idTutorial, self.__countTutorialPages)):
                self.__countTutorialPages += 1
            if self.__countTutorialPages == 0:
                canQuitEarly = True
        
        if canQuitEarly:
            # HACK - This will cause problems as variable is overwritten during init... Use spawn function to prevent this possibility
            # TODO - Offer method for all popups to get if should be killed immediately, then kill after init in parent object
            if callable(self.__callbackOnTerminate):
                self.__callbackOnTerminate()
        else:
            self.__btnForward = getButtonFromPath(laytonState, PATH_ANIM_BTN_TUTORIAL, self.__callbackOnForward, NAME_ANIM_TUTORIAL_NEXT_OFF, NAME_ANIM_TUTORIAL_NEXT_ON, namePosVariable=NAME_ANIM_VAR_POS_TUT_NEXT)
            self.__btnBackward = getButtonFromPath(laytonState, PATH_ANIM_BTN_TUTORIAL, self.__callbackOnBackward, NAME_ANIM_TUTORIAL_BACK_OFF, NAME_ANIM_TUTORIAL_BACK_ON, namePosVariable=NAME_ANIM_VAR_POS_TUT_BACK)
            self.__reloadTutorialImage()
    
    def __reloadTutorialImage(self):
        self.__screenController.setBgMain(PATH_BG_TUTORIAL % (self.__laytonState.language.value, self.__idTutorial, self.__indexCurrentPage))

    def __callbackOnForward(self):
        self.__indexCurrentPage += 1
        if self.__indexCurrentPage >= self.__countTutorialPages:
            if callable(self.__callbackOnTerminate):
                self.__callbackOnTerminate()
        else:
            self.__reloadTutorialImage()

    def __callbackOnBackward(self):
        if self.__indexCurrentPage > 0:
            self.__indexCurrentPage -= 1
            self.__reloadTutorialImage()
    
    def __shouldDrawForwards(self):
        return self.__countTutorialPages > self.__indexCurrentPage + 1
    
    def __shouldDrawBackwards(self):
        return self.__indexCurrentPage > 0

    def update(self, gameClockDelta):
        if self.__shouldDrawBackwards() and self.__btnBackward != None:
            self.__btnBackward.update(gameClockDelta)
        if self.__shouldDrawForwards() and self.__btnForward != None:
            self.__btnForward.update(gameClockDelta)
        return super().update(gameClockDelta)

    def draw(self, gameDisplay):
        if self.__shouldDrawBackwards() and self.__btnBackward != None:
            self.__btnBackward.draw(gameDisplay)
        if self.__shouldDrawForwards() and self.__btnForward != None:
            self.__btnForward.draw(gameDisplay)
    
    def handleTouchEvent(self, event):
        if self.__shouldDrawBackwards() and self.__btnBackward != None and self.__btnBackward.handleTouchEvent(event):
            return True
        if self.__shouldDrawForwards() and self.__btnForward != None and self.__btnForward.handleTouchEvent(event):
            return True
        if self.__indexCurrentPage == self.__countTutorialPages - 1 and event.type == MOUSEBUTTONUP:
            if callable(self.__callbackOnTerminate):
                self.__callbackOnTerminate()
                return True
        return super().handleTouchEvent(event)