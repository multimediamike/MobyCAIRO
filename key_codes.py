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

    if keyCode == 13:
        return ENTER
    elif keyCode == 27:
        return ESC
    elif keyCode == 32:
        return SPACE

    elif keyCode in [ 0x210000, 0xFF55 ]:
        return PGUP
    elif keyCode in [ 0x220000, 0xFF56 ]:
        return PGDOWN
    elif keyCode in [ 0x250000, 0xFF51 ]:
        return LEFT_ARROW
    elif keyCode in [ 0x260000, 0xFF52 ]:
        return UP_ARROW
    elif keyCode in [ 0x270000, 0xFF53 ]:
        return RIGHT_ARROW
    elif keyCode in [ 0x280000, 0xFF54 ]:
        return DOWN_ARROW

    return keyCode

