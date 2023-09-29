from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from widebrim.madhatter.common import logSevere

if TYPE_CHECKING:
    from widebrim.madhatter.hat_io.asset_dlz.nz_lst import DlzEntryNzLst
    from widebrim.madhatter.hat_io.asset_dlz.sm_inf import DlzEntrySubmapInfoNds
    from widebrim.madhatter.hat_io.asset_dlz.ev_inf2 import DlzEntryEvInf2
    from widebrim.engine.file import ReadOnlyFileInterface

from widebrim.madhatter.hat_io.asset_sav import Layton2SaveSlot, WiFiState
from widebrim.madhatter.hat_io.asset_dlz import EventInfoList, SubmapInfoNds, GoalInfo, NazoListNds, HerbteaEvent, ChapterInfo, TimeDefinitionInfo
from widebrim.madhatter.hat_io.asset_dat import NazoDataNds
from widebrim.madhatter.hat_io.asset_placeflag import PlaceFlag
from widebrim.madhatter.hat_io.asset_storyflag import StoryFlag
from widebrim.madhatter.hat_io.asset_autoevent import AutoEvent
from widebrim.madhatter.hat_io.asset import File

from ...const import LANGUAGES, EVENT_ID_START_PUZZLE, EVENT_ID_START_TEA, PATH_DB_AUTOEVENT, PATH_DB_EV_INF2, PATH_DB_HTEVENT, PATH_DB_PLACEFLAG, PATH_DB_SM_INF, PATH_DB_STORYFLAG, PATH_PROGRESSION_DB, PATH_DB_RC_ROOT, PATH_DB_GOAL_INF, PATH_DB_NZ_LST, PATH_DB_TM_DEF, PATH_DB_RC_ROOT_LANG, PATH_DB_CHP_INF
from ...const import PATH_NAZO_A, PATH_NAZO_B, PATH_NAZO_C, PATH_PACK_NAZO
from ...exceptions import FileInvalidCritical
from ...anim.font.nftr_decode import NftrTiles

from time import time
from math import floor

from ..enum_mode import GAMEMODES

class Layton2GameState():
    def __init__(self, language : LANGUAGES, fileInterface : ReadOnlyFileInterface):
        """Convenience object to store entire game state required for playback.

        Args:
            language (LANGUAGES): Language for filesystem access.
            fileInterface (FileInterface): Filesystem abstraction used for gameplay.

        Raises:
            FileInvalidCritical: Raised if any immediate asset required for gameplay is missing. Further missing assets are not counted.
        """
        
        self.__fileInterface  = fileInterface

        # Save header is unused during gameplay
        self.saveSlot       = Layton2SaveSlot()
        # TODO - Index slot
        self.wiFiData       = WiFiState()
        self.language       = language
        
        self._gameMode       = GAMEMODES.INVALID
        self._gameModeNext   = GAMEMODES.INVALID

        self._idEvent       = -1
        self._idMovieNum    = -1
        
        self.namePlace      = ""

        self.isFirstTouchEnabled    = False
        self.wasPuzzleSkipped       = False
        self.wasPuzzleSolved        = False
        self.wasPuzzleRestarted     = False
        self.puzzleLastReward       = -1
        self.isInMovieMode          = False
        self._indexMysteryChanged           : int   = -1
        self._roomLoadBehaviour             : int   = 0
        self._idExternalLastFavouritePuzzle : int   = 0
        self._idExternalLastWiFiPuzzle      : int   = 0

        self.dbPlaceFlag        = PlaceFlag()
        self.dbStoryFlag        = StoryFlag()
        self.dbAutoEvent        = AutoEvent()

        self.dlzHerbteaEvent    = HerbteaEvent()

        if (herbteaData := self.__fileInterface.getData(PATH_DB_HTEVENT)) != None:
            try:
                self.dlzHerbteaEvent.load(herbteaData)
            except:
                pass

        # Safe to assume always loaded
        try:
            packedProgressionDbs = self.__fileInterface.getPack(PATH_PROGRESSION_DB)
            self.dbPlaceFlag.load(packedProgressionDbs.getFile(PATH_DB_PLACEFLAG))
            self.dbStoryFlag.load(packedProgressionDbs.getFile(PATH_DB_STORYFLAG))
            self.dbAutoEvent.load(packedProgressionDbs.getFile(PATH_DB_AUTOEVENT))

        except:
            raise FileInvalidCritical()

        # Loaded and unloaded where required
        self._dbChapterInfo     = None
        self._dbSubmapInfo      = None
        self._dbGoalInfo        = None
        self._dbSoundSetList    = None
        self._dbEventInfo       = None
        self._dbEventBaseList   = None
        self._dbPuzzleInfo      = None
        self._dbSubPhoto        = None
        self._dbTeaElement      = None
        self._dbTeaRecipe       = None
        self._dbTeaEventInfo    = None
        self._dbTeaTalk         = None
        self._dbNazoList        = None
        self._dbSubmapInfo      = None

        # TODO - Add to const
        try:
            self.font18             = NftrTiles(self.__fileInterface.getData("/data_lt2/font/font18.NFTR"))
            self.fontEvent          = NftrTiles(self.__fileInterface.getData("/data_lt2/font/fontevent.NFTR"))
            self.fontQ              = NftrTiles(self.__fileInterface.getData("/data_lt2/font/fontq.NFTR"))
            self._dbNazoList        = NazoListNds()
            self._dbNazoList.load(self.__fileInterface.getData(PATH_DB_RC_ROOT_LANG % (self.language.value, PATH_DB_NZ_LST)))
            self._dbTimeDef         = TimeDefinitionInfo()
            self._dbTimeDef.load(self.__fileInterface.getData(PATH_DB_RC_ROOT % (PATH_DB_TM_DEF)))
        except:
            raise FileInvalidCritical()

        # Accuracy changes - SoundSet, EventBase, EventInfo, PuzzleInfo and Herbtea persistent from init
        self.loadEventInfoDb()

        self.entryEvInfo : Optional[DlzEntryEvInf2] = None
        self.entryNzList    = None
        self._entryNzData    = None

        # Not accurate, but used to centralise event behaviour between room and event
        self.__isTimeStarted = False
        self.__timeStarted = 0
        self._wasLastEventIdBranching = False
        self.timeStartTimer()

    def resetState(self):
        # Not accurate but not using globals so who cares (HACK)
        self._gameMode              = GAMEMODES.INVALID
        self._gameModeNext          = GAMEMODES.INVALID
        self._idEvent               = -1
        self._idMovieNum            = -1
        self.namePlace              = ""
        self.isFirstTouchEnabled    = False
        self.wasPuzzleSkipped       = False
        self.wasPuzzleSolved        = False
        self.wasPuzzleRestarted     = False
        self.puzzleLastReward       = -1
        self.isInMovieMode          = False
        self._indexMysteryChanged   = -1
        self._roomLoadBehaviour     = 0
        self._idExternalLastFavouritePuzzle = 0
        self._idExternalLastWiFiPuzzle      = 0

        self.unloadChapterInfoDb()
        self.unloadCurrentNazoData()
        self.unloadEventInfoDb()
        self.unloadSubmapInfo()
        self.unloadGoalInfoDb()

        self.timeStartTimer()

    def timeGetStartedState(self):
        return self.__isTimeStarted

    def timeStartTimer(self):
        self.__isTimeStarted = True
        self.__timeStarted = time()

    def timeUpdateStoredTime(self):
        if self.timeGetStartedState():
            # TODO - Access method which changes the header time and save slot time simulataneously
            # This is only used to verify whether the save was tampered with which isn't that accuracy anyway
            # TODO - Is the padding after the time variable actually where the counting time is stored?
            self.saveSlot.timeElapsed = self.timeGetRunningTime()
            self.__timeStarted = time()

    def timeGetRunningTime(self):
        return max(floor(time() - self.__timeStarted), 0) + self.saveSlot.timeElapsed

    def setMovieNum(self, movieNum):
        self._idMovieNum = movieNum
    
    def getMovieNum(self):
        return self._idMovieNum

    def setPlaceNum(self, placeNum):
        if self.saveSlot.roomIndex != placeNum:
            self.saveSlot.idHeldAutoEvent = -1
        self.saveSlot.roomIndex = placeNum
    
    def getPlaceNum(self):
        return self.saveSlot.roomIndex

    def setGameMode(self, newGameMode):
        self._gameMode = newGameMode
    
    def getGameMode(self):
        return self._gameMode
    
    def setGameModeNext(self, newGameMode):
        self._gameModeNext = newGameMode
    
    def getGameModeNext(self):
        return self._gameModeNext

    def getTimeDefinitionEntry(self, idTime):
        return self._dbTimeDef.searchForEntry(idTime)

    def loadEventInfoDb(self):
        self._dbEventInfo = EventInfoList()
        self._dbEventInfo.load(self.__fileInterface.getData(PATH_DB_EV_INF2 % self.language.value))

    def unloadEventInfoDb(self):
        self._dbEventInfo = None

    def getEventInfoEntry(self, idEvent) -> Optional[DlzEntryEvInf2]:
        if self._dbEventInfo == None:
            # TODO : Load event info
            logSevere("Event Info unloaded too early!", name="StateLowAcc")
            self.loadEventInfoDb()

        return self._dbEventInfo.searchForEntry(idEvent)
    
    def setEventId(self, idEvent):
        # As evidenced by event 15000, the game will accept events which are not inside
        # any event database and simply void out its own cached entry in RAM.
        # Without this behaviour implemented, 14510 will loop as it tries to connect to
        # 15000.
        entry = self.getEventInfoEntry(idEvent)
        self._idEvent = idEvent
        self.entryEvInfo = entry
        self._wasLastEventIdBranching = False
        return True
    
    def setEventIdBranching(self, idEvent):
        self.setEventId(idEvent)
        self._wasLastEventIdBranching = True
        return True
    
    def getEventId(self):

        def getOffsetIdWasViewed():
            if self.entryEvInfo.indexEventViewedFlag != None:
                if self.saveSlot.eventViewed.getSlot(self.entryEvInfo.indexEventViewedFlag):
                    return self._idEvent + 1
            return self._idEvent

        def getOffsetIdPuzzle():
            # Initial solved and quit not included as these seem to be the result of the puzzle handler
            # These will not be modified however
            if self.entryEvInfo.dataPuzzle != None:
                nazoListEntry = self.getNazoListEntry(self.entryEvInfo.dataPuzzle)
                if nazoListEntry != None:
                    entryPuzzle = self.saveSlot.puzzleData.getPuzzleData(nazoListEntry.idExternal - 1)
                    if entryPuzzle.wasSolved:
                        return self._idEvent + 2
                    elif entryPuzzle.wasEncountered:
                        return self._idEvent + 1
                return getOffsetIdWasViewed()
            return self._idEvent
        
        def getOffsetIdLimit():
            countSolved, countEncountered = self.saveSlot.getSolvedAndEncounteredPuzzleCount()
            if countSolved >= self.entryEvInfo.dataPuzzle:
                return self._idEvent + 2
            return getOffsetIdWasViewed()

        if self.entryEvInfo == None:
            return self._idEvent

        if self.entryEvInfo.indexStoryFlag != None:
            self.saveSlot.storyFlag.setSlot(True, self.entryEvInfo.indexStoryFlag)
        
        if not(self._wasLastEventIdBranching):
            return self._idEvent
        
        if self._idEvent >= EVENT_ID_START_TEA:
            # Tea Event
            # TODO - Figure out progression on these
            return self._idEvent
        
        elif self._idEvent >= EVENT_ID_START_PUZZLE:
            # Puzzle Event (designated IDs)
            return getOffsetIdPuzzle()

        else:
            # Drama Event
            if self.entryEvInfo.typeEvent == 5:
                return getOffsetIdLimit()
            elif self.entryEvInfo.typeEvent == 2:
                return getOffsetIdWasViewed()
            else:
                return self._idEvent
    
    def clearEventId(self):
        self._idEvent = -1
        self.entryEvInfo = None
    
    def setPuzzleId(self, idInternal):
        # Load nz info entry, set id
        self.entryNzList = self.getNazoListEntry(idInternal)
        if self.entryNzList == None:
            logSevere("Failed to update entry!", name="StateNazo")

    def getCurrentNazoListEntry(self) -> Optional[DlzEntryNzLst]:
        return self.entryNzList

    def getNazoListEntry(self, idInternal) -> Optional[DlzEntryNzLst]:
        return self._dbNazoList.searchForEntry(idInternal)
    
    def getNazoListEntryByExternal(self, idExternal) -> Optional[DlzEntryNzLst]:
        for indexEntry in range(self._dbNazoList.getCountEntries()):
            entry = self._dbNazoList.getEntry(indexEntry)
            if entry.idExternal == idExternal:
                return entry
        return None

    def getNazoDataAtId(self, idInternal) -> Optional[NazoDataNds]:
        # TODO - Store this max somewhere, it's already a save field
        if type(idInternal) == int and 0 <= idInternal < 216:
            if idInternal < 60:
                pathNazo = PATH_NAZO_A
            elif idInternal < 120:
                pathNazo = PATH_NAZO_B
            else:
                pathNazo = PATH_NAZO_C
            
            if (data := self.__fileInterface.getPackedData(pathNazo % self.language.value, PATH_PACK_NAZO % idInternal)) != None:
                output = NazoDataNds()
                if output.load(data):
                    return output
        return None

    def loadCurrentNazoData(self) -> bool:
        if self.getCurrentNazoListEntry() != None:
            self._entryNzData = self.getNazoDataAtId(self.getCurrentNazoListEntry().idInternal)
            return self._entryNzData != None
        self._entryNzData = None
        return False
    
    def getNazoData(self) -> Optional[NazoDataNds]:
        return self._entryNzData

    def unloadCurrentNazoData(self):
        pass

    def loadChapterInfoDb(self):
        self._dbChapterInfo = ChapterInfo()
        if (dbChapterInfo := self.__fileInterface.getData(PATH_DB_RC_ROOT % PATH_DB_CHP_INF)) != None:
            self._dbChapterInfo.load(dbChapterInfo)

    def unloadChapterInfoDb(self):
        del self._dbChapterInfo
        self._dbChapterInfo = None

    def getChapterInfEntry(self):
        if self._dbChapterInfo == None:
            logSevere("Chapter Info was unloaded too early!", name="StateLowAcc")
            self.loadChapterInfoDb()

        for indexEntry in range(self._dbChapterInfo.getCountEntries()):
            entry = self._dbChapterInfo.getEntry(indexEntry)
            if entry.chapter == self.saveSlot.chapter:
                return entry
        return None

    def loadGoalInfoDb(self):
        self._dbGoalInfo = GoalInfo()
        # HACK - Temporary workaround
        if (data := self.__fileInterface.getData(PATH_DB_RC_ROOT % PATH_DB_GOAL_INF)) != None:
            tempFile = File(data=data)
            tempFile.decompressLz10()
            self._dbGoalInfo.load(tempFile.data)
    
    def unloadGoalInfoDb(self):
        del self._dbGoalInfo
        self._dbGoalInfo = None

    def getGoalInfEntry(self, id : int):
        if self._dbGoalInfo == None:
            logSevere("Goal Info was unloaded too early!", name="StateLowAcc")
            self.loadGoalInfoDb()
        return self._dbGoalInfo.searchForEntry(id)
    
    def loadSubmapInfo(self):
        if self._dbSubmapInfo == None:
            if (submapData := self.__fileInterface.getData(PATH_DB_RC_ROOT % PATH_DB_SM_INF)) != None:
                self._dbSubmapInfo = SubmapInfoNds()
                self._dbSubmapInfo.load(submapData)
                return True
        return False

    def unloadSubmapInfo(self):
        del self._dbSubmapInfo
        self._dbSubmapInfo = None

    def getSubmapInfoEntry(self, indexEventViewed) -> Optional[DlzEntrySubmapInfoNds]:
        if indexEventViewed == 0 or self.saveSlot.eventViewed.getSlot(indexEventViewed):
            if self._dbSubmapInfo == None:
                self.loadSubmapInfo()
                logSevere("Submap Info was unloaded too early!", name="StateLowAcc")

            if self._dbSubmapInfo != None:
                return self._dbSubmapInfo.searchForEntry(indexEventViewed, self.saveSlot.roomIndex, self.saveSlot.chapter)
        return None
    
    # TODO - Merge into madhatter, simpler
    def isAnthonyDiaryEnabled(self) -> bool:
        for indexFlag in range(16):
            if self.saveSlot.anthonyDiaryState.flagEnabled.getSlot(indexFlag):
                return True
        return False
    
    def isCameraAvailable(self) -> bool:
        return int.from_bytes(self.saveSlot.minigameCameraState.getCameraAvailableBytes(), byteorder = 'little') != 0
    
    def isCameraAssembled(self) -> bool:
        # Don't know best way to do this yet :(
        return False
    
    def isCameraComplete(self) -> bool:
        for indexCamFlag in range(10):
            if not(self.saveSlot.photoState.flagComplete.getSlot(indexCamFlag)):
                return False
        return True

    def isHamsterUnlocked(self) -> bool:
        return self.saveSlot.minigameHamsterState.isEnabled
    
    def isHamsterCompleted(self) -> bool:
        return self.saveSlot.minigameHamsterState.level == 0
    
    def isTeaEnabled(self) -> bool:
        for indexElement in range(self.saveSlot.minigameTeaState.flagElements.getLength()):
            if self.saveSlot.minigameTeaState.flagElements.getSlot(indexElement):
                return True
        return False

    def isTeaCompleted(self) -> bool:
        # TODO - More to this, maybe reserved bit elsewhere
        for indexElement in range(self.saveSlot.minigameTeaState.flagCorrect.getLength()):
            if not(self.saveSlot.minigameTeaState.flagCorrect.getSlot(indexElement)):
                return False
        return True
    
    def getRoomLoadBehaviour(self) -> int:
        return self._roomLoadBehaviour
    
    def setRoomLoadBehaviour(self, value : int) -> bool:
        if 0 <= value <= 2:
            self._roomLoadBehaviour = value
            return True
        return False

    def getCountSolvedStoryPuzzles(self) -> int:
        countSolved = 0
        for indexExternalPuzzle in range(1, 0x8b):
            indexPuzzleData = indexExternalPuzzle - 1
            if (puzzleData := self.saveSlot.puzzleData.getPuzzleData(indexPuzzleData)) != None and puzzleData.wasSolved:
                countSolved += 1
        return countSolved
    
    def getCountEncounteredStoryPuzzle(self) -> int:
        count = 0
        for idExternal in range(1, 0x8b):
            if (puzzleData := self.saveSlot.puzzleData.getPuzzleData(idExternal - 1)) != None and puzzleData.wasEncountered:
                count += 1
        return count
    
    def hasAllStoryPuzzlesBeenSolved(self) -> bool:
        return self.getCountSolvedStoryPuzzles() == 138
    
    def hasAllPuzzlesBeenSolved(self) -> bool:
        for indexExternalPuzzle in range(1, 0x9a):
            indexPuzzleData = indexExternalPuzzle - 1
            if (puzzleData := self.saveSlot.puzzleData.getPuzzleData(indexPuzzleData)) != None and not(puzzleData.wasSolved):
                return False
        return True
    
    def clearMysteryUnlockedIndex(self):
        self._indexMysteryChanged = -1

    # IndexMystery should be between 1 and 10, but game never checks this
    def setMysteryUnlockedIndex(self, indexMystery : int, isSolved : bool):
        if isSolved:
            self._indexMysteryChanged = indexMystery + 9
        else:
            self._indexMysteryChanged = indexMystery - 1

    def getEncodedMysteryIndex(self) -> int:
        return self._indexMysteryChanged

    def getLastJitenNazoExternal(self) -> int:
        return self.saveSlot.lastAccessedPuzzle

    def setLastJitenNazoExternal(self, idExternal : int):
        # TODO - Puzzle int validation
        self.saveSlot.lastAccessedPuzzle = idExternal

    def getLastJitenFavouriteExternal(self) -> int:
        return self._idExternalLastFavouritePuzzle

    def setLastJitenFavouriteExternal(self, idExternal : int):
        self._idExternalLastFavouritePuzzle = idExternal
    
    def getLastJitenWiFiExternal(self) -> int:
        return self._idExternalLastWiFiPuzzle

    def setLastJitenWiFiExternal(self, idExternal : int):
        self._idExternalLastWiFiPuzzle = idExternal
    
    def getFileAccessor(self) -> ReadOnlyFileInterface:
        return self.__fileInterface
