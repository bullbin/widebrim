from typing import List

from widebrim.madhatter.common import log

from ...engine.anim.font.static import generateImageFromString
from ...engine.anim.button import NullButton
from ...engine.config import PATH_SAVE
from ...engine.const import PATH_TEXT_GENERIC, PATH_PACK_PLACE_NAME, PATH_TEXT_PLACE_NAME, RESOLUTION_NINTENDO_DS
from ...engine_ext.utils import getButtonFromPath, getTxt2String
from ...madhatter.hat_io.asset_sav import Layton2SaveFile

from .const import COLOR_SLOT_B, COLOR_SLOT_G, COLOR_SLOT_R, COLOR_UNUSED_SLOT, OFFSET_Y_SLOT_0, PATH_BG_FILELOAD, PATH_BG_FILESAVE, PATH_ANI_BTN_BACK, ID_SAVE_EMPTY, POS_TOP_SLOT_Y
from .utils import MainScreenPopup

from pygame import Surface, BLEND_RGB_SUB

# TODO - Bugfix, buttons can be pressed during fading operation
# TODO - Needs rewrite...

from widebrim.engine.state.manager.state import Layton2GameState

class SaveLoadScreenPopup(MainScreenPopup):

    MODE_SAVE = 0
    MODE_LOAD = 1

    # All values from ROM
    OFFSET_BOTTOM_TEXT  = 0x39
    OFFSET_MIDDLE_TEXT  = 0x2f
    OFFSET_TOP_TEXT     = 0x25

    OFFSET_X_EMPTY_TEXT = 0x8a
    OFFSET_X_BOX_TEXT   = 0x5b
    
    OFFSET_X_SLOT_START = 0x03
    OFFSET_X_SLOT_END   = 0xfa

    OFFSET_Y_SLOT_START = 0x1f

    STRIDE_BOX          = 0x2e
    HEIGHT_SLOT         = 0x2b

    def __init__(self, laytonState : Layton2GameState, screenController, mode, bgIndex, callbackOnTerminate, callbackOnSlot):
        MainScreenPopup.__init__(self, callbackOnTerminate)

        self.saveData = Layton2SaveFile()
        try:
            with open(PATH_SAVE, 'rb') as saveIn:
                if not(self.saveData.load(saveIn.read())):
                    self.saveData = Layton2SaveFile()
        except FileNotFoundError:
            pass

        self.surfaceName    = [None, None, None]
        self.surfacePlace   = [None, None, None]
        self.surfaceNameX   = [0,0,0]
        self.surfacePlaceX   = [0,0,0]
        self.surfaceUnused : Surface = Surface((0xdd,0x25))
        self.surfaceUnused.fill(COLOR_UNUSED_SLOT)
        self.surfaceNameTag : List[Surface] = []
        for r,g,b in zip(COLOR_SLOT_R, COLOR_SLOT_G, COLOR_SLOT_B):
            self.surfaceNameTag.append(Surface((0x79,0x11)))
            self.surfaceNameTag[-1].fill((r,g,b))

        self.slotButtons = []
        self.slotIndexSlot = []
        self.slotActive = None

        # TODO - Support saving, which has a popup with the overwrite screen

        def writeSaveData():
            # TODO - Centralise a way to get the save path, which can currently be destroyed by the launcher
            self.saveData.save()
            try:
                self.saveData.export(PATH_SAVE)
                return True
            except IOError:
                return False

        def callbackOnSlotAccessed():
            if mode == SaveLoadScreenPopup.MODE_LOAD:
                laytonState.timeStartTimer()
                laytonState.saveSlot = self.saveData.getSlotData(self.slotActive)
                laytonState.wiFiData = self.saveData.getWiFiData()
            else:
                laytonState.timeUpdateStoredTime()
                # TODO - When is the save slot made active?
                laytonState.saveSlot.isActive = True
                self.saveData.setSlotData(self.slotActive, laytonState.saveSlot)
                self.saveData.setWiFiData(laytonState.wiFiData)
                writeSaveData()
                generateGraphicsForIndex(self.slotActive)
                log("Overwrote save slot " + str(self.slotActive) + "!", name="FsSave")

                # TODO - Draw save logo like game before starting write operation

            callbackOnSlot()

        try:
            self.surfaceEmpty = generateImageFromString(laytonState.fontEvent, getTxt2String(laytonState, PATH_TEXT_GENERIC % ID_SAVE_EMPTY))
        except:
            self.surfaceEmpty = Surface((0,0))
        
        self.surfaceEmptyX = (SaveLoadScreenPopup.OFFSET_X_EMPTY_TEXT - self.surfaceEmpty.get_width() // 2)
        
        def generateGraphicsForIndex(indexSlot):
            try:
                indexPlace = self.saveData.getSlotData(indexSlot).roomIndex
                if indexPlace == 0x5c:
                    indexPlace = 0x26
                # TODO - Decode...?
                self.surfacePlace[indexSlot] = generateImageFromString(laytonState.fontQ, laytonState.getFileAccessor().getPackedString(PATH_PACK_PLACE_NAME % laytonState.language.value, PATH_TEXT_PLACE_NAME % indexPlace))
                self.surfacePlaceX[indexSlot] = SaveLoadScreenPopup.OFFSET_X_BOX_TEXT - self.surfacePlace[indexSlot].get_width() // 2
            except:
                pass

            self.surfaceName[indexSlot] = generateImageFromString(laytonState.fontEvent, saveSlot.name)
            self.surfaceNameX[indexSlot] = SaveLoadScreenPopup.OFFSET_X_BOX_TEXT - self.surfaceName[indexSlot].get_width() // 2

        for indexSlot in range(3):
            saveSlot = self.saveData.getSlotData(indexSlot)
            if saveSlot.isActive:
                
                generateGraphicsForIndex(indexSlot)

                self.slotButtons.append(NullButton((SaveLoadScreenPopup.OFFSET_X_SLOT_START, SaveLoadScreenPopup.OFFSET_Y_SLOT_START + RESOLUTION_NINTENDO_DS[1] + (SaveLoadScreenPopup.STRIDE_BOX * indexSlot)),
                                                    (SaveLoadScreenPopup.OFFSET_X_SLOT_END,
                                                    SaveLoadScreenPopup.OFFSET_Y_SLOT_START + RESOLUTION_NINTENDO_DS[1] + SaveLoadScreenPopup.HEIGHT_SLOT + (SaveLoadScreenPopup.STRIDE_BOX * indexSlot)),
                                                    callback=callbackOnSlotAccessed))

            elif mode == SaveLoadScreenPopup.MODE_SAVE:
                # Always add a button if in save menu, since empty slots can be overwritten
                self.slotButtons.append(NullButton((SaveLoadScreenPopup.OFFSET_X_SLOT_START, SaveLoadScreenPopup.OFFSET_Y_SLOT_START + RESOLUTION_NINTENDO_DS[1] + (SaveLoadScreenPopup.STRIDE_BOX * indexSlot)),
                                (SaveLoadScreenPopup.OFFSET_X_SLOT_END,
                                SaveLoadScreenPopup.OFFSET_Y_SLOT_START + RESOLUTION_NINTENDO_DS[1] + SaveLoadScreenPopup.HEIGHT_SLOT + (SaveLoadScreenPopup.STRIDE_BOX * indexSlot)),
                                callback=callbackOnSlotAccessed))
            self.slotIndexSlot.append(indexSlot)
                
        self.buttonBack = getButtonFromPath(laytonState, PATH_ANI_BTN_BACK, callback=callbackOnTerminate) 

        if mode == SaveLoadScreenPopup.MODE_LOAD:
            screenController.setBgMain(PATH_BG_FILELOAD % (laytonState.language.value, bgIndex + 1))
        else:
            screenController.setBgMain(PATH_BG_FILESAVE % (laytonState.language.value))

        screenController.fadeInMain()
    
    def draw(self, gameDisplay):
        self.buttonBack.draw(gameDisplay)

        offsetBottom    = SaveLoadScreenPopup.OFFSET_BOTTOM_TEXT + RESOLUTION_NINTENDO_DS[1]
        offsetMiddle    = SaveLoadScreenPopup.OFFSET_MIDDLE_TEXT + RESOLUTION_NINTENDO_DS[1]
        offsetTop       = SaveLoadScreenPopup.OFFSET_TOP_TEXT + RESOLUTION_NINTENDO_DS[1]
        offsetSlot      = POS_TOP_SLOT_Y + RESOLUTION_NINTENDO_DS[1]

        for indexSlot in range(3):
            if self.saveData.getSlotData(indexSlot).isActive:
                gameDisplay.blit(self.surfaceNameTag[indexSlot], (0x1d, offsetSlot))
            else:
                gameDisplay.blit(self.surfaceUnused, (0x1d, offsetSlot))
            offsetSlot += OFFSET_Y_SLOT_0

            if self.saveData.getSlotData(indexSlot).isActive and self.surfaceName[indexSlot] != None:
                gameDisplay.blit(self.surfaceName[indexSlot], (self.surfaceNameX[indexSlot], offsetTop), special_flags=BLEND_RGB_SUB)
                if self.surfacePlace[indexSlot] != None:
                    gameDisplay.blit(self.surfacePlace[indexSlot], (self.surfacePlaceX[indexSlot], offsetBottom), special_flags=BLEND_RGB_SUB)
            else:
                gameDisplay.blit(self.surfaceEmpty, (self.surfaceEmptyX, offsetMiddle), special_flags=BLEND_RGB_SUB)
            
            offsetBottom += SaveLoadScreenPopup.STRIDE_BOX
            offsetMiddle += SaveLoadScreenPopup.STRIDE_BOX
            offsetTop += SaveLoadScreenPopup.STRIDE_BOX
    
    def update(self, gameClockDelta):
        self.buttonBack.update(gameClockDelta)
    
    def handleTouchEvent(self, event):
        self.buttonBack.handleTouchEvent(event)
        for indexButton, slot in enumerate(self.slotButtons):
            self.slotActive = self.slotIndexSlot[indexButton]
            slot.handleTouchEvent(event)