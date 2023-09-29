from os import getcwd

TIME_FRAMERATE          = 60                    # Controls framerate. 60 = 60fps. Reducing below 60 may result in strange pacing

ROM_LOAD_BANNER         = True                  # Nice-to-have. Slows initial launch but extracts the title and banner icon from ROM

NDS_USE_FIRMWARE_MAC    = False                 # Uses MAC address from DS firmware instead of system. Keeps certain cipher checks (Hidden Door) accurate to NDS
                                                #     Results are tied to the MAC address of this device so unless using NDS firmware, ciphers are not portable
NAME_INTERFACE_MAC      = None                  # String representation of the interface used for grabbing the MAC address. Leave as 'None' if default is okay.
                                                #     If you're experiencing very slow cipher generations or odd results, make sure the name given is a valid interface

WINDOW_DEFAULT_NAME     = "widebrim"
WINDOW_SCALE_TO_VIEW    = True                  # For high DPI devices, widebrim will be small at default resolution. Enable this to integer scale where possible
WINDOW_USE_VSYNC        = False                 # Eliminates screen tearing. pygame has some issues with this flag, however, so disable this if you get a black screen

PATH_ROM        = getcwd() + "\\rom2.nds"
PATH_SAVE       = getcwd() + "\\rom2.sav"
PATH_NDS_FIRM   = getcwd() + "\\firmware.bin"   # Path to DS (DSi unsupported) firmware file containing the WiFi configuration data

# Debug configurations below. Don't change these unless you know what you're doing!

DEBUG_BYPASS_PUZZLE_INTRO   = False             # Bypass puzzle intro scene - good for rapid puzzle testing