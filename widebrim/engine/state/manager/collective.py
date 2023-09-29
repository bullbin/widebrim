from widebrim.engine.const import LANGUAGES
from widebrim.engine.file import NativeRomFileInterface
from .state import Layton2GameState

class Layton2CollectiveState(Layton2GameState):
    def __init__(self, language : LANGUAGES=LANGUAGES.Japanese, forceUseLanguage=False):
        """Manager object used to bootstrap a game state with a file accessor.

        Args:
            language (LANGUAGES, optional): Language to load asset with, ignored unless forced. Defaults to LANGUAGES.Japanese.
            forceUseLanguage (bool, optional): Override ROM language detection with selected language. Defaults to False.
        """
        fileInterface = NativeRomFileInterface()
        if not(forceUseLanguage or (fileLanguage := fileInterface.getLanguage()) == None):
            language = fileLanguage
        super().__init__(language, fileInterface)