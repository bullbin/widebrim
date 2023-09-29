POS_Y_ANIM_PARTY    = 0x90
POS_X_ANIM_PARTY    = [5, 0x17, 0x29, 0x3b]
NAME_ANIM_PARTY     = ["1", "2", "3", "4"]

PATH_ANIM_PARTY     = "map/map_icons.sbj"
PATH_ANIM_MAPICON   = "map/mapicon.sbj"

PATH_ANIM_CURSOR_WAIT   = "cursor_wait.spr"
NAME_ANIM_CURSOR_WAIT   = "touch"
POS_CURSOR_WAIT         = (0xcf, 0x69)

PATH_ANIM_TOBJ_WINDOW   = "tobj/window.spr"
PATH_ANIM_TOBJ_ICON     = "tobj/icon.spr"
POS_TOBJ_ICON           = (0x25,0x54)
POS_TOBJ_TEXT_CENTRAL_LINE  = (0x42,0x5c)    # Note this starts from the top of the symbol, so padding needs to be accounted for

PATH_PACK_TOBJ      = "/data_lt2/place/%s/tobj.plz"
PATH_FILE_TOBJ      = "tobj%i.txt"
PATH_FILE_HINTCOIN  = "hintcoin.txt"

PATH_BTN_MOVEMODE   = "map/movemode.spr"
PATH_BTN_MENU_ICON  = "map/menu_icon.spr"
PATH_BTN_CAMERA     = "map/camera_icon.spr"

PATH_ANIM_HINTCOIN      = "map/hintcoin.spr"
PATH_ANIM_ICON_BUTTONS  = "map/icon_buttons.spr"

PATH_ANIM_TOUCH_ICON    = "map/touch_icon.spr"
POS_TOUCH_ICON          = (-32,-32)

PATH_ANIM_TEAEVENT_ICON     = "map/teaevent_icon.spr"
POS_TEAEVENT_ICON_Y_OFFSET  = -0xe

PATH_ANIM_SOLVED_TEXT   = "map/%s/toketa_nazo.sbj"
POS_SOLVED_TEXT         = (2,6)

PATH_ANIM_NUM_MAP_NUMBER    = "map/map_number.sbj"
PATH_ANIM_FIRSTTOUCH        = "map/%s/firsttouch.spr"

PATH_ANIM_PIECE_MESSAGE = "map/%s/piece_mes.sbj"
PATH_ANIM_NUM_PIECE_NUM = "map/piece_num.sbj"
POS_PIECE_MESSAGE       = (0x4d, 0x9b)

PATH_ANIM_MAP_ARROW     = "map/?/map_arrows.sbj"
EVENT_VIEWED_MAP_ARROW  = [0, 0x8a, 0x6d]

PATH_PLACE_A    = "/data_lt2/place/plc_data1.plz"
PATH_PLACE_B    = "/data_lt2/place/plc_data2.plz"
PATH_PACK_PLACE = "n_place%i_%i.dat"

PATH_PLACE_BG   = "map/main%i.bgx"
PATH_PLACE_MAP  = "map/map%i.bgx"

PATH_ANIM_BGANI = "bgani/%s"
PATH_EXT_EXIT   = "map/exit_%i.arc"
PATH_EXT_EVENT  = "eventobj/obj_%i.arc"

# TODO - Duplicated event IDs, but separated in binary too
LIMIT_ID_PUZZLE_START   = 20000
LIMIT_ID_TEA_START      = 30000
COUNT_HERBTEA           = 0x18
COUNT_HERBTEA_LIMIT     = 0x15