class PathInvalidRom(Exception):
    # Exception when ROM is not found
    pass

class PathInvalidPatch(Exception):
    # Exception when patch folder not found
    pass

class RomInvalid(Exception):
    pass

class FileInvalidCritical(Exception):
    # Exception when an important file could not be found
    pass

class ProgressionInvalidEventId(Exception):
    # Exception when an event is called which cannot exist
    pass

class ProgressionInvalidPlaceId(Exception):
    # Exception when a place is called which cannot exist
    pass

class ProgressionMissingDatabaseInformation(Exception):
    # Exception when a critical resolving database is missing at runtime
    pass