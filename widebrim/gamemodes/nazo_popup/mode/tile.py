from .base import BaseQuestionObject
from .const import PATH_ANI_TILE

class HandlerTile(BaseQuestionObject):
    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)
    
    def _doUnpackedCommand(self, opcode, operands):
        
        return super()._doUnpackedCommand(opcode, operands)