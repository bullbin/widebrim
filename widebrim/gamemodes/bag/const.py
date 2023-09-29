PATH_BG_MAIN = "menu/bag/?/bag_bg.bgx"
PATH_BG_SUB = "menu/bag/?/bag_sub.bgx"

PATH_ANI_RESET_WINDOW = "menu/bag/reset_window.spr"
PATH_ANI_RESET_FONT = "menu/bag/%s/reset_font.spr"
PATH_ANI_TOBJ_WINDOW = "tobj/window.spr"
PATH_ANI_NEW = "system/btn/?/new_button.spr"
PATH_ANI_STATUS_NUMBER = "menu/bag/status_number.sbj"
PATH_ANI_STATUS_NUMBER2 = "menu/bag/status_number2.sbj"
PATH_ANI_MEDAL_ICON = "menu/bag/medal_icon.sbj"
PATH_ANI_DOT_LAYTON_WALK = "menu/bag/dot_layton_walk.sbj"
PATH_ANI_ITEM_ICON = "menu/bag/item_icon.spr"
PATH_ANI_HELP_MES = "menu/bag/?/help_mes.spr"

PATH_ANI_CAMERA_DISABLED = "menu/bag/no_camera.spr"
PATH_ANI_HAMSTER_DISABLED = "menu/bag/no_ham.spr"
PATH_ANI_TEA_DISABLED = "menu/bag/no_tea.spr"

POS_ANI_MEDAL_ICON = (0x6c,0x4c)
POS_ANI_DOT_LAYTON_WALK = (0x14,0x98)
# Initial animation index is 1, any above the values increases this
MEDAL_ICON_LIMITS = [0x1e,0x32,0x50,0x96,0xe5]
DOT_LAYTON_WALK_SPAWN_ANIM = 1

# After a second before 100 hours, the Layton walking animation is replaced with an old sprite
DOT_LAYTON_WALK_OLD_ANIM = 2
DOT_LAYTON_WALK_OLD_ANIM_HOURS = 100

# Uses "pos" as position name, but directly specified
PATH_BTN_TOJIRU     = "menu/bag/%s/tojiru.spr"
PATH_BTN_RESET      = "menu/bag/reset.spr"
PATH_BTN_MEMO       = "menu/bag/%s/memo.spr"
PATH_BTN_MYSTERY    = "menu/bag/%s/hukamaru.spr"
PATH_BTN_PUZZLE     = "menu/bag/%s/jiten.spr"
PATH_BTN_SAVE       = "menu/bag/%s/save.spr"
PATH_BTN_DIARY      = "menu/bag/%s/diary.spr"

# Position depends on diary
PATH_BTN_CAMERA_BROKEN      = "menu/bag/%s/camera.spr"
PATH_BTN_CAMERA_FIXED       = "menu/bag/%s/camera_fix.spr"
PATH_BTN_HAMSTER_ENABLED    = "menu/bag/%s/ham.spr"
PATH_BTN_HAMSTER_COMPLETE   = "menu/bag/%s/ham_fix.spr"
PATH_BTN_TEA_ENABLED        = "menu/bag/%s/tea.spr"
PATH_BTN_TEA_COMPLETE       = "menu/bag/%s/tea_fix.spr"

VARIABLE_BTN_DIARY_DISABLED = "pos"
VARIABLE_BTN_DIARY_ENABLED  = "pos2"
VARIABLE_DEFAULT_POS        = "pos"

VARIABLE_BTN_RESET_POS  = "reset_p"
PATH_BTN_RESET_YES      = "system/btn/%s/yes.spr"
PATH_BTN_RESET_NO       = "system/btn/%s/no.spr"

ID_TEXT2_RESET          = 100
POS_TEXT_RESET_CENTER   = (0x80, 0x3c)

POS_TEXT_PLACE_NAME     = (0xa4, 0xa1)