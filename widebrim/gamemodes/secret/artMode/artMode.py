from __future__ import annotations
from typing import Optional, TYPE_CHECKING

from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine.state.enum_mode import GAMEMODES
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getButtonFromPath, getStaticButtonFromAnim, getTxtString, offsetVectorToSecondScreen
from widebrim.engine.anim.image_anim.imageAsNumber import StaticImageAsNumericalFont
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
from widebrim.madhatter.common import logSevere

from .const import *

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController
    from widebrim.engine.anim.button import StaticButton

class ArtModePlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController):
        ScreenLayerNonBlocking.__init__(self)

        self.__laytonState = laytonState
        self.__screenController = screenController
        self.__buttons = []
        self.__numRenderer : Optional[StaticImageAsNumericalFont] = None
        self.__indexArt : int = -1
        self.__textRendererTitle = StaticTextHelper(laytonState.fontEvent)
        self.__textRendererDescription = StaticTextHelper(laytonState.fontEvent)
        
        # TODO - Weird text positioning... again.
        x,y = POS_TEXT_TITLE
        self.__textRendererTitle.setPos(offsetVectorToSecondScreen((x,y + 2)))
        self.__textRendererDescription.setPos(offsetVectorToSecondScreen(POS_TEXT_DESC))

        def addButtonIfNotNone(button : Optional[StaticButton]):
            if button != None:
                self.__buttons.append(button)

        self.__animBtn = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_SECRET_BUTTON)
        addButtonIfNotNone(getStaticButtonFromAnim(self.__animBtn, NAME_ANIM_BTN_BACK, pos=POS_BTN_BACK, callback=self.__callbackOnBack, clickOffset=BTN_CLICK_OFFSET))
        addButtonIfNotNone(getStaticButtonFromAnim(self.__animBtn, NAME_ANIM_BTN_NEXT, pos=POS_BTN_NEXT, callback=self.__callbackOnNext, clickOffset=BTN_CLICK_OFFSET))

        if (animFont := getBottomScreenAnimFromPath(laytonState, PATH_ANIM_PICARAT_NUM)) != None:
            self.__numRenderer = StaticImageAsNumericalFont(animFont, stride=STRIDE_PAGE, maxNum=99, usePadding=True)
            self.__numRenderer.setPos(offsetVectorToSecondScreen(POS_PAGE_DISPLAY))

        self.__btnCancel = getButtonFromPath(laytonState, PATH_ANIM_BTN_CANCEL, callback=self.__callbackOnCancel)
        addButtonIfNotNone(self.__btnCancel)

        screenController.setBgMain(PATH_BG_MAIN)

        # TODO - Sound index here (haha)

        self.__setIndexAndText(0)
        screenController.fadeIn()

    def __setIndexAndText(self, index : int):
        if self.__indexArt != index:
            self.__indexArt = index
            if self.__numRenderer != None:
                self.__numRenderer.setText(index + 1)
            
            # TODO - Missing file check
            self.__textRendererTitle.setText(getTxtString(self.__laytonState, PATH_TEXT_TITLE % index))
            self.__textRendererDescription.setText(getTxtString(self.__laytonState, PATH_TEXT_DESC % index))

            if not(0 <= index < len(MAP_BG_TO_INDEX)):
                logSevere("Missing art BG mapping, index %i out of range!" % index, name="ArtMode")
            self.__screenController.setBgSub(PATH_BG_ART % MAP_BG_TO_INDEX[index])

    def __callbackOnBack(self):
        self.__setIndexAndText((self.__indexArt - 1)  % 10)
    
    def __callbackOnNext(self):
        self.__setIndexAndText((self.__indexArt + 1)  % 10)

    def __callbackOnCancel(self):
        self.__laytonState.setGameMode(GAMEMODES.TopSecretMenu)
        self.__screenController.fadeOut(callback=self.doOnKill)

    def draw(self, gameDisplay):
        for button in self.__buttons:
            button.draw(gameDisplay)
        if self.__numRenderer != None:
            self.__numRenderer.drawBiased(gameDisplay)
        self.__textRendererTitle.drawXYCenterPoint(gameDisplay)
        self.__textRendererDescription.draw(gameDisplay)
    
    def update(self, gameClockDelta):
        if self.__btnCancel != None:
            self.__btnCancel.update(gameClockDelta)
    
    def handleTouchEvent(self, event):
        if not(self.__screenController.getFadingStatus()):
            for button in self.__buttons:
                if button.handleTouchEvent(event):
                    return True
        return super().handleTouchEvent(event)
