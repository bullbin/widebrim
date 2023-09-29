from __future__ import annotations
from typing import TYPE_CHECKING

from widebrim.madhatter.common import logSevere

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController
    from widebrim.madhatter.hat_io.asset_script import GdScript

from widebrim.engine.string.cmp import strCmp
from widebrim.engine.state.layer import ScreenLayerNonBlocking
from widebrim.engine.state.enum_mode import STRING_TO_GAMEMODE_VALUE, GAMEMODES
from widebrim.engine.anim.fader import Fader
from widebrim.engine.const import TIME_FRAMECOUNT_TO_MILLISECONDS, RESOLUTION_NINTENDO_DS, PATH_CHAP_ROOT

from widebrim.madhatter.typewriter.strings_lt2 import OPCODES_LT2
from widebrim.madhatter.hat_io.asset_sav import FlagsAsArray
from widebrim.madhatter.hat_io.asset_script import Instruction

from pygame import MOUSEBUTTONDOWN

# TODO - Add callback support

class ScriptPlayer(ScreenLayerNonBlocking):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController, script : GdScript):
        ScreenLayerNonBlocking.__init__(self)
        self.laytonState        = laytonState
        self.screenController   = screenController

        self._popup             = None
        self._faderWait         = Fader(0, initialActiveState=False)
        self._isWaitingForTouch = False
        self._isActive          = True

        self._script = script
        # TODO - Set script method
        if self._script != None:
            self._script.cullUnreachableInstructions()

        self._indexScriptCommand = 0

    def update(self, gameClockDelta):
        if not(self.getContextState()):
            self._faderWait.update(gameClockDelta)

            if self._popup != None:
                self._popup.update(gameClockDelta)
                # TODO - Change to some other way of detecting finished state
                if self._popup.getContextState():
                    self._popup = None
            else:
                while self._popup == None and self._isActive and self._indexScriptCommand < self._script.getInstructionCount():
                    if not(self.executeCommand(self._script.getInstruction(self._indexScriptCommand))):
                        opcode = int.from_bytes(self._script.getInstruction(self._indexScriptCommand).opcode, byteorder = 'little')
                        logSevere("Unimplemented", OPCODES_LT2(opcode).name + "\n" + str(self._script.getInstruction(self._indexScriptCommand)), name="GdsPlay")

                    self._indexScriptCommand += 1
                
                if self._popup == None and self._isActive and self._indexScriptCommand >= self._script.getInstructionCount():
                    self._makeInactive()
                    self.doOnComplete()

    def doOnComplete(self):
        # TODO - Maybe call doOnComplete under script fail (no available data)
        self.doOnKill()

    def draw(self, gameDisplay):
        if self._popup != None:
            self._popup.draw(gameDisplay)

    def handleTouchEvent(self, event):
        # TODO - Centralise check that tap is on touch screen region
        if not(self.getContextState()):
            if self._isWaitingForTouch and event.type == MOUSEBUTTONDOWN and event.pos[1] >= RESOLUTION_NINTENDO_DS[1]:
                self._makeActive()
            elif self._popup != None:
                self._popup.handleTouchEvent(event)
            else:
                return super().handleTouchEvent(event)
            return True
        else:
            return super().handleTouchEvent(event)

    def _makeActive(self):
        self._faderWait.skip()
        self._isWaitingForTouch = False
        self._isActive = True
    
    def _makeInactive(self):
        self._isActive = False

    def executeCommand(self, command : Instruction):
        return self._doUnpackedCommand(int.from_bytes(command.opcode, byteorder = 'little'), command.getFilteredOperands())

    def _doUnpackedCommand(self, opcode, operands):

        if opcode == OPCODES_LT2.ExitScript.value:
            self._indexScriptCommand = self._script.getInstructionCount()

        elif opcode == OPCODES_LT2.FadeIn.value:
            self._makeInactive()
            self.screenController.fadeIn(callback=self._makeActive)

        elif opcode == OPCODES_LT2.FadeOut.value:
            self._makeInactive()
            self.screenController.fadeOut(callback=self._makeActive)

        elif opcode == OPCODES_LT2.SetPlace.value:
            self.laytonState.setPlaceNum(operands[0].value)

        elif opcode == OPCODES_LT2.SetGameMode.value:
            for key in STRING_TO_GAMEMODE_VALUE:
                if strCmp(key, operands[0].value):
                    self.laytonState.setGameMode(STRING_TO_GAMEMODE_VALUE[key])

        elif opcode == OPCODES_LT2.SetEndGameMode.value:
            for key in STRING_TO_GAMEMODE_VALUE:
                if strCmp(key, operands[0].value):
                    self.laytonState.setGameModeNext(STRING_TO_GAMEMODE_VALUE[key])

        elif opcode == OPCODES_LT2.SetMovieNum.value:
            self.laytonState.setMovieNum(operands[0].value)

        elif opcode == OPCODES_LT2.SetDramaEventNum.value:
            self.laytonState.setEventId(operands[0].value)
        
        elif opcode == OPCODES_LT2.SetAutoEventNum.value:
            # Stubbed, but don't want an error
            pass

        elif opcode == OPCODES_LT2.SetPuzzleNum.value:
            self.laytonState.setPuzzleId(operands[0].value)

        elif opcode == OPCODES_LT2.LoadBG.value:
            self.screenController.setBgMain(operands[0].value)

        elif opcode == OPCODES_LT2.LoadSubBG.value:
            self.screenController.setBgSub(operands[0].value)

        elif opcode == OPCODES_LT2.DrawChapter.value:
            # TODO - Since its known faders only work when required, how does this event fade in the bottom screen when it should already be unobscured?
            #        Think this will cause a bug where screen can be pressed without finishing fade in...

            def callbackDrawChapter():
                self.screenController.setBgMain(PATH_CHAP_ROOT % operands[0].value)
                self.screenController.fadeInMain()
                self._isWaitingForTouch = True
                self._makeInactive()

            self._makeInactive()
            self.screenController.fadeOutMain(callback=callbackDrawChapter)

        elif opcode == OPCODES_LT2.WaitFrame.value:
            self._makeInactive()
            self._faderWait.setCallback(self._makeActive)
            self._faderWait.setDurationInFrames(operands[0].value)

        elif opcode == OPCODES_LT2.FadeInOnlyMain.value:
            self._makeInactive()
            self.screenController.fadeInMain(callback=self._makeActive)

        elif opcode == OPCODES_LT2.FadeOutOnlyMain.value:
            self._makeInactive()
            self.screenController.fadeOutMain(callback=self._makeActive)

        elif opcode == OPCODES_LT2.SetEventCounter.value:
            indexCounter = operands[0].value
            valueCounter = operands[1].value

            if 0 <= indexCounter < 128:
                tempEventCounter = bytearray(self.laytonState.saveSlot.eventCounter.toBytes(outLength=128))
                tempEventCounter[indexCounter] = valueCounter
                self.laytonState.saveSlot.eventCounter = FlagsAsArray.fromBytes(tempEventCounter)

        elif opcode == OPCODES_LT2.AddEventCounter.value:
            indexCounter = operands[0].value
            valueCounter = operands[1].value

            if 0 <= indexCounter < 128:
                tempEventCounter = bytearray(self.laytonState.saveSlot.eventCounter.toBytes(outLength=128))
                tempEventCounter[indexCounter] = tempEventCounter[indexCounter] + valueCounter
                self.laytonState.saveSlot.eventCounter = FlagsAsArray.fromBytes(tempEventCounter)

        elif opcode == OPCODES_LT2.OrEventCounter.value:
            indexCounter = operands[0].value
            valueCounter = operands[1].value

            if 0 <= indexCounter < 128:
                tempEventCounter = bytearray(self.laytonState.saveSlot.eventCounter.toBytes(outLength=128))
                tempEventCounter[indexCounter] = tempEventCounter[indexCounter] | valueCounter
                self.laytonState.saveSlot.eventCounter = FlagsAsArray.fromBytes(tempEventCounter)

        # HACK - 3 unknowns in palette operations, only darkness value is used
        elif opcode == OPCODES_LT2.ModifyBGPal.value:
            self.screenController.modifyPaletteMain(operands[3].value)

        elif opcode == OPCODES_LT2.ModifySubBGPal.value:
            self.screenController.modifyPaletteSub(operands[3].value)

        elif opcode == OPCODES_LT2.WaitInput.value:
            self._isWaitingForTouch = True
            self._makeInactive()
        
        elif opcode == OPCODES_LT2.ShakeBG.value:
            self.screenController.shakeBg(operands[0].value * TIME_FRAMECOUNT_TO_MILLISECONDS)
        
        elif opcode == OPCODES_LT2.ShakeSubBG.value:
            self.screenController.shakeBgSub(operands[0].value * TIME_FRAMECOUNT_TO_MILLISECONDS)

        elif opcode == OPCODES_LT2.WaitVSyncOrPenTouch.value:
            self._makeInactive()
            self._isWaitingForTouch = True
            self._faderWait.setCallback(self._makeActive)
            self._faderWait.setDurationInFrames(operands[0].value)

        elif opcode == OPCODES_LT2.AddMemo.value:
            isMemoAdded = self.laytonState.saveSlot.memoFlag.flagEnabled.getSlot(operands[0].value - 1)
            if not(isMemoAdded):
                self.laytonState.saveSlot.memoFlag.flagNew.setSlot(True, operands[0].value - 1)
                self.laytonState.saveSlot.menuNewFlag.setSlot(True, 0)

            self.laytonState.saveSlot.memoFlag.flagEnabled.setSlot(True, operands[0].value - 1)

        elif opcode == OPCODES_LT2.FadeOutFrame.value:
            self._makeInactive()
            self.screenController.fadeOut(duration=operands[0].value * TIME_FRAMECOUNT_TO_MILLISECONDS, callback=self._makeActive)

        elif opcode == OPCODES_LT2.SetEventTea.value:
            # TODO - 2 unks stored in state, probably used in tea mode
            self.laytonState.setGameMode(GAMEMODES.EventTea)
            self.laytonState.setGameModeNext(GAMEMODES.DramaEvent)
        
        elif opcode == OPCODES_LT2.SetSubItem.value:
            self.laytonState.puzzleLastReward = operands[0].value

        elif opcode == OPCODES_LT2.ReleaseItem.value:
            self.laytonState.saveSlot.storyItemFlag.setSlot(False, operands[0].value)
        
        elif opcode == OPCODES_LT2.DrawFrames.value:
            # Not fully accurate since this counts drawn frames in the game, decoupling frames from actual timing. If the game is losing time (eg due to asset streaming) this will finish faster.
            self._makeInactive()
            self._faderWait.setCallback(self._makeActive)
            self._faderWait.setDurationInFrames(operands[0].value)

        elif opcode == OPCODES_LT2.FadeOutFrameMain.value:
            self._makeInactive()
            self.screenController.fadeOutMain(duration=operands[0].value * TIME_FRAMECOUNT_TO_MILLISECONDS, callback=self._makeActive)

        elif opcode == OPCODES_LT2.FadeInFrame.value:
            self._makeInactive()
            self.screenController.fadeIn(duration=operands[0].value * TIME_FRAMECOUNT_TO_MILLISECONDS, callback=self._makeActive)
        
        elif opcode == OPCODES_LT2.FadeInFrameMain.value:
            self._makeInactive()
            self.screenController.fadeInMain(duration=operands[0].value * TIME_FRAMECOUNT_TO_MILLISECONDS, callback=self._makeActive)
        
        elif opcode == OPCODES_LT2.CheckCounterAutoEvent.value:
            if 0 <= operands[0].value < 128:
                # Type 0 of CheckEventCounter
                eventCounterEncoded = self.laytonState.saveSlot.eventCounter.toBytes(outLength=128)
                if eventCounterEncoded[operands[0].value] == operands[1].value:
                    self.laytonState.setGameMode(GAMEMODES.DramaEvent)
                    self.laytonState.setGameModeNext(GAMEMODES.DramaEvent)

        elif opcode == OPCODES_LT2.FadeOutFrameSub.value:
            self._makeInactive()
            self.screenController.fadeOutSub(duration=operands[0].value * TIME_FRAMECOUNT_TO_MILLISECONDS, callback=self._makeActive)

        elif opcode == OPCODES_LT2.FadeInFrameSub.value:
            self._makeInactive()
            self.screenController.fadeInSub(duration=operands[0].value * TIME_FRAMECOUNT_TO_MILLISECONDS, callback=self._makeActive)

        elif opcode == OPCODES_LT2.WaitFrame2.value:
            timeEntry = self.laytonState.getTimeDefinitionEntry(operands[0].value)
            if timeEntry != None:
                self._makeInactive()
                self._faderWait.setCallback(self._makeActive)
                self._faderWait.setDurationInFrames(timeEntry.countFrames)
            else:
                logSevere("Missing time definition information for ID", operands[0].value, name="GdsPlayErr")

        elif opcode == OPCODES_LT2.SetRepeatAutoEventID.value:
            self.laytonState.saveSlot.idHeldAutoEvent = operands[0].value
            self.laytonState.saveSlot.eventViewed.setSlot(False, operands[0].value)

        elif opcode == OPCODES_LT2.ReleaseRepeatAutoEventID.value:
            self.laytonState.saveSlot.idHeldAutoEvent = -1
            self.laytonState.saveSlot.eventViewed.setSlot(True, operands[0].value)

        elif opcode == OPCODES_LT2.SetFirstTouch.value:
            self.laytonState.isFirstTouchEnabled = True

        else:
            return False

        return True