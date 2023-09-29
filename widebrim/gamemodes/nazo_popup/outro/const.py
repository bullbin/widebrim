PATH_BG_LANGUAGE = "nazo/hantei/?/judge_%c%i_bg.bgx"
PATH_BG          = "nazo/hantei/judge_%c%i_bg.bgx"

# TODO - Redundant strings
PATH_BG_PASS   = "nazo/system/nazo_seikai%i.bgx"
PATH_BG_ANSWER  = "nazo/q%ia.bgx"
PATH_BG_ANSWER_LANG = "nazo/?/q%ia.bgx"
PATH_BG_FAIL    = "nazo/system/nazo_fail%i.bgx"
PATH_BG_RETRY   = "nazo/system/qend_retry.bgx"

PATH_ANI_TRY_AGAIN  = "nazo/system/?/retry.spr"
PATH_ANI_VIEW_HINT  = "nazo/system/?/viewhint.spr"
PATH_ANI_QUIT       = "nazo/system/?/later.spr"

CHAR_CHARACTER_0 = "l"
CHAR_CHARACTER_1 = "r"

INDEX_IMAGE_FINAL   = [0xe, 0x72]
INDEX_IMAGE_SOLVED  = [10, 0x6e]

# Decoded from game binary and reversed to grab values in correct order
JUDGE_INDEX_PASS    = [1, 2, 3, 0, 4, 5, 6, 0,  7,   8,   9,  0,  10,  11,  12,  13, 0,  14]
JUDGE_INDEX_FAIL    = [1, 2, 3, 0, 4, 5, 6, 0, 107, 108, 109, 0, 110, 111, 112, 113, 0, 114]
JUDGE_PARAM_WAIT    = [         0,          0,                8,                     0     ]
JUDGE_PARAM_DEFAULT = [2, 2, 6,    2, 2, 6,     2,   2,   6,      2,   1,   1,   20,     16]