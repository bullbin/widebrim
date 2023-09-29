from .base import BaseQuestionObject

from .freeButton import HandlerFreeButton
from .onOff import HandlerOnOff
from .traceButton import HandlerTraceButton
from .traceOnly import HandlerTraceOnly as HandlerTrace
from .divide import HandlerDivide
from .touch import HandlerTouch
from .tile import HandlerTile
from .pancake_short import HandlerShortbrimPancake as HandlerPancake
from .drawInput import HandlerDrawInput
from .knight_short import HandlerShortbrimKnight as HandlerKnight
from .onOff2 import HandlerOnOff2
from .rose_short import HandlerShortbrimRose as HandlerRose
from .slide2_short import HandlerShortbrimSlide2 as HandlerSlide2
from .tile2 import HandlerTile2
from .skate_short import HandlerShortbrimSkate as HandlerSkate
from .pegSolitaire_short import HandlerShortbrimPegSolitaire as HandlerPegSolitaire
from .couple import HandlerCouple
from .lamp_short import HandlerShortbrimLamp as HandlerLamp
from .bridge import HandlerBridge
from .traceOnly import HandlerTraceOnly

# TODO - Handle errors in GdScript gracefully like the game would, eg Divide with too few points to subdivide