from typing import Optional

COMPARE_TABLE = ['\x00', '\x01', '\x02', '\x03', '\x04', '\x05', '\x06', '\x07',
                 '\x08', '\t',   '\n',   '\x0b', '\x0c', '\r',   '\x0e', '\x0f',
                 '\x10', '\x11', '\x12', '\x13', '\x14', '\x15', '\x16', '\x17',
                 '\x18', '\x19', '\x1a', '\x1b', '\x1c', '\x1d', '\x1e', '\x1f',
                 ' ',    '!',    '"',    '#',    '$',    '%',    '&',    "'",
                 '(',    ')',    '*',    '+',    ',',    '-',    '.',    '/',
                 '0',    '1',    '2',    '3',    '4',    '5',    '6',    '7',
                 '8',    '9',    ':',    ';',    '<',    '=',    '>',    '?',
                 '@',    'A',    'B',    'C',    'D',    'E',    'F',    'G',
                 'H',    'I',    'J',    'K',    'L',    'M',    'N',    'O',
                 'P',    'Q',    'R',    'S',    'T',    'U',    'V',    'W',
                 'X',    'Y',    'Z',    '[',    '\\',   ']',    '^',    '_',
                 '`',    'A',    'B',    'C',    'D',    'E',    'F',    'G',
                 'H',    'I',    'J',    'K',    'L',    'M',    'N',    'O',
                 'P',    'Q',    'R',    'S',    'T',    'U',    'V',    'W',
                 'X',    'Y',    'Z',    '{',    '|',    '}',    '~',    '\x7f']

def getCharEquivalent(char : str) -> Optional[str]:
    """Get the comparison value for a particular character.

    Args:
        char (str): Input character

    Returns:
        Optional[str]: Output character. None if no equivalent available
    """
    if len(char) == 1:
        charCode = ord(char)
        if charCode < len(COMPARE_TABLE):
            return COMPARE_TABLE[charCode]
    return None

def strLen(inStr : str) -> int:
    """Get the length of the first segment from a null-terminated string.

    Args:
        inStr (str): String with null characters

    Returns:
        int: Length of first segment not including the terminating character
    """
    output = 0
    for char in inStr:
        if char != '\x00':
            output += 1
        else:
            break
    return output

def strCmp(x : str, y : str) -> bool:
    """Compare two strings for equivalency. Uses comparison tables and termination length checking for looser equivalency, eg allows changes in letter case.

    Args:
        x (str): String 1
        y (str): String 2

    Returns:
        bool: True if strings can be considered equivalent
    """
    lenStr = strLen(x)
    if lenStr != strLen(y):
        return False
    
    for chrX, chrY in zip(x[:lenStr], y[:lenStr]):
        if (codeX := getCharEquivalent(chrX)) != None and (codeY := getCharEquivalent(chrY)) != None:
            if codeX != codeY:
                return False
        elif chrX != chrY:
            return False
    return True