from .base import BaseQuestionObject

class HandlerRose(BaseQuestionObject):
    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)
    
    def hasSubmitButton(self):
        return False