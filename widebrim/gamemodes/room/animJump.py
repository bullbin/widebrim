from math import pi, sin

class AnimJumpHelper():

    def __init__(self, initialPos, isExclamationPoint : bool):
        if isExclamationPoint:
            self.jumpHeight = 28
            self.lengthJump = 500
            self.lengthWait = 0
        else:
            self.jumpHeight = 4
            self.lengthJump = 250
            self.lengthWait = 250

        self.pos = initialPos
        self.totalDuration = self.lengthJump + self.lengthWait
        self.strengthMaxJump = self.lengthJump / self.totalDuration

    def __getOffset(self, strength) -> float:
        if strength <= self.strengthMaxJump:
            return self.jumpHeight * sin(pi * (strength / self.strengthMaxJump))
        else:
            return 0
    
    def getPosition(self, strength):
        yOffset = round(self.__getOffset(strength))
        return (self.pos[0], self.pos[1] - yOffset)