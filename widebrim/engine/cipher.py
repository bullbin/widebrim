from widebrim.madhatter.hat_io.binary import BinaryReader
from numpy import seterr, geterr, uint8
from getmac import get_mac_address
from .config import NDS_USE_FIRMWARE_MAC, PATH_NDS_FIRM, NAME_INTERFACE_MAC
from .const import CIPHER_IV

def generatePasscode(iv : CIPHER_IV) -> str:
    """Generates passcodes used in Hidden Door related gamemodes.

    Args:
        iv (CIPHER_IV): Initial value which tunes output alongside MAC address

    Returns:
        str: 8 character passcode featuring letters from A-G and digits from 0-9
    """

    def getMacAddressFromDevice() -> bytes:
        output = bytearray(b'\x00\x00\x00\x00\x00\x00')
        mac = get_mac_address(interface=NAME_INTERFACE_MAC)
        if mac != None:
            for indexSegment, segment in enumerate(mac.split(":")):
                output[indexSegment] = int(segment, base=16)
        return output

    def getMacAddressFromFirmware() -> bytes:
        reader = BinaryReader(filename=PATH_NDS_FIRM)
        try:
            reader.seek(8)
            if reader.read(4) == b'MACP':
                reader.seek(54)
                return reader.read(6)
        except:
            pass
        return getMacAddressFromDevice()

    if NDS_USE_FIRMWARE_MAC:
        macAddress = getMacAddressFromFirmware()
    else:
        macAddress = getMacAddressFromDevice()

    def getMacAddressByte(indexByte) -> uint8:
        return uint8(macAddress[indexByte])    

    iv = uint8(iv.value)

    # Hide numpy overflow errors - intentional
    npOverErr = geterr()["over"]
    seterr(over="ignore")
    mix0 = getMacAddressByte(1) + getMacAddressByte(3) - getMacAddressByte(4)
    mix1 = getMacAddressByte(4) + getMacAddressByte(3) + getMacAddressByte(2) + getMacAddressByte(5)

    output = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00')
    output[0] = (getMacAddressByte(0) + getMacAddressByte(3)) * iv
    output[1] = mix0 + iv
    output[2] = mix1 * iv
    output[3] = getMacAddressByte(3) - iv
    output[4] = getMacAddressByte(4) * iv
    output[5] = getMacAddressByte(5) + iv
    output[6] = (getMacAddressByte(0) + getMacAddressByte(3) + mix0 + mix1) * iv
    output[7] = (getMacAddressByte(3) - getMacAddressByte(4) - getMacAddressByte(5)) - iv
    # Restore numpy overflow errors
    seterr(over=npOverErr)

    for indexOutput in range(8):
        if indexOutput % 2 == 0:
            output[indexOutput] = (output[indexOutput] % 9) + ord('0')
        else:
            output[indexOutput] = (output[indexOutput] % 7) + ord('A')

    return output.decode('ascii')