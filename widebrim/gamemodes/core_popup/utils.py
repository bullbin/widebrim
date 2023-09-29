from ...engine.state.layer import ScreenLayerNonBlocking

# TODO - AWFUL!!!!! had to redefine this everywhere.

class MainScreenPopup(ScreenLayerNonBlocking):
    def __init__(self, callbackOnTerminate):
        ScreenLayerNonBlocking.__init__(self)

class FullScreenPopup(ScreenLayerNonBlocking):
    def __init__(self, callbackOnTerminate):
        ScreenLayerNonBlocking.__init__(self)