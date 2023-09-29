from widebrim.madhatter.common import logSevere
from .const import DECODE_MAP

# TODO - Enforce cp1252 encoding

def getSubstitutedString(inString):
    # Not fully accurate

    indexChar = 0
    stringKey = ""
    output = ""
    while indexChar < len(inString):
        if inString[indexChar] == "<":
            stringKey = ""
            while indexChar < len(inString):
                if inString[indexChar] == ">":
                    if (indexChar == len(inString) - 1) or (indexChar < len(inString) - 1 and inString[indexChar + 1] != ">"):
                        break
                indexChar += 1
                stringKey += inString[indexChar]

            stringKey = stringKey[:-1]

            if stringKey in DECODE_MAP:
                output += DECODE_MAP[stringKey]
            else:
                logSevere("Did not have substitution for", stringKey, name="TextSubs")
        else:
            output += inString[indexChar]
        
        indexChar += 1

    if len(output) > 1536:
        return output[:1536]
    return output

