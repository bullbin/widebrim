from .base import BaseQuestionObject

class HandlerKnight(BaseQuestionObject):
    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)
    
    def hasSubmitButton(self):
        return False