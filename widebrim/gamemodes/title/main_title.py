from typing import List, Union
from widebrim.engine.anim.image_anim.image import AnimatedImageObject
from widebrim.engine.anim.button import AnimatedButton
from ...engine_ext.utils import getBottomScreenAnimFromPath, getButtonFromPath
from ...engine_ext.utils import getImageFromPath
from .const import PATH_ANIM_SENRO, PATH_ANIM_TRAIN, PATH_ANIM_WAKU, PATH_BG_TITLE, PATH_BUTTON_NEW_GAME, PATH_BUTTON_CONTINUE, PATH_BUTTON_BONUS
from ...engine.const import RESOLUTION_NINTENDO_DS
from ...engine.state.layer import ScreenLayerNonBlocking
from ...engine.state.enum_mode import GAMEMODES

class TitlePlayerBottomScreenOverlay(ScreenLayerNonBlocking):
    def __init__(self, laytonState, screenController, saveData, routineTitleScreen, routineContinue, routineBonus, routineTerminate):
        ScreenLayerNonBlocking.__init__(self)
        self.screenController = screenController
        self.laytonState = laytonState

class MenuScreen(TitlePlayerBottomScreenOverlay):

    ANIM_TRAIN      : AnimatedImageObject = None
    ANIM_SENRO      : AnimatedImageObject = None
    ANIM_WAKU       : AnimatedImageObject = None
    BUTTON_NEW      = None
    BUTTON_CONT     = None
    BUTTON_BONUS    = None

    BACKGROUND_SPEED_MULTIPLIER = 0.0666
    BACKGROUND_SPEED_MULTIPLIER = 2/30
    FOREGROUND_SPEED_MULTIPLIER = 1/5

    def __init__(self, laytonState, screenController, saveData, routineTitleScreen, routineContinue, routineBonus, routineTerminate):
        TitlePlayerBottomScreenOverlay.__init__(self, laytonState, screenController, saveData, routineTitleScreen, routineContinue, routineBonus, routineTerminate)
        screenController.setBgMain(PATH_BG_TITLE)

        if MenuScreen.ANIM_TRAIN == None:
            MenuScreen.ANIM_TRAIN = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_TRAIN)
        if MenuScreen.ANIM_SENRO == None:
            MenuScreen.ANIM_SENRO = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_SENRO)
        if MenuScreen.ANIM_WAKU == None:
            MenuScreen.ANIM_WAKU = getBottomScreenAnimFromPath(laytonState, PATH_ANIM_WAKU)

        self.__drawables : List[Union[AnimatedButton, AnimatedImageObject]] = []

        def addIfNotNone(item : Union[AnimatedButton, AnimatedImageObject]):
            if item != None:
                self.__drawables.append(item)

        self.background = getImageFromPath(laytonState, PATH_BG_TITLE)
        self.backgroundX = 0
        if MenuScreen.ANIM_SENRO != None:
            self.senroX = MenuScreen.ANIM_SENRO.getPos()[0]
        else:
            self.senroX = 0

        screenController.fadeInMain()

        self.routineTerminate = routineTerminate
        self.routineContinue = routineContinue
        self.routineBonus = routineBonus
        self.isActive = False
        for slotIndex in range(3):
            self.isActive = self.isActive or saveData.getSlotData(slotIndex).isActive
        
        def callbackOnNewGame():
            self.laytonState.setGameMode(GAMEMODES.Name)
            self.routineTerminate()

        # TODO - Remake this (change positions, callbacks, etc) to prevent button reloading as this creates a visible stall
        MenuScreen.BUTTON_CONT = getButtonFromPath(laytonState, PATH_BUTTON_CONTINUE, callback=routineContinue)
        MenuScreen.BUTTON_BONUS = getButtonFromPath(laytonState, PATH_BUTTON_BONUS, callback=routineBonus)
        if self.isActive:
            MenuScreen.BUTTON_NEW = getButtonFromPath(laytonState, PATH_BUTTON_NEW_GAME, callback=callbackOnNewGame)
        else:
            MenuScreen.BUTTON_NEW = getButtonFromPath(laytonState, PATH_BUTTON_NEW_GAME, namePosVariable="pos2", callback=callbackOnNewGame)
        
        addIfNotNone(MenuScreen.ANIM_TRAIN)
        addIfNotNone(MenuScreen.ANIM_WAKU)
        if self.isActive:
            addIfNotNone(MenuScreen.BUTTON_BONUS)
            addIfNotNone(MenuScreen.BUTTON_CONT)
        addIfNotNone(MenuScreen.BUTTON_NEW)
    
    def update(self, gameClockDelta):

        self.backgroundX    = (self.backgroundX + gameClockDelta * MenuScreen.BACKGROUND_SPEED_MULTIPLIER) % RESOLUTION_NINTENDO_DS[0]
        self.senroX         = (self.senroX + gameClockDelta * MenuScreen.FOREGROUND_SPEED_MULTIPLIER) % RESOLUTION_NINTENDO_DS[0]

        if MenuScreen.ANIM_SENRO != None:
            MenuScreen.ANIM_SENRO.update(gameClockDelta)

        for drawable in self.__drawables:
            drawable.update(gameClockDelta)

    def draw(self, gameDisplay):

        if self.background != None:
            gameDisplay.blit(self.background, (self.backgroundX, RESOLUTION_NINTENDO_DS[1]))
            gameDisplay.blit(self.background, (self.backgroundX - self.background.get_width(), RESOLUTION_NINTENDO_DS[1]))

        # TODO - What happens with subanimations? Maybe safer to change position each time.
        if MenuScreen.ANIM_SENRO != None and MenuScreen.ANIM_SENRO.getActiveFrame() != None:
            gameDisplay.blit(MenuScreen.ANIM_SENRO.getActiveFrame(), (self.senroX, MenuScreen.ANIM_SENRO.getPos()[1]))
            gameDisplay.blit(MenuScreen.ANIM_SENRO.getActiveFrame(), (self.senroX - RESOLUTION_NINTENDO_DS[0], MenuScreen.ANIM_SENRO.getPos()[1]))

        for drawable in self.__drawables:
            drawable.draw(gameDisplay)

    def handleTouchEvent(self, event):
        for button in self.__drawables:
            if type(button) == AnimatedButton:
                if button.handleTouchEvent(event):
                    return True
        return super().handleTouchEvent(event)