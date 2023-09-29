PATH_BG_SUB         = "menu/bag/%s/jiten_sub.bgx"           # Actually ends with spr. Game doesn't validate string for bgx... # TODO - Bugfix, RomGrabFailed here!
PATH_BG_SUB_WIFI    = "menu/secret/?/wifi_jiten_sub.bgx"
PATH_BG_MAIN_WIFI   = "menu/bag/?/wifi_jiten_bg.bgx"
PATH_BG_MAIN        = "menu/bag/jiten_bg.bgx"

PATH_BG_WIFI_SAVE_SUB   = "map/main0.bgx"
PATH_BG_WIFI_SAVE_MAIN  = "menu/wifi/%s/wifi_window3.spr"

PATH_ANIM_PREVIEW_Q1    = "menu/jiten/jiten_q1.sbj"
PATH_ANIM_PREVIEW       = "menu/jiten/jiten_q%i.sbj"

PATH_ANIM_BTN_ALL       = "menu/jiten/%s/jiten_btn.spr"
PATH_ANIM_NUM           = "menu/jiten/%s/jiten_num.sbj"
PATH_ANIM_INTRO_TEXT    = "menu/jiten/%s/jiten_title.spr"
PATH_ANIM_TABS          = "menu/jiten/%s/tag.spr"
PATH_ANIM_NUM_ARC       = "menu/jiten/?/jiten_num.spr"

PATH_ANIM_COVER         = "menu/jiten/jiten_guard.spr"
PATH_ANIM_COVER_WIFI_1  = "menu/wifi/jiten_guard1.spr"
PATH_ANIM_COVER_WIFI_2  = "menu/wifi/jiten_guard2.spr"

PATH_ANIM_HINT          = "menu/jiten/jiten_hintbox.sbj"
PATH_ANIM_PRIZE         = "menu/jiten/jiten_prize.sbj"

PATH_PACK_JITEN         = "/data_lt2/nazo/?/jiten.plz"
PATH_TEXT_JITEN_PLACE   = "p_%u.txt"
PATH_TEXT_JITEN_MISSING = "p_63.txt"
PATH_TEXT_NAZO_TYPE     = "type_%u.txt"

NAME_ANIM_JITEN_BTN_DOWN_OFF        = "down_off"
NAME_ANIM_JITEN_BTN_DOWN_ON         = "down_on"
NAME_ANIM_JITEN_BTN_DOWN_MANY_OFF   = "downfast_off"
NAME_ANIM_JITEN_BTN_DOWN_MANY_ON    = "downfast_on"
NAME_ANIM_JITEN_BTN_UP_OFF          = "up_off"
NAME_ANIM_JITEN_BTN_UP_ON           = "up_on"
NAME_ANIM_JITEN_BTN_UP_MANY_OFF     = "upfast_off"
NAME_ANIM_JITEN_BTN_UP_MANY_ON      = "upfast_on"

NAME_ANIM_JITEN_BTN_TOGGLE_FAV_OFF  = "fav_off"
NAME_ANIM_JITEN_BTN_TOGGLE_FAV_ON   = "fav_on"

NAME_ANIM_JITEN_BTN_ALT_CLOSE_CLICK = "close_click"
NAME_ANIM_JITEN_BTN_ALT_CLOSE_OFF   = "close_off"
NAME_ANIM_JITEN_BTN_ALT_CLOSE_ON    = "close_on"

NAME_ANIM_JITEN_BTN_SOLVE_OFF       = "pazzle_off"
NAME_ANIM_JITEN_BTN_SOLVE_ON        = "pazzle_on"
NAME_ANIM_JITEN_BTN_SOLVE_OFF_WIFI  = "wifipuzzle_off"
NAME_ANIM_JITEN_BTN_SOLVE_ON_WIFI   = "wifipuzzle_on"

NAME_ANIM_JITEN_TAG_HAT         = "nazo"
NAME_ANIM_JITEN_TAG_SOLVED      = "o"
NAME_ANIM_JITEN_TAG_ENCOUNTERED = "x"
NAME_ANIM_JITEN_TAG_UNTOUCHED   = "New"
NAME_ANIM_JITEN_NUM_WIFI_DOT    = "dot"
NAME_ANIM_TAG_TAB_ALL           = "all"
NAME_ANIM_TAG_TAB_PICKS         = "favorite"

ANIM_VAR_POS_TAG_JITEN_GUARD    = "pos"

POS_X_NAZO_NAME_WIFI    = 0x5b
POS_X_NAZO_NAME         = 0x65

POS_TEXT_PUZZLE_NUMBER  = (0x3c, 0xf)
POS_TEXT_PICARAT_FULL   = (0xe1, 0x16)
POS_TEXT_PICARAT_DECAY  = (0xcd, 0x16)
COUNT_DIGIT_PICARAT     = 2
COUNT_DIGIT_NUMBER      = 3

POS_TEXT_TYPE       = (0x9e, 0x96)
POS_TEXT_LOCATION   = (0x9e, 0xa8)
POS_Y_TEXT_NAME     = 0xf

POS_ANIM_HINT_OPEN  = (0x83, 0x7e)
POS_ANIM_PREVIEW    = (0x50, 0x30)
POS_ANIM_PRIZE      = (0xd, 0x6)
POS_ANIM_TITLE      = (0xe, 8)

POS_BTN_SOLVE       = (0xb3, 0x3)
POS_BTN_UP          = (0x6b, 0x1e)
POS_BTN_UP_MANY     = (0x8b, 0x1e)
POS_BTN_DOWN        = (0x6b, 0x9a)
POS_BTN_DOWN_MANY   = (0x8b, 0x9a)
POS_BTN_CLOSE       = (0xbb, 0xa3)
POS_BTN_TO_FAV      = (0x2f, 0x26)
POS_BTN_FROM_FAV    = (0xe, 0x26)

DIM_BTN_SOLVE           = (0x38, 0x32)
DIM_BTN_MOVE            = (0x1e, 0x18)
DIM_BTN_CLOSE           = (0x34, 0x14)
DIM_BTN_TO_FAVOURITES   = (0x30, 0x10)
DIM_BTN_FROM_FAVOURITES = (0x20, 0x10)

POS_CORNER_HITBOX_SELECT    = (0x26, 0x38)
SIZE_HITBOX_SELECT          = (0xb4, 0x11)
BIAS_HITBOX_SELECT_Y        = 0x14

POS_CORNER_FAVOURITE        = (0x15, 0x3a)
SIZE_HITBOX_FAVOURITE       = (0x10, 0xc)

POS_X_SELECT_BOX            = 0x10
SIZE_BOX_SELECT_OVERLAY     = (0xd0, 0x10)
COLOR_BOX_SELECT_OVERLAY    = (0,0,0x40,0x5)
BOUNDS_Y_SELECT_BOX_MAX     = 152
BOUNDS_Y_SELECT_BOX_MIN     = 56

NAME_MAIN_X_WIFI    = 0x5b
NAME_MAIN_X_NORMAL  = 0x65

BIAS_X_HINT_OPEN    = 0x11

# Inaccurate
SPEED_BTN_SLOW  = 100
SPEED_BTN_FAST  = 300
COUNT_DISPLAY   = 5
ALPHA_SELECT_OVERLAY    = 45    # Alpha works differently, so define custom alpha