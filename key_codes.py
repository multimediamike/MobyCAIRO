TAB = 'TAB'
ENTER = 'ENTER'
ESC = 'ESC'
SPACE = 'SPACE'
PGUP = 'PGUP'
PGDOWN = 'PGDOWN'
LEFT_ARROW = 'LEFT_ARROW'
UP_ARROW = 'UP_ARROW'
RIGHT_ARROW = 'RIGHT_ARROW'
DOWN_ARROW = 'DOWN_ARROW'


def translateKey(keyCode):
    if 32 < keyCode < 128:
        keyCode = chr(keyCode).upper()
        return keyCode

    if keyCode == 9:
        return TAB
    elif keyCode == 13:
        return ENTER
    elif keyCode == 27:
        return ESC
    elif keyCode == 32:
        return SPACE

    elif keyCode in [ 0x210000 ]:
        return PGUP
    elif keyCode in [ 0x220000 ]:
        return PGDOWN
    elif keyCode in [ 0x250000 ]:
        return LEFT_ARROW
    elif keyCode in [ 0x260000 ]:
        return UP_ARROW
    elif keyCode in [ 0x270000 ]:
        return RIGHT_ARROW
    elif keyCode in [ 0x280000 ]:
        return DOWN_ARROW

    return keyCode