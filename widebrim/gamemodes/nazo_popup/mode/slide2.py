from .base import BaseQuestionObject

class HandlerSlide2(BaseQuestionObject):
    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)
    
    def hasSubmitButton(self):
        return False