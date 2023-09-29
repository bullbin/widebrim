class StaticImageAsFont():
    def __init__(self, image, text="", stride=None):
        self._image = image
        self._useStride = False
        self._pos = (0,0)
        self._text = None
        self._stride = None

        self.setText(text)
        self.setStride(stride)
    
    def setText(self, text):
        isValid = type(text) == str
        if isValid:
            self._text = text
        return isValid
    
    def setStride(self, stride):
        isValid = type(stride) == int
        if isValid:
            self._useStride = True
            self._stride = stride
        else:
            self._useStride = False
        return isValid

    def setPos(self, pos):
        try:
            x = int(pos[0])
            y = int(pos[1])
            self._pos = (x,y)
        except:
            return False
        return True
    
    def getPos(self):
        return self._pos
    
    def _getText(self):
        return self._text

    def drawBiased(self, gameDisplay, fromRight=True):
        x, y = self._pos
        if fromRight:
            text = self._getText()[::-1]
        else:
            text = self._getText()

        if self._useStride:
            if fromRight:
                stride = - self._stride
            else:
                stride = self._stride

            for char in text:
                if self._image.setAnimationFromName(char):
                    frame = self._image.getActiveFrame()
                    if frame != None:
                        gameDisplay.blit(frame, (x,y))
                x += stride
        else:
            if fromRight:
                multiplier = -1
            else:
                multiplier = 1
            
            for char in text:
                if self._image.setAnimationFromName(char):
                    frame = self._image.getActiveFrame()
                    if frame != None:
                        gameDisplay.blit(frame, (x,y))
                        y += (frame.get_width() * multiplier)
            
class StaticImageAsNumericalFont(StaticImageAsFont):
    def __init__(self, image, text=None, stride=None, maxNum=None, usePadding=False):
        self._maxNum = None
        self._usePadding = False
        self.setUsePadding(usePadding)
        self.setMaxNum(maxNum)
        super().__init__(image, text=text, stride=stride)
        
    def setText(self, text):
        """Sets the number to draw. Positive values only.

        Args:
            text (int): Value to draw

        Returns:
            bool: True if value was accepted
        """
        isValid = (type(text) == int and text >= 0) or type(text) == None
        if isValid:
            self._text = text
        return isValid
    
    def setMaxNum(self, maxNum):
        isValid = type(maxNum) == int
        if isValid:
            self._maxNum = maxNum
        return isValid
    
    def setUsePadding(self, usePadding):
        if usePadding == True:
            self._usePadding = True
        else:
            self._usePadding = False
        return usePadding == True

    def _getText(self):
        output = None
        if self._text != None:
            if self._maxNum != None:
                if self._text > self._maxNum:
                    output = self._maxNum
                else:
                    output = self._text
                
                lenAllowedOutput = len(str(self._maxNum))
                if self._usePadding:
                    formatString = "%0" + str(lenAllowedOutput) + "d"
                else:
                    formatString = "%" + str(lenAllowedOutput) + "d"
                
                if lenAllowedOutput > 0:
                    output = formatString % output

            else:
                output = str(self._text)
        else:
            output = ""
        return output