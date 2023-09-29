from __future__ import annotations

from typing import Optional
import ndspy.rom
from widebrim.engine.file.base import ReadOnlyFileInterface
from widebrim.engine_ext.utils import decodeStringFromPack
from widebrim.madhatter.common import log, logSevere
from widebrim.engine.config import PATH_ROM
from os.path import isfile

from widebrim.madhatter.hat_io.asset import File, LaytonPack
from ..exceptions import PathInvalidRom, RomInvalid
from widebrim.engine.const import ADDRESS_ARM9_POINTER_FUNC_LANGUAGE, DICT_ID_TO_LANGUAGE, LANGUAGES

# TODO - Madhatter magic checks, file checks (there will be errors once patching starts...)

class NativeRomFileInterface(ReadOnlyFileInterface):

    LOG_MODULE_NAME = "FsNative"

    def __init__(self):
        super().__init__()
        self._rom = None
        self._romLanguage : Optional[LANGUAGES] = None

        if isfile(PATH_ROM):
            try:
                self._rom = ndspy.rom.NintendoDSRom.fromFile(PATH_ROM)
            except:
                raise RomInvalid
            
            if self._rom != None and self._rom.name != bytearray(b'LAYTON2') or not((self._rom.idCode[:3] != bytearray(b'YLT') or self._rom.idCode[:3] != bytearray(b'Y6Z'))):
                raise RomInvalid
        
        if self._rom == None:
            raise PathInvalidRom

    def doesFileExist(self, filepath : str) -> bool:
        try:
            if self._rom.filenames.idOf(filepath) != None:
                return True
            return False
        except:
            return False

    def getData(self, filepath : str) -> Optional[bytearray]:
        if self.doesFileExist(filepath):
            testFile = File(data=self._rom.getFileByName(filepath))
            testFile.decompress()
            log("RomGrab", filepath, name=NativeRomFileInterface.LOG_MODULE_NAME)
            return testFile.data
        logSevere("RomGrabFailed", filepath, name=NativeRomFileInterface.LOG_MODULE_NAME)
        return None

    def getPack(self, filepath : str) -> LaytonPack:
        archive = LaytonPack()
        if (data := self.getData(filepath)) != None:
            archive.load(data)
        return archive
    
    def getPackedData(self, pathPack : str, filename : str) -> Optional[bytearray]:
        return self.getPack(pathPack).getFile(filename)
    
    def getPackedString(self, pathPack : str, filename : str) -> Optional[str]:
        return decodeStringFromPack(self.getPack(pathPack), filename)
    
    def isRunningFromRom(self) -> bool:
        return True
    
    def getRom(self) -> Optional[ndspy.rom.NintendoDSRom]:
        return self._rom

    def getLanguage(self) -> Optional[LANGUAGES]:
        """Attempts to get language from loaded LAYTON2 ROM. Will not recognise (regional, unmodified) Japanese ROM due to changes interfering with language heuristic.

        Returns:
            Optional[Union[Literal[LANGUAGES.Chinese], Literal[LANGUAGES.Dutch], Literal[LANGUAGES.English], Literal[LANGUAGES.French], Literal[LANGUAGES.German], Literal[LANGUAGES.Italian], Literal[LANGUAGES.Japanese], Literal[LANGUAGES.Korean]]]: Returns LANGUAGES Enum member if language could be found, else None
        """
        if self._romLanguage != None:
            return self._romLanguage

        if self._rom != None:
            arm9 = self._rom.loadArm9()
            startAddress = arm9.ramAddress
            dataArm9 = arm9.save()

            def is32BitGrabValid(address : int):
                return 0 <= address and address + 4 <= len(dataArm9)

            # Not emulating any registers, so relying on heuristics to detect correct MOV instruction. Assumes r0 will be used, so rest of engine not touched

            targetInstructionPointer = ADDRESS_ARM9_POINTER_FUNC_LANGUAGE - startAddress    # Find pointer to next big function after entry
            
            if is32BitGrabValid(targetInstructionPointer):
                targetInstructionPointer = int.from_bytes(dataArm9[targetInstructionPointer:targetInstructionPointer + 4], byteorder='little') - startAddress
                if is32BitGrabValid(targetInstructionPointer):
                    targetInstructionPointer += 4 * 33                      # Seek forward 33 instructions into the function (mov)
                    if is32BitGrabValid(targetInstructionPointer):
                        languageInstruction = int.from_bytes(dataArm9[targetInstructionPointer : targetInstructionPointer + 4], byteorder = 'little')
                        if languageInstruction & 0xffffff00 == 0xe3a00000:  # Check for proper MOV instruction to r0 with immediate language operand
                            languageInstruction = languageInstruction & 0x000000ff
                            if languageInstruction in DICT_ID_TO_LANGUAGE:
                                log("Detected language", DICT_ID_TO_LANGUAGE[languageInstruction].value, name=NativeRomFileInterface.LOG_MODULE_NAME)
                                self._romLanguage = DICT_ID_TO_LANGUAGE[languageInstruction]
                                return self._romLanguage
        logSevere("Failed to detect language!", name=NativeRomFileInterface.LOG_MODULE_NAME)
        return None