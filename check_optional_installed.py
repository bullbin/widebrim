import pytesseract
from subprocess import run

ffmpeg_installed    : bool = False
ffmpeg_has_codec    : bool = False
tess_okay           : bool = False

try:
    pytesseract.get_tesseract_version()
    tess_okay = True
except (pytesseract.TesseractNotFoundError, SystemExit):
    pass

output = run([r"ffmpeg.exe", "-version"], capture_output=True, shell=True, universal_newlines=True)
if output.returncode == 0:
    if "ffmpeg version" in output.stdout:
        ffmpeg_installed = True
        output = run([r"ffmpeg.exe", "-codecs"], capture_output=True, shell=True, universal_newlines=True)
        if "mobiclip" in output.stdout:
            ffmpeg_has_codec = True

if ffmpeg_installed and ffmpeg_has_codec and tess_okay:
    print("Your system is configured correctly for widebrim!")
else:
    if ffmpeg_installed:
        if ffmpeg_has_codec:
            print("PASS - FFMPEG is configured correctly.")
        else:
            print("FAIL - FFMPEG is configured correctly, but your version does not contain the required formats for mobiclip decoding.")
    else:
        print("FAIL - FFMPEG could not be located on your PATH. Please check it is installed correctly.")
    if tess_okay:
        print("PASS - pytesseract is able to interface with your Tesseract-OCR install.")
    else:
        print("FAIL - pytesseract was not able to interface with your Tesseract-OCR install. Please check it is installed correctly.")
    print("Your system may be able to run widebrim but there will be compromises in compatibility and gameplay.")

input("Press ENTER to quit...")