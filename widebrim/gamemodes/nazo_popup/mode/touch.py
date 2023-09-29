from .base import BaseQuestionObject
from .const import PATH_ANI_TOUCH
from ....engine_ext.utils import getBottomScreenAnimFromPath
from ....engine.const import RESOLUTION_NINTENDO_DS
from ....madhatter.typewriter.strings_lt2 import OPCODES_LT2
from pygame import MOUSEBUTTONDOWN

class HandlerTouch(BaseQuestionObject):
    def __init__(self, laytonState, screenController, callbackOnTerminate):
        super().__init__(laytonState, screenController, callbackOnTerminate)
        self.sprites = []
        self.spritesTargetAnimIndex = []
        self.spritesCurrentAnimIndex = []
    
    def drawPuzzleElements(self, gameDisplay):
        for sprite in self.sprites:
            sprite.draw(gameDisplay)
        return super().drawPuzzleElements(gameDisplay)
    
    def _wasAnswerSolution(self):
        return self.spritesTargetAnimIndex == self.spritesCurrentAnimIndex

    def _doUnpackedCommand(self, opcode, operands):
        if opcode == OPCODES_LT2.AddTouchSprite.value and len(operands) == 5:
            touchSprite = getBottomScreenAnimFromPath(self.laytonState, PATH_ANI_TOUCH % operands[2].value)
            if touchSprite != None:
                if touchSprite.setAnimationFromIndex(operands[3].value) and touchSprite.setAnimationFromIndex(operands[4].value):
                    touchSprite.setAnimationFromIndex(operands[3].value)
                    self.spritesTargetAnimIndex.append(operands[4].value)
                    self.spritesCurrentAnimIndex.append(operands[3].value)
                    touchSprite.setPos((operands[0].value, operands[1].value + RESOLUTION_NINTENDO_DS[1]))
                    self.sprites.append(touchSprite)
                    return True
        return super()._doUnpackedCommand(opcode, operands)
    
    def handleTouchEventPuzzleElements(self, event):
        if event.type == MOUSEBUTTONDOWN:
            for indexSprite, sprite in enumerate(self.sprites):
                if sprite.wasPressed(event.pos):
                    currentAnimIndex = self.spritesCurrentAnimIndex[indexSprite]
                    currentAnimIndex += 1
                    if not(sprite.setAnimationFromIndex(currentAnimIndex)):
                        # Reset animation to initial index (which should be 1, above Create an Animation...)
                        currentAnimIndex = 1
                        sprite.setAnimationFromIndex(currentAnimIndex)
                    self.spritesCurrentAnimIndex[indexSprite] = currentAnimIndex
                    return True
        return super().handleTouchEventPuzzleElements(event)