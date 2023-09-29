from enum import Enum

RESOLUTION_NINTENDO_DS          = (256,192)

TIME_FRAMECOUNT_TO_MILLISECONDS = 1000/60

EVENT_ID_START_PUZZLE           = 20000
EVENT_ID_START_TEA              = 30000

PATH_DB_HTEVENT     = "/data_lt2/rc/ht_event.dlz"
PATH_DB_EV_INF2     = "/data_lt2/rc/%s/ev_inf2.dlz"
PATH_DB_GOAL_INF    = "goal_inf.dlz"
PATH_DB_NZ_LST      = "nz_lst.dlz"
PATH_DB_CHP_INF     = "chp_inf.dlz"
PATH_DB_TM_DEF      = "tm_def.dlz"
PATH_DB_SM_INF      = "sm_inf.dlz"
PATH_DB_PLACEFLAG   = "placeflag.dat"
PATH_DB_STORYFLAG   = "storyflag2.dat"
PATH_DB_AUTOEVENT   = "autoevent2.dat"
PATH_DB_RC_ROOT     = "/data_lt2/rc/%s"
PATH_DB_RC_ROOT_LANG    = "/data_lt2/rc/%s/%s"

PATH_ANI            = "/data_lt2/ani/%s"
PATH_EXT_BGANI      = "bgani/%s"
PATH_EXT_EXIT       = "map/exit_%i.arc"
PATH_EXT_EVENT      = "eventobj/obj_%i.arc"

PATH_BG_ROOT        = "/data_lt2/bg/%s"
PATH_CHAP_ROOT      = "chapter/?/chapter%i.arc"
PATH_NAME_ROOT      = "eventchr/%s/chr%i_n.arc"
PATH_EVENT_ROOT     = "event/%s"

PATH_FACE_ROOT      = "/data_lt2/ani/sub/%s"

PATH_EVENT_SCRIPT   = "/data_lt2/event/ev_d%i.plz"
PATH_EVENT_SCRIPT_A = "/data_lt2/event/ev_d%ia.plz"
PATH_EVENT_SCRIPT_B = "/data_lt2/event/ev_d%ib.plz"
PATH_EVENT_SCRIPT_C = "/data_lt2/event/ev_d%ic.plz"
PATH_EVENT_TALK     = "/data_lt2/event/%s/ev_t%i.plz"
PATH_EVENT_TALK_A   = "/data_lt2/event/%s/ev_t%ia.plz"
PATH_EVENT_TALK_B   = "/data_lt2/event/%s/ev_t%ib.plz"
PATH_EVENT_TALK_C   = "/data_lt2/event/%s/ev_t%ic.plz"
PATH_PUZZLE_SCRIPT  = "/data_lt2/script/puzzle.plz"

PATH_PACK_EVENT_DAT = "d%i_%.3i.dat"
PATH_PACK_EVENT_SCR = "e%i_%.3i.gds"
PATH_PACK_TALK      = "t%i_%.3i_%i.gds"
PATH_PACK_PUZZLE    = "q%i_param.gds"

PATH_PROGRESSION_DB = "/data_lt2/place/data.plz"

PATH_NAZO_A = "/data_lt2/nazo/%s/nazo1.plz"
PATH_NAZO_B = "/data_lt2/nazo/%s/nazo2.plz"
PATH_NAZO_C = "/data_lt2/nazo/%s/nazo3.plz"

PATH_PACK_NAZO  = "n%i.dat"

PATH_PLACE_BG           = "map/main%i.bgx"
PATH_PLACE_MAP          = "map/map%i.bgx"
PATH_EVENT_BG           = "event/sub%i.bgx"
PATH_EVENT_BG_LANG_DEP  = "event/?/sub%i.bgx"

PATH_PUZZLE_BG              = "nazo/q%i.bgx"
PATH_PUZZLE_BG_LANGUAGE     = "nazo/?/q%i.bgx"
PATH_PUZZLE_BG_NAZO_TEXT    = "nazo/system/nazo_text%i.bgx"

PATH_PACK_PLACE_NAME    = "/data_lt2/nazo/%s/jiten.plz"
PATH_PACK_TXT           = "/data_lt2/txt/%s/txt.plz"
PATH_PACK_TXT2          = "/data_lt2/txt/%s/txt2.plz"

PATH_TEXT_GOAL          = "goal_%i.txt"
PATH_TEXT_GENERIC       = "tx_%i.txt"
PATH_TEXT_PURPOSE       = "next_%i.txt"
PATH_TEXT_PLACE_NAME    = "p_%i.txt"
PATH_TEXT_ITEM          = "item_%i.txt"
PATH_TEXT_CAM           = "cam_%i.txt"
PATH_TEXT_HERB          = "herb_%i.txt"
PATH_TEXT_HAM           = "ham_%i.txt"

class LANGUAGES(Enum):
    French      = "fr"
    English     = "en"
    Chinese     = "ch"
    German      = "ge"
    Dutch       = "du"
    Italian     = "it"
    Spanish     = "sp"
    Korean      = "ko"
    Japanese    = "jp"

class CIPHER_IV(Enum):
    Default     = 0x59
    Future      = 0x55
    Pandora     = 0x4b

ADDRESS_ARM9_POINTER_FUNC_LANGUAGE  = 0x0200094c

DICT_ID_TO_LANGUAGE = {0 : LANGUAGES.Japanese,
                       1 : LANGUAGES.English,
                       2:  LANGUAGES.Spanish,
                       3 : LANGUAGES.French,
                       4 : LANGUAGES.Italian,
                       5 : LANGUAGES.German,
                       6 : LANGUAGES.Dutch,
                       7 : LANGUAGES.Korean,
                       8 : LANGUAGES.Chinese}