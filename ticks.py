import supervisor

_TICKS_PERIOD = const(1 << 29)
_TICKS_MAX = const(_TICKS_PERIOD-1)
_TICKS_HALFPERIOD = const(_TICKS_PERIOD//2)


def ticks_add(ticks, delta):
    "Add a delta to a base number of ticks, performing wraparound at 2**29ms."
    return (ticks + delta) % _TICKS_PERIOD

def ticks_diff(ticks1, ticks2):
    "Compute the signed difference between two ticks values, assuming that they are "
    "within 2**28 ticks (about 75 hours)"
    diff = (ticks1 - ticks2) & _TICKS_MAX
    diff = ((diff + _TICKS_HALFPERIOD) & _TICKS_MAX) - _TICKS_HALFPERIOD
    return diff

def is_due(due):
    return due and ticks_diff(due, supervisor.ticks_ms()) <= 0

def calc_due_ticks(seconds):
    return calc_due_ticks_ms(int(seconds * 1000))

def calc_due_ticks_ms(ms):
    due = ticks_add(supervisor.ticks_ms(), ms)
    if due == 0:
        # never return 0, so we can use it for a disable status
        due = 1
    return due

