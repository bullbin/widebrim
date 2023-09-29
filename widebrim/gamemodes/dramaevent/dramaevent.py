from __future__ import annotations
from typing import Callable, Dict, List, Optional, TYPE_CHECKING, Union
from widebrim.engine.string.cmp import strCmp
from widebrim.engine_ext.const import SHAKE_PIX
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
from widebrim.gamemodes.dramaevent.popup.utils import FadingPopupAnimBackground, FadingPopupMultipleAnimBackground
from widebrim.engine_ext.utils import getBottomScreenAnimFromPath, getTxt2String
from widebrim.madhatter.hat_io.asset import LaytonPack
from widebrim.madhatter.hat_io.asset_dat.event import EventData
if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController
    from widebrim.engine.anim.image_anim.image import AnimatedImageObjectWithSubAnimation

from widebrim.gamemodes.mystery import MysteryPlayer

from ...engine.state.enum_mode import GAMEMODES
from ...engine.anim.fader import Fader
from ...engine.anim.font.scrolling import ScrollingFontHelper
from ...engine.exceptions import FileInvalidCritical
from ..core_popup.script import ScriptPlayer

from ...engine.const import PATH_EVENT_BG_LANG_DEP, PATH_TEXT_GENERIC, PATH_TEXT_PURPOSE, RESOLUTION_NINTENDO_DS, PATH_CHAP_ROOT
from ...engine.const import PATH_EVENT_SCRIPT, PATH_EVENT_SCRIPT_A, PATH_EVENT_SCRIPT_B, PATH_EVENT_SCRIPT_C, PATH_EVENT_TALK, PATH_EVENT_TALK_A, PATH_EVENT_TALK_B, PATH_EVENT_TALK_C
from ...engine.const import PATH_PACK_EVENT_DAT, PATH_PACK_EVENT_SCR, PATH_PACK_TALK, PATH_EVENT_BG, PATH_PLACE_BG, PATH_EVENT_ROOT, PATH_NAME_ROOT

from ...madhatter.hat_io.asset_script import GdScript
from ...madhatter.hat_io.asset_sav import FlagsAsArray
from ...madhatter.typewriter.strings_lt2 import OPCODES_LT2

from .storage import EventStorage
from .popup import *
from ..core_popup.save import SaveLoadScreenPopup

from .const import *

from widebrim.madhatter.common import logSevere, logVerbose

from pygame import Surface, MOUSEBUTTONUP, event
from pygame.transform import flip
from random import randint

# TODO - During fading, the main screen doesn't actually seem to be updated.

# TODO - Set up preparations for many hardcoded event IDs which are called for various tasks in binary
#        aka nazoba hell, since there's so much back and forth to spawn the extra handler due to memory constraints on NDS

class TextWindow(FadingPopupMultipleAnimBackground):

    DICT_SLOTS = {0:"LEFT",
                  2:"RIGHT",
                  3:"LEFT_L",
                  4:"LEFT_R",
                  5:"RIGHT_L",
                  6:"RIGHT_R"}
    spriteWindow : Optional[AnimatedImageObjectWithSubAnimation] = None

    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController, text : str, targetCharacter : Optional[CharacterController], animNameOnSpawn : Optional[str] = None, animNameOnExit : Optional[str] = None, funcSetAni : Optional[Callable[[int, str], None]] = None, callbackOnTerminate : Optional[Callable] = None):
        
        if TextWindow.spriteWindow == None:
            TextWindow.spriteWindow = getBottomScreenAnimFromPath(laytonState, PATH_EVENT_ROOT % "twindow.arc", enableSubAnimation=True)

        self.__textScroller = ScrollingFontHelper(laytonState.fontEvent)
        self.__textScroller.setText(text)
        self.__textScroller.setPos((8, RESOLUTION_NINTENDO_DS[1] + 141))
        self.__textScroller.setFunctionSetAnimation(funcSetAni)

        self.__animNameOnExit = animNameOnExit
        self.__targetCharacter = targetCharacter

        TextWindow.spriteWindow.setAnimationFromIndex(1)

        bgAnims = [TextWindow.spriteWindow]
        if targetCharacter != None:
            bgAnims.insert(0, targetCharacter.imageName)
            if animNameOnSpawn != None:
                targetCharacter.setCharacterAnimationFromName(animNameOnSpawn)
            if targetCharacter.slot in TextWindow.DICT_SLOTS and targetCharacter.getVisibility():
                TextWindow.spriteWindow.setAnimationFromName(TextWindow.DICT_SLOTS[targetCharacter.slot])

        super().__init__(laytonState, screenController, callbackOnTerminate, bgAnims)
    
    def updateForegroundElements(self, gameClockDelta):
        self.__textScroller.update(gameClockDelta)
        if self.__targetCharacter != None:
            if self.__textScroller.isWaiting() or not(self.__textScroller.getActiveState()):
                self.__targetCharacter.setCharacterTalkingState(False)
            else:
                self.__targetCharacter.setCharacterTalkingState(True)
        return super().updateForegroundElements(gameClockDelta)
    
    def drawForegroundElements(self, gameDisplay):
        self.__textScroller.draw(gameDisplay)
        return super().drawForegroundElements(gameDisplay)

    def startTerminateBehaviour(self):
        # TODO - When is character end anim applied?
        if self.__targetCharacter != None:
            self.__targetCharacter.setCharacterTalkingState(False)
            if self.__animNameOnExit != None:
                self.__targetCharacter.setCharacterAnimationFromName(self.__animNameOnExit)
        return super().startTerminateBehaviour()

    def handleTouchEventForegroundElements(self, event : event):
        if self.__textScroller.getActiveState():
            if event.type == MOUSEBUTTONUP:
                if not(self.__textScroller.isWaiting()):
                    self.__textScroller.skip()
                else:
                    self.__textScroller.setTap()
            return True
        return False

class MokutekiWindow(FadingPopupAnimBackground):

    # TODO - Timings are known for anim, cursor_wait, etc. Uses tm_def for aligned timing. Is this using TextWindow base (eg can span multiple pages)?

    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController, text : str, callbackOnTerminate : Optional[Callable]):
        super().__init__(laytonState, screenController, callbackOnTerminate, getBottomScreenAnimFromPath(laytonState, PATH_MOKUTEKI_WINDOW))
        self.__text = StaticTextHelper(laytonState.fontEvent)
        self.__text.setText(text)
        self.__text.setPos((POS_MOKUTEKI_TEXT[0], POS_MOKUTEKI_TEXT[1] + RESOLUTION_NINTENDO_DS[1]))

    def drawForegroundElements(self, gameDisplay):
        self.__text.draw(gameDisplay)

class CharacterController():

    # Verified against game binary
    SLOT_OFFSET = {0:0x30,     1:0x80,
                   2:0xd0,     3:0x20,
                   4:0x58,     5:0xa7,
                   6:0xe0}
    SLOT_LEFT  = [0,3,4]    # Left side characters need flipping
    SLOT_RIGHT = [2,5,6]

    def __init__(self, laytonState, characterIndex, characterInitialAnimIndex=0, characterVisible=False, characterSlot=0):

        self._baseAnimIndex = None
        self._isCharacterTalking = False

        if characterIndex == 86 or characterIndex == 87:
            self.imageCharacter = getBottomScreenAnimFromPath(laytonState, (PATH_BODY_ROOT_LANG_DEP % characterIndex), enableSubAnimation=True)
        else:
            self.imageCharacter = getBottomScreenAnimFromPath(laytonState, PATH_BODY_ROOT % characterIndex, enableSubAnimation=True)

        if self.imageCharacter != None:
            self.setCharacterAnimationFromIndex(characterInitialAnimIndex)
            self.imageCharacter.setPos((0,0))

        self.imageName = getBottomScreenAnimFromPath(laytonState, PATH_NAME_ROOT % (laytonState.language.value, characterIndex))

        self._visibilityFader = Fader(0, initialActiveState=True)
        self._shakeFader      = Fader(0, initialActiveState=False)
        self._drawLocation = (0,0)

        self._characterIsFlipped = False
        if self.imageCharacter != None:
            self._characterFlippedSurface = Surface(self.imageCharacter.getDimensions()).convert_alpha()
        else:
            self._characterFlippedSurface = Surface((0,0))
        self._characterFlippedSurfaceNeedsUpdate = True
        
        self.slot = 0
        self.setCharacterSlot(characterSlot)
        self.setVisibility(characterVisible)

    def update(self, gameClockDelta):
        if self.imageCharacter != None:
            if self.imageCharacter.update(gameClockDelta) or self._characterFlippedSurfaceNeedsUpdate:
                self._characterFlippedSurface.fill((0,0,0,0))
                self.imageCharacter.setAlpha(round(255 * self._visibilityFader.getStrength()))
                self.imageCharacter.draw(self._characterFlippedSurface)
                if self._characterIsFlipped:
                    self._characterFlippedSurface = flip(self._characterFlippedSurface, True, False)
            
        self._visibilityFader.update(gameClockDelta)
        self._shakeFader.update(gameClockDelta)

    def draw(self, gameDisplay):
        if self.getVisibility() and self.imageCharacter != None:
            if self._shakeFader.getActiveState():
                # HACK - Screen isn't clipped for speed sake
                gameDisplay.blit(self._characterFlippedSurface, (self._drawLocation[0] + randint(-SHAKE_PIX,SHAKE_PIX), self._drawLocation[1] + randint(-SHAKE_PIX,SHAKE_PIX)))
            else:
                gameDisplay.blit(self._characterFlippedSurface, self._drawLocation)

    def setVisibility(self, isVisible):
        self._visibilityFader.setDuration(0)
        self._visibilityFader.setInvertedState(not(isVisible))
    
    def setVisibilityFading(self, isVisible, callback, durationInFrames=15):
        self._visibilityFader.setDurationInFrames(durationInFrames)
        self._visibilityFader.setCallback(callback)
        self._visibilityFader.setInvertedState(not(isVisible))

    def getVisibility(self):
        return self._visibilityFader.getStrength() > 0
    
    def setShakeDuration(self, durationInFrames):
        self._shakeFader.setDurationInFrames(durationInFrames)

    def _updateCharacterTalkState(self):
        if self.imageCharacter != None:
            if self._isCharacterTalking:
                if self.imageCharacter.doesTalkAnimExistForCurrentAnim():
                    self.imageCharacter.setAnimationFromIndex(self._baseAnimIndex + 1)
            else:
                self.imageCharacter.setAnimationFromIndex(self._baseAnimIndex)

    def setCharacterTalkingState(self, isTalking):
        if isTalking != self._isCharacterTalking:
            self._isCharacterTalking = isTalking
            self._updateCharacterTalkState()

    def setCharacterSlot(self, slot):
        def getImageOffset():
            offset = self.imageCharacter.getVariable("drawoff")
            if offset != None:
                return (offset[0], abs(offset[1]))
            else:
                return (0,0)

        if slot in CharacterController.SLOT_OFFSET:
            self.slot = slot

            if self.imageCharacter != None:
                offset = CharacterController.SLOT_OFFSET[self.slot]
                variableOffset = getImageOffset()

                if slot in CharacterController.SLOT_LEFT:
                    self._characterIsFlipped = True
                    self._drawLocation = (offset - (self.imageCharacter.getDimensions()[0] // 2) - variableOffset[0],
                                      RESOLUTION_NINTENDO_DS[1] * 2 - variableOffset[1] - self.imageCharacter.getDimensions()[1])
                else:
                    self._characterIsFlipped = False
                    self._drawLocation = (offset - (self.imageCharacter.getDimensions()[0] // 2) + variableOffset[0],
                                      RESOLUTION_NINTENDO_DS[1] * 2 - variableOffset[1] - self.imageCharacter.getDimensions()[1])
                
                self._characterFlippedSurfaceNeedsUpdate = True

    def setCharacterAnimationFromName(self, animName : str):
        if self.imageCharacter != None:
            activeAnimName = self.imageCharacter.getAnimationName()
            if activeAnimName == None or not(strCmp(activeAnimName, animName)):
                newIndex = self.imageCharacter.getAnimationIndexIfNameIsValid(animName)
                if newIndex != None:
                    self.setCharacterAnimationFromIndex(newIndex)
    
    def setCharacterAnimationFromIndex(self, animIndex):
        if self.imageCharacter != None:
            if self._baseAnimIndex != animIndex and animIndex != 0 and self.imageCharacter.isAnimationIndexValid(animIndex):
                self._baseAnimIndex = animIndex
                self._updateCharacterTalkState()

class EventPlayer(ScriptPlayer):
    def __init__(self, laytonState : Layton2GameState, screenController, overrideId : Optional[int] = None):

        def substituteEventPath(inPath, inPathA, inPathB, inPathC):

            def trySubstitute(path, lang, evId):
                try:
                    return path % (lang, evId)
                except TypeError:
                    return path % evId

            if self._idMain != 24:
                return trySubstitute(inPath, self.laytonState.language.value, self._idMain)
            elif self._idSub < 300:
                return trySubstitute(inPathA, self.laytonState.language.value, self._idMain)
            elif self._idSub < 600:
                return trySubstitute(inPathB, self.laytonState.language.value, self._idMain)
            else:
                return trySubstitute(inPathC, self.laytonState.language.value, self._idMain)

        def getEventTalkPath():
            return substituteEventPath(PATH_EVENT_TALK, PATH_EVENT_TALK_A, PATH_EVENT_TALK_B, PATH_EVENT_TALK_C)

        def getEventScriptPath():
            return substituteEventPath(PATH_EVENT_SCRIPT, PATH_EVENT_SCRIPT_A, PATH_EVENT_SCRIPT_B, PATH_EVENT_SCRIPT_C)

        ScriptPlayer.__init__(self, laytonState, screenController, GdScript())

        # TODO - Type checking
        self.laytonState.setGameMode(GAMEMODES.Room)
        self._packEventTalk : Optional[LaytonPack] = None

        if overrideId != None:
            spawnId = overrideId
        else:
            spawnId = self.laytonState.getEventId()
        
        # EndPuzzle workaround causes invalidation to happen too early for event info...
        # TODO - Think this through
        spawnEventData = self.laytonState.getEventInfoEntry(spawnId)

        self._id = spawnId
        self._idMain = spawnId // 1000
        self._idSub = spawnId % 1000

        self.talkScript     = GdScript()

        self.characters : List[CharacterController] = []
        self.nameCharacters = []
        self.characterSpawnIdToCharacterMap : Dict[int, CharacterController] = {}

        self._sharedImageHandler = EventStorage(laytonState)

        self._doGoalSet = True

        if spawnId == -1:
            self.doOnKill()
        else:
            logVerbose("Started event", spawnId, name="DramaEvent")
            # Centralise this so it can be deleted when finished
            try:
                packEventScript = self.laytonState.getFileAccessor().getPack(getEventScriptPath())
                self._packEventTalk = self.laytonState.getFileAccessor().getPack(getEventTalkPath())

                eventData = EventData()

                if (data := packEventScript.getFile(PATH_PACK_EVENT_DAT % (self._idMain, self._idSub))) != None:
                    eventData.load(data)
                else:
                    raise FileInvalidCritical()

                # Event_MaybeLoadEvent
                # Wants to set gamemode to puzzle, but this is overriden by setting to room. Done in different functions in game but both run during event
                if ID_EVENT_PUZZLE <= spawnId < ID_EVENT_TEA and spawnEventData != None and spawnEventData.dataPuzzle != None:
                    self.laytonState.setPuzzleId(spawnEventData.dataPuzzle)
                    self.laytonState.setGameModeNext(GAMEMODES.EndPuzzle)
                
                if spawnEventData != None and spawnEventData.indexEventViewedFlag != None:
                    self.laytonState.saveSlot.eventViewed.setSlot(True, spawnEventData.indexEventViewedFlag)

                self._loadEventAndScriptData(packEventScript.getFile(PATH_PACK_EVENT_SCR % (self._idMain, self._idSub)), eventData)

            except TypeError:
                logSevere("Failed to catch script data for event!", name="DramaEvent")
                self.doOnKill()
            except FileInvalidCritical:
                logSevere("Failed to fetch required data for event!", name="DramaEvent")
                self.doOnKill()
    
    def _loadEventAndScriptData(self, script : Union[GdScript, bytes], data : EventData):
        if type(script) == GdScript:
            self._script = script
        else:
            self._script.load(script)

        self.screenController.setBgMain(PATH_PLACE_BG % data.mapBsId)
        if 0x32 <= data.mapTsId <= 0x36:
            self.screenController.setBgSub(PATH_EVENT_BG_LANG_DEP % data.mapTsId)
        else:
            self.screenController.setBgSub(PATH_EVENT_BG % data.mapTsId)

        # TODO - Remove this to populate event data structure
        # 1 - Nothing
        # 2 - Fade in main screen
        # 3, 0 - Fade in both screens and modify main palette
        # else - Fade in both screens
        # There is another check for customSoundSet != 2 and behaviour != 3 but this is sound-related
        # customSoundSet != 1 means fade out on exit...

        introBehaviour = data.behaviour
        if introBehaviour == 0 or introBehaviour == 3:
            self.screenController.modifyPaletteMain(120)
        
        if introBehaviour != 1 and introBehaviour != 2:
            self.screenController.fadeIn()
        if introBehaviour == 2:
            self.screenController.fadeInMain()

        # TODO - MaybeLoadCharactersFromData - language specific and boundary checks
        for charIndex, character in enumerate(data.characters):
            if character != 0:
                self.characters.append(CharacterController(self.laytonState, character))
                self.characterSpawnIdToCharacterMap[character] = self.characters[-1]

        for charIndex, slot in enumerate(data.charactersPosition):
            if charIndex < len(self.characters):
                self.characters[charIndex].setCharacterSlot(slot)

        for charIndex, visibility in enumerate(data.charactersShown):
            if charIndex < len(self.characters):
                self.characters[charIndex].setVisibility(visibility)
        
        for charIndex, animIndex in enumerate(data.charactersInitialAnimationIndex):
            if charIndex < len(self.characters):
                self.characters[charIndex].setCharacterAnimationFromIndex(animIndex)

    def doOnComplete(self):
        if self._doGoalSet:
            self.laytonState.loadGoalInfoDb()
            goalInfoEntry = self.laytonState.getGoalInfEntry(self._id)
            self.laytonState.unloadGoalInfoDb()
            if goalInfoEntry != None:
                self._makeActive()
                self.laytonState.saveSlot.goal = goalInfoEntry.goal
                self._doGoalSet = False
                if self.__doMokutekiWindow(goalInfoEntry.type, goalInfoEntry.goal):
                    return
        super().doOnComplete()

    def doOnKill(self):
        # TODO - Research more into next handler. What happens if the next gamemode is set in chapter event? Or normal gamemode?
        # When reaching a forced save screen, will this force the event to run twice? Perhaps hitting no on the question to save invalidates this event.

        # According to research, this event should run first, destroying the event currently queued to play. But playing the game, the chapter event plays first.
        # Why is this the case?
        if self.laytonState.saveSlot.idImmediateEvent != -1:
            self.laytonState.setEventId(self.laytonState.saveSlot.idImmediateEvent)
            self.laytonState.setGameMode(GAMEMODES.DramaEvent)
            self.laytonState.saveSlot.idImmediateEvent = -1
        super().doOnKill()

    def draw(self, gameDisplay):
        for controller in self.characters:
            controller.draw(gameDisplay)
        super().draw(gameDisplay)

    def update(self, gameClockDelta):
        for controller in self.characters:
            controller.update(gameClockDelta)

        super().update(gameClockDelta)

    def __doMokutekiWindow(self, doPopup : int, objective : int) -> bool:
        if doPopup != 0:
            text = ""
            if type(objective) == int:
                text = getTxt2String(self.laytonState, PATH_TEXT_PURPOSE % objective)
            
            # TODO - Strange mid-file checks here to see if some flags met. Affects timing and audio, not game state
            self._popup = MokutekiWindow(self.laytonState, self.screenController, text, callbackOnTerminate=self._makeActive)
            self._makeInactive()
            return True
        return False

    def __setAniCallback(self, idChar : int, nameAnim : str):
        if idChar in self.characterSpawnIdToCharacterMap:
            self.characterSpawnIdToCharacterMap[idChar].setCharacterAnimationFromName(nameAnim)

    def _spriteOffAllCharacters(self):
        # TODO - Not a good hack! If a fader doesn't need to activate, this can be called immediately, breaking the order of execution!
        for character in self.characters:
            character.setVisibility(False)
        self._makeActive()

    def _doUnpackedCommand(self, opcode, operands):

        def isCharacterSlotValid(indexSlot):
            if type(indexSlot) == int and 0 <= indexSlot <= 7:
                if indexSlot < len(self.characters):
                    return True
            return False

        if opcode == OPCODES_LT2.TextWindow.value:
            targetController = None
            animNameOn = None
            animNameOff = None
            text = ""

            # No need to check for None, script can't execute without this loading
            tempTalkScript = self._packEventTalk.getFile(PATH_PACK_TALK % (self._idMain, self._idSub, operands[0].value))
            if tempTalkScript != None:
                self.talkScript = GdScript()
                self.talkScript.load(tempTalkScript, isTalkscript=True)

                # Game doesn't 'verify' data but broken scripts would inherit operands from previous scripts. Not feasible here

                if self.talkScript.getInstructionCount() >= 1 and len(self.talkScript.getInstruction(0).operands) >= 5:
                    if self.talkScript.getInstruction(0).operands[0].value in self.characterSpawnIdToCharacterMap:
                        targetController = self.characterSpawnIdToCharacterMap[self.talkScript.getInstruction(0).operands[0].value]
                    if self.talkScript.getInstruction(0).operands[1].value != "NONE" and type(self.talkScript.getInstruction(0).operands[1].value) == str:
                        animNameOn = self.talkScript.getInstruction(0).operands[1].value
                    if self.talkScript.getInstruction(0).operands[2].value != "NONE" and type(self.talkScript.getInstruction(0).operands[2].value) == str:
                        animNameOff = self.talkScript.getInstruction(0).operands[2].value
                    
                    # Operand 3 is the text voice
                    
                    if type(self.talkScript.getInstruction(0).operands[4].value) == str:
                        text = self.talkScript.getInstruction(0).operands[4].value

            else:
                # Game will execute command regardless, but window will inherit bad string data from central buffer. Not feasible but can mostly replicate.

                logSevere("\tTalk script missing!", PATH_PACK_TALK % (self._idMain, self._idSub, operands[0].value), name="DramaEvent")
            
            self._popup = TextWindow(self.laytonState, self.screenController, text, targetController, animNameOnSpawn=animNameOn, animNameOnExit=animNameOff, funcSetAni=self.__setAniCallback, callbackOnTerminate=self._makeActive)
            self._makeInactive()

        elif opcode == OPCODES_LT2.EndingMessage.value:
            text = ""
            try:
                countSolved = self.laytonState.getCountSolvedStoryPuzzles()
                if countSolved < 100:
                    textCongrats = getTxt2String(self.laytonState, PATH_TEXT_GENERIC % ID_TEXT2_CONGRATS_SOLVED_UND_100)
                elif countSolved < 120:
                    textCongrats = getTxt2String(self.laytonState, PATH_TEXT_GENERIC % ID_TEXT2_CONGRATS_SOLVED_OVR_100)
                else:
                    textCongrats = getTxt2String(self.laytonState, PATH_TEXT_GENERIC % ID_TEXT2_CONGRATS_SOLVED_OVR_120)

                text = getTxt2String(self.laytonState, PATH_TEXT_GENERIC % ID_TEXT2_ENDING_MESSAGE) % (countSolved, textCongrats)
            except:
                pass

            self._popup = TextWindow(self.laytonState, self.screenController, text, None, callbackOnTerminate=self._makeActive)
            self._makeInactive()

        elif opcode == OPCODES_LT2.SpriteOn.value:
            if isCharacterSlotValid(operands[0].value):
                self.characters[operands[0].value].setVisibility(True)

        elif opcode == OPCODES_LT2.SpriteOff.value:
            if isCharacterSlotValid(operands[0].value):
                self.characters[operands[0].value].setVisibility(False)

        elif opcode == OPCODES_LT2.DoSpriteFade.value:

            def callbackCharacterFinishFading():
                self._makeActive()

            if isCharacterSlotValid(operands[0].value):
                # Not accurate. Duration logic not fully understood, but this works...
                customDurationInFrames = 20
                if type(operands[1].value) == int and operands[1].value != 0:
                    customDurationInFrames = (32 / abs(operands[1].value)) + 4

                self.characters[operands[0].value].setVisibilityFading(operands[1].value >= 0, callbackCharacterFinishFading, durationInFrames=customDurationInFrames)
                self._makeInactive()

        elif opcode == OPCODES_LT2.DrawChapter.value:
            
            def callbackDrawChapter():
                self._spriteOffAllCharacters()
                self.screenController.setBgMain(PATH_CHAP_ROOT % operands[0].value)
                self.screenController.fadeInMain()
                self._isWaitingForTouch = True
                self._makeInactive()

            self._makeInactive()
            self.screenController.fadeOutMain(duration=0, callback=callbackDrawChapter)
        
        elif opcode == OPCODES_LT2.SetSpritePos.value:
            if isCharacterSlotValid(operands[0].value):
                self.characters[operands[0].value].setCharacterSlot(operands[1].value)
        
        elif opcode == OPCODES_LT2.SetSpriteAnimation.value:
            if operands[0].value in self.characterSpawnIdToCharacterMap:
                self.characterSpawnIdToCharacterMap[operands[0].value].setCharacterAnimationFromName(operands[1].value)

        elif opcode == OPCODES_LT2.GameOver.value:
            # TODO - Remove const. Understand behaviour first. Plays some sound effects and stops BGM.
            def switchToReset():
                self.laytonState.setGameMode(GAMEMODES.Reset)
                self._makeActive()

            def switchToFadeOut():
                self._makeInactive()
                self.screenController.fadeOut(callback=switchToReset)
            
            self._makeInactive()
            timeEntry = self.laytonState.getTimeDefinitionEntry(0x3f1)
            if timeEntry != None:
                self._faderWait.setCallback(switchToFadeOut)
                self._faderWait.setDurationInFrames(timeEntry.countFrames)
            else:
                switchToFadeOut()

        elif opcode == OPCODES_LT2.DoHukamaruAddScreen.value:
            # TODO - Quite extreme stalling due to inefficiency loading buttons

            def switchToMystery():
                self._spriteOffAllCharacters()
                self._popup = MysteryPlayer(self.laytonState, self.screenController)
                self.laytonState.clearMysteryUnlockedIndex()

            self._makeInactive()
            self.laytonState.setMysteryUnlockedIndex(operands[0].value, False)
            self.screenController.fadeOut(callback=switchToMystery)
    
        elif opcode == OPCODES_LT2.DoSubItemAddScreen.value:
            if self.laytonState.puzzleLastReward != -1:
                # TODO - This is a hack, when is the correct image loaded?
                self._sharedImageHandler.loadItemAnimById(self.laytonState.puzzleLastReward)
                self._popup = SubItemAddPopup(self.laytonState, self.screenController, self._sharedImageHandler)

        elif opcode == OPCODES_LT2.DoStockScreen.value:
            # TODO - This will still execute even if entryNzLst was empty, right. Come up as ID 0
            if self.laytonState.entryNzList != None:
                if self.laytonState.entryNzList.idInternal != 0x87 and self.laytonState.entryNzList.idInternal != 0xcb:
                    self._popup = StockPopup(self.laytonState, self.screenController, self._sharedImageHandler)
        
        elif opcode == OPCODES_LT2.DoNazobaListScreen.value:

            def switchToNazobaList():
                for character in self.characters:
                    character.setVisibility(False)
                self._popup = NazobaListPopup(self.laytonState, self.screenController, self._makeActive, operands[0].value)
            
            self._makeInactive()
            self.screenController.fadeOut(callback=switchToNazobaList)

        elif opcode == OPCODES_LT2.DoItemAddScreen.value:
            self.laytonState.saveSlot.storyItemFlag.setSlot(True, operands[0].value)
            if operands[0].value != 2:
                self._popup = ItemAddPopup(self.laytonState, self.screenController, self._sharedImageHandler, operands[0].value)
        
        elif opcode == OPCODES_LT2.SetSubItem.value and len(operands) == 1:
            # TODO - Load correct reward window asset
            super()._doUnpackedCommand(opcode, operands)
            self._sharedImageHandler.loadItemAnimById(operands[0].value)
        
        elif opcode == OPCODES_LT2.DoSubGameAddScreen.value:
            self._popup = SubGameAddPopup(self.laytonState, self.screenController, self._sharedImageHandler, operands[0].value)
        
        elif opcode == OPCODES_LT2.DoSaveScreen.value:

            def clearPopup():
                self._popup = None
                self._spriteOffAllCharacters()

            def callbackKillPopup():
                self.screenController.fadeOut(callback=clearPopup)

            def spawnSaveScreenAndTerminateCharacters():
                self._popup = SaveLoadScreenPopup(self.laytonState, self.screenController, SaveLoadScreenPopup.MODE_SAVE, None, callbackKillPopup, callbackKillPopup)

            def switchPopupToSaveScreen():
                self.screenController.fadeOut(callback=spawnSaveScreenAndTerminateCharacters)

            self._makeInactive()

            if operands[0].value == 0:
                self.laytonState.saveSlot.chapter = COMPLETE_CHAPTER
                self.laytonState.saveSlot.storyFlag.setSlot(False, COMPLETE_STORY_FLAG)
                self.laytonState.saveSlot.roomIndex = COMPLETE_PLACE_NUM
                self.laytonState.saveSlot.idImmediateEvent = -1

                if self.laytonState.hasAllStoryPuzzlesBeenSolved() and (eventEntry := self.laytonState.getEventInfoEntry(ID_EVENT_ALL_STORY_PUZZLES_SOLVED)) != None:
                    if eventEntry.indexEventViewedFlag != None:
                        self.laytonState.saveSlot.eventViewed.setSlot(True, eventEntry.indexEventViewedFlag)
            else:
                self.laytonState.saveSlot.idImmediateEvent = operands[0].value
            
            self._popup = SaveButtonPopup(self.laytonState, self.screenController, self._sharedImageHandler, switchPopupToSaveScreen, callbackKillPopup, saveIsComplete=operands[0].value == 0)
            
        elif opcode == OPCODES_LT2.HukamaruClear.value:
            # TODO - Quite extreme stalling due to inefficiency loading buttons
            
            def switchToMystery():
                self._spriteOffAllCharacters()
                self._popup = MysteryPlayer(self.laytonState, self.screenController)
                self.laytonState.clearMysteryUnlockedIndex()

            self._makeInactive()
            self.laytonState.setMysteryUnlockedIndex(operands[0].value, True)
            self.screenController.fadeOut(callback=switchToMystery)
        
        elif opcode == OPCODES_LT2.SetSpriteShake.value and len(operands) == 2:
            if isCharacterSlotValid(operands[0].value) and type(operands[1].value) == int:
                self.characters[operands[0].value].setShakeDuration(operands[1].value)

        elif opcode == OPCODES_LT2.DoPhotoPieceAddScreen.value:
            self.laytonState.saveSlot.photoPieceFlag.setSlot(True, operands[0].value)
            photoPieceAddCounter = bytearray(self.laytonState.saveSlot.eventCounter.toBytes(outLength=128))
            photoPieceAddCounter[0x18] = photoPieceAddCounter[0x18] + 1
            self.laytonState.saveSlot.eventCounter = FlagsAsArray.fromBytes(photoPieceAddCounter)
            self._popup = PhotoPieceAddPopup(self.laytonState, self.screenController, self._sharedImageHandler)
        
        elif opcode == OPCODES_LT2.MokutekiScreen.value and len(operands) == 2:
            self.__doMokutekiWindow(operands[1].value, operands[0].value)
        
        elif opcode == OPCODES_LT2.DoNamingHamScreen.value:
            self._popup = NamingHamPopup(self.laytonState, self.screenController, self._sharedImageHandler)

        elif opcode == OPCODES_LT2.DoLostPieceScreen.value:
            self._popup = DoLostPiecePopup(self.laytonState, self.screenController, self._sharedImageHandler)
        
        elif opcode == OPCODES_LT2.DoInPartyScreen.value and len(operands) == 1:
            partyFlagEncoded = int.from_bytes(self.laytonState.saveSlot.partyFlag.toBytes(), byteorder = 'little') | operands[0].value
            self.laytonState.saveSlot.partyFlag = FlagsAsArray.fromBytes(partyFlagEncoded.to_bytes(1, byteorder = 'little'), 8)

            if operands[0].value != 2:
                self._popup = DoInPartyPopup(self.laytonState, self.screenController, self._sharedImageHandler)
        
        elif opcode == OPCODES_LT2.DoOutPartyScreen.value and len(operands) == 1:
            partyFlagEncoded = int.from_bytes(self.laytonState.saveSlot.partyFlag.toBytes(), byteorder = 'little') & ~operands[0].value
            self.laytonState.saveSlot.partyFlag = FlagsAsArray.fromBytes(partyFlagEncoded.to_bytes(1, byteorder = 'little'), 8)

            if operands[0].value != 2:
                self._popup = DoOutPartyPopup(self.laytonState, self.screenController, self._sharedImageHandler)

        elif opcode == OPCODES_LT2.DoDiaryAddScreen.value:
            # Stubbed, but don't want an error
            pass
    
        elif opcode == OPCODES_LT2.EventSelect.value and len(operands) == 3:
            # TODO - Test, think this is on last event
            if operands[0].value == 0:
                countPuzzle = operands[1].value
                targetEventId = operands[2].value
                solved, _encountered = self.laytonState.saveSlot.getSolvedAndEncounteredPuzzleCount()
                if solved >= countPuzzle:
                    if (eventEntry := self.laytonState.getEventInfoEntry(targetEventId)) != None:
                        if eventEntry.indexEventViewedFlag != None:
                            if not(self.laytonState.saveSlot.eventViewed.getSlot(eventEntry.indexEventViewedFlag)):
                                self.laytonState.setGameMode(GAMEMODES.DramaEvent)
                                self.laytonState.saveSlot.eventViewed.setSlot(True, eventEntry.indexEventViewedFlag)
                                self.laytonState.setEventId(targetEventId)
        
        elif opcode == OPCODES_LT2.ReturnStationScreen.value:
            self._popup = ReturnStationPopup(self.laytonState, self.screenController, self._sharedImageHandler)

        elif opcode == OPCODES_LT2.CompleteWindow.value and len(operands) == 2:
            self._popup = CompleteWindowPopup(self.laytonState, self.screenController, self._sharedImageHandler, operands[0].value, operands[1].value)

        elif opcode == OPCODES_LT2.EndingAddChallenge.value and len(operands) == 0:
            if not(self.laytonState.saveSlot.isComplete):
                self._popup = EndingAddChallengePopup(self.laytonState, self.screenController, self._sharedImageHandler)

        else:
            return super()._doUnpackedCommand(opcode, operands)

        return True