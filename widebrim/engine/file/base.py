from typing import Optional
from widebrim.engine.const import LANGUAGES
from widebrim.madhatter.hat_io.asset import LaytonPack
from ndspy.rom import NintendoDSRom

class ReadOnlyFileInterface():
    
    def doesFileExist(self, filepath : str) -> bool:
        """Checks if there is a file available for given filepath. Does not ensure file is valid or readable.

        Args:
            filepath (str): Full filepath for data

        Returns:
            bool: True if file reference could be found
        """
        return False

    def getData(self, filepath : str) -> Optional[bytearray]:
        """Gets data stored at filepath if it exists and could be opened. Does not ensure file pertains to any particular format.

        Args:
            filepath (str): Full filepath for data.

        Returns:
            Optional[bytearray]:  Raw bytearray of contents if file exists, else None
        """
        return None

    def getPack(self, filepath : str) -> LaytonPack:
        """Get an archive object representing files stored in the pack at the given filepath.

        Args:
            filepath (str): Full filepath for LPCK archive

        Returns:
            LaytonPack: Archive object regardless of if filepath exists or not
        """
        return LaytonPack()
    
    def getPackedData(self, pathPack : str, filename : str) -> Optional[bytearray]:
        """Get uncompressed data for some file stored inside an archive at the given filepath.

        Args:
            pathPack (str): Full filepath for LPCK archive
            filename (str): Filename for desired file inside archive

        Returns:
            Optional[bytearray]: Raw bytearray of contents if file exists, else None
        """
        return self.getPack(pathPack).getFile(filename)
    
    def getPackedString(self, pathPack : str, filename : str) -> Optional[str]:
        """Get raw string contents for some file stored inside an archive at the given filepath.

        Args:
            pathPack (str): Full filepath for LPCK archive
            filename (str): Filename for desired file inside archive

        Returns:
            Optional[str]: Unicode string contents if file exists and could be decoded, else None
        """
        return ""
    
    def isRunningFromRom(self) -> bool:
        """Returns whether widebrim's filesystem has access to some LAYTON2 ROM.

        Returns:
            bool: True if there is a ROM loaded for widebrim to access
        """
        return False
    
    def getRom(self) -> Optional[NintendoDSRom]:
        """Gets the loaded ROM being accessed by widebrim. Not recommended since usage of this object may interfere with widebrim's operation.

        Returns:
            Optional[ndspy.rom.NintendoDSRom]: ROM object if loaded, else None
        """
        return None

    def getLanguage(self) -> Optional[LANGUAGES]:
        """Get the stored language from ROM.

        Returns:
            Optional[LANGUAGES]: LANGUAGE Enum or None if the language could not be derived.
        """
        return None