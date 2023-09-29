from __future__ import annotations
from typing import List, Optional, TYPE_CHECKING

from pygame.constants import KEYUP
from widebrim.engine.anim.font.staticFormatted import StaticTextHelper
from widebrim.madhatter.common import logSevere
from widebrim.madhatter.hat_io.asset import LaytonPack
from widebrim.madhatter.hat_io.asset_script import GdScript
from widebrim.engine.keybinds import KEY_START

from widebrim.engine_ext.const import PATH_TEMP
from widebrim.engine.state.enum_mode import GAMEMODES
from widebrim.engine.config import TIME_FRAMERATE
from widebrim.engine.const import PATH_PACK_TXT, RESOLUTION_NINTENDO_DS
from widebrim.engine_ext.utils import ensureTempFolder, substituteLanguageString, decodeStringFromPack
from widebrim.gamemodes.core_popup.script import ScriptPlayer

from widebrim.madhatter.typewriter.strings_lt2 import OPCODES_LT2

from subprocess import Popen, PIPE
from pygame import Surface
from pygame.image import frombuffer
from .const import *
from os import remove
from math import ceil

if TYPE_CHECKING:
    from widebrim.engine.state.manager.state import Layton2GameState
    from widebrim.engine_ext.state_game import ScreenController
    from widebrim.engine.file import ReadOnlyFileInterface

# Thank you FFMPEG team for supporting mobiclip! 4.4 minimum req.

# TODO - Implement drawable
class MovieSurface():

    LOG_MODULE_NAME = "MovieSurf"

    def __init__(self, fileAccessor : ReadOnlyFileInterface, indexMovie : int, callback : Optional[callable], framerate : float = 23.98):
        width, height               = RESOLUTION_NINTENDO_DS
        self.__pathMovieFile        = None
        self.__timeElapsed  : float = 0
        self.__callback             = callback
        self.__pos                  = (0,RESOLUTION_NINTENDO_DS[1])

        if ensureTempFolder():
            if ((movieData := fileAccessor.getData(PATH_MOBICLIP_MOVIE % indexMovie)) != None):
                try:
                    # Credit to Gericom for MODS header information - https://github.com/Gericom/MobiclipDecoder
                    if len(movieData) > 30 and movieData[:4] == b'MODS':
                        calcDimensions = (int.from_bytes(movieData[0xc:0x10], byteorder = 'little'), int.from_bytes(movieData[0x10:0x14], byteorder = 'little'))
                        if calcDimensions[0] > 0 and calcDimensions[1] > 0:
                            width, height = calcDimensions
                        calcFps = int.from_bytes(movieData[0x14:0x18], byteorder = 'little') / (2 ** 24)
                        if calcFps != 0:
                            framerate = calcFps

                        # TODO - Writes empty even if not found...
                        with open(PATH_TEMP + "//" + PATH_TEMP_MOVIE_FILE, 'wb') as movieTemp:
                            movieTemp.write(movieData)
                        self.__pathMovieFile = PATH_TEMP + "//" + PATH_TEMP_MOVIE_FILE
                except:
                    pass
        
        # Calculate size of raw frame
        self.__bufferSize       = width * height * 3
        self.__surfVideo    :   Surface  = Surface((width, height))
        self.__timeFrame        = 1000 / framerate
        self.__procConv     :   Optional[Popen] = None

        if self.__pathMovieFile != None:
            # TODO - Switch to python ffmpeg for platform agnostic ffmpeg
            # Credit to https://stackoverflow.com/a/62870947 for the command used in this process
            command = [ "ffmpeg",
                        '-loglevel', 'quiet',
                        '-i', self.__pathMovieFile,
                        # Mobiclip decoder doesn't deswizzle correctly...
                        '-filter_complex', 'colorchannelmixer=1:0:0:0:0:0:1:0:0:1:0:0:0:0:0:1', 
                        '-f', 'image2pipe',
                        '-s', '%dx%d' % (width, height),
                        '-pix_fmt', 'rgb24',
                        '-vcodec', 'rawvideo',
                        '-' ]
            
            if framerate > 0:
                # Scale the amount of frames by the actual framerate. Eg at 12fps, we need 2 frames of 24fps video to keep display smooth
                bufferFrameCount = framerate / TIME_FRAMERATE
                bufferFrameCount *= COUNT_BUFFER_FRAMES
                bufferFrameCount = max(ceil(bufferFrameCount), COUNT_BUFFER_FRAMES) # Ensure that there is always at least COUNT_BUFFER_FRAMES in background
            else:
                bufferFrameCount = COUNT_BUFFER_FRAMES

            try:
                self.__procConv = Popen(command, stdout=PIPE, bufsize=self.__bufferSize * bufferFrameCount)
            except:
                logSevere("Error starting FFMPEG decoder!", name=MovieSurface.LOG_MODULE_NAME)
                self.cleanup()
        else:
            self.cleanup()

    def setPos(self, pos):
        self.__pos = pos
    
    def getPos(self):
        return self.__pos

    def canStart(self) -> bool:
        return self.__procConv != None

    def cleanup(self):
        if self.__procConv != None:
            self.__procConv.stdout.close()
            self.__procConv.terminate()
            self.__procConv.wait()
            self.__procConv = None
            try:
                remove(self.__pathMovieFile)
            except:
                pass

            if callable(self.__callback):
                self.__callback()
                self.__callback = None

    def update(self, gameClockDelta):
        if self.__procConv != None:
            self.__timeElapsed += gameClockDelta
            while self.__timeElapsed >= self.__timeFrame:
                try:
                    self.__surfVideo = frombuffer(self.__procConv.stdout.read(self.__bufferSize), (self.__surfVideo.get_width(), self.__surfVideo.get_height()), 'RGB')
                    self.__timeElapsed -= self.__timeFrame
                except:
                    # Buffer underrun. Can happen for variety of reasons. We want a frame but its not ready yet
                    if self.__procConv.poll() != None:
                        # ffmpeg has finished. Video either errored or has finished playing. Since buffer is empty, we can terminate early
                        self.cleanup()
                        break
                    else:
                        # Flush just in case...
                        self.__procConv.stdout.flush()
    
    def draw(self, gameDisplay):
        gameDisplay.blit(self.__surfVideo, self.__pos)

class SubtitleCommand():
    def __init__(self, packSubtitle : LaytonPack, indexMovie : int, indexSubtitle : int, timeStart : float, timeEnd : float):
        self.text = decodeStringFromPack(packSubtitle, PATH_TXT_SUBTITLE % (indexMovie, indexSubtitle))
        self.timeStart = timeStart
        self.timeEnd = timeEnd

class MoviePlayer(ScriptPlayer):
    def __init__(self, laytonState : Layton2GameState, screenController : ScreenController):
        ScriptPlayer.__init__(self, laytonState, screenController, GdScript())
        self.__surfaceMovie = MovieSurface(laytonState.getFileAccessor(), laytonState.getMovieNum(), self.__fadeOutAndTerminate)

        if (scriptData := laytonState.getFileAccessor().getPackedData(PATH_ARCHIVE_MOVIE_SUBTITLES.replace("?", laytonState.language.value), PATH_NAME_SUBTITLE_SCRIPT % laytonState.getMovieNum())) != None:
            self._script.load(scriptData)
        else:
            self.doOnComplete()

        self.__packTxt = laytonState.getFileAccessor().getPack(substituteLanguageString(laytonState, PATH_PACK_TXT))
        self.__indexActiveSubtitle = -1
        self.__waitingForNextSubtitle = False
        self.__textRendererSubtitle = StaticTextHelper(laytonState.fontEvent, yBias=2)
        self.__textRendererSubtitle.setColor((255,255,255))
        self.__textRendererSubtitle.setPos((RESOLUTION_NINTENDO_DS[0] // 2, RESOLUTION_NINTENDO_DS[1] + 177))
        self.__timeElapsedSeconds = 0
        self.__subtitles : List[SubtitleCommand] = []
    
    def __updateRenderedSubtitle(self):

        def getNextSubtitle():
            # TODO - While loop to eliminate without rendering text if decoding is SEVERELY behind (this maxes at 1 subtitle per frame)
            nextSubIndex = self.__indexActiveSubtitle + 1
            if nextSubIndex < len(self.__subtitles) and self.__subtitles[nextSubIndex].timeStart <= self.__timeElapsedSeconds and self.__subtitles[nextSubIndex].timeEnd > self.__timeElapsedSeconds:
                self.__textRendererSubtitle.setText(self.__subtitles[nextSubIndex].text)
                self.__waitingForNextSubtitle = False
                self.__indexActiveSubtitle = nextSubIndex

        if self.__indexActiveSubtitle != -1:
            # If a subtitle is valid and loaded
            if self.__waitingForNextSubtitle:
                getNextSubtitle()
            else:
                if self.__subtitles[self.__indexActiveSubtitle].timeEnd < self.__timeElapsedSeconds:
                    self.__textRendererSubtitle.setText("")
                    self.__waitingForNextSubtitle = True

        if self.__indexActiveSubtitle == -1 and len(self.__subtitles) != 0:
            getNextSubtitle()

    # TODO - Draw and update returns
    def __drawOnScriptComplete(self, gameDisplay):
        self.__surfaceMovie.draw(gameDisplay)
        self.__textRendererSubtitle.drawXYCenterPointNoBias(gameDisplay)
    
    def __updateOnScriptComplete(self, gameClockDelta):
        self.__timeElapsedSeconds += gameClockDelta / 1000      # TODO - What happens if ffmpeg is losing time due to overload?
        self.__updateRenderedSubtitle()
        self.__surfaceMovie.update(gameClockDelta)
    
    def handleKeyboardEvent(self, event):
        if not(self.screenController.getFadingStatus()):
            if event.type == KEYUP and event.key == KEY_START:
                self.__fadeOutAndTerminate()
                return True
        return super().handleKeyboardEvent(event)
    
    def doOnKill(self):
        # HACK - Force cleanup on termination in case of skipped scene, as the thread will otherwise continue in background
        if self.__surfaceMovie != None:
            self.__surfaceMovie.cleanup()
        if self.laytonState.isInMovieMode:
            self.laytonState.setGameMode(GAMEMODES.MovieViewMode)
        else:
            self.laytonState.setGameMode(self.laytonState.getGameModeNext())
        return super().doOnKill()

    def __fadeOutAndTerminate(self):
        if not(self.screenController.getFadingStatus()):
            self.screenController.fadeOutMain(callback=self.doOnKill)

    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.SetSubTitle.value and len(operands) == 3:
            if len(self.__subtitles) < COUNT_MAX_SUBTITLES:
                self.__subtitles.append(SubtitleCommand(self.__packTxt, self.laytonState.getMovieNum(), operands[0].value, operands[1].value, operands[2].value))
            else:
                logSevere("Prevented overflow from excessive subtitles!", name="MovieWarn")
            return True
        return super()._doUnpackedCommand(opcode, operands)

    def doOnComplete(self):
        self.update = self.__updateOnScriptComplete
        self.draw = self.__drawOnScriptComplete

        if self.__surfaceMovie.canStart():
            self.screenController.fadeInMain()
        else:
            self.__fadeOutAndTerminate()

    def doOnPygameQuit(self):
        self.__surfaceMovie.cleanup()
        return super().doOnPygameQuit()